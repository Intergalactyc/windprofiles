import windprofiles.lib.polar as polar
import windprofiles.lib.stats as stats
import numpy as np
import pandas as pd
import scipy.integrate as spint
from scipy.signal import welch
from scipy.optimize import curve_fit
from scipy.stats import binned_statistic


def get_stats(
    df: pd.DataFrame, stat=np.mean, suffix=None, col_types=None
) -> dict:
    result = dict()
    if suffix is None:
        if stat == np.mean:
            suffix = "_mean"
        elif stat == np.median:
            suffix = "_med"
        elif stat == np.std:
            suffix = "_std"
        else:
            suffix = ""
    for col in df.columns:
        ctype = col.split("_")[0]
        if col_types is not None and ctype not in col_types:
            continue
        result_col = col + str(suffix)
        if ctype in {"wd", "propwd"}:
            if stat == np.mean:
                result[result_col] = polar.unit_average_direction(df[col])
            elif stat == np.std:
                result[result_col] = polar.directional_rms(df[col])
            else:
                result[result_col] = pd.NA
        else:
            result[result_col] = stat(df[col])
    return result


def mean_directions(df, booms, prefix: str = "", degrees: bool = True):
    # u should be East, v should be North

    result = {}

    for b in booms:
        ux = df[f"{prefix}u_{b}"]
        uy = df[f"{prefix}v_{b}"]

        uxavg = np.mean(ux)
        uyavg = np.mean(uy)

        result[f"{prefix}wd_{b}_mean"] = polar.polar_wind(
            uxavg, uyavg, degrees
        )[1]

    return result


def align_to_directions(
    df, directions, prefix: str = "", degrees: bool = True
):
    # Given vector-mean wind directions:
    # Convert wind components to streamwise coordinates - that is,
    # Geometrically align the u, v components of wind such that u is oriented
    # in the direction of the mean wind and v is in the crosswind direction (and hence mean-0)
    by_boom = {
        int(s.split("_")[1]): np.deg2rad(d) if degrees else d
        for s, d in directions.items()
    }

    dfc = df.copy()
    for b, d in by_boom.items():
        ux = df[f"{prefix}u_{b}"]
        uy = df[f"{prefix}v_{b}"]

        ux_aligned = ux * np.sin(d) + uy * np.cos(d)
        uy_aligned = ux * np.cos(d) - uy * np.sin(d)
        # ux_aligned = ux * np.cos(d) + uy * np.sin(d)
        # uy_aligned = -ux * np.sin(d) + uy * np.cos(d)

        dfc[f"{prefix}u_{b}"] = ux_aligned
        dfc[f"{prefix}v_{b}"] = uy_aligned

    return dfc


available_cutoff_methods = [
    "zerocrossing",
    "efolding",
    "efoldingtime",
    "threshold",
    "total",
]


def integral_time_scale(
    ac: pd.Series,
    scale_factor: float = 1.0,
    integration_method: str = "simpson",
    cutoff_method: str = "efolding",
    threshold: float | None = None,
) -> float:
    # typical index is a lag # index, rather than true time index;
    # in this case a correction factor should be passed
    # (e.g. for lags at intervals of 0.05 s, use scale_factor=0.05)
    # Note that "efoldingtime" is special: rather than integrating, it simply
    # returns the time at which the 1/e threshold is met
    INTEGRATION_METHODS = {
        "simpson": spint.simpson,
        "trapezoid": np.trapezoid,
        "trapezoidal": np.trapezoid,
    }
    method = INTEGRATION_METHODS.get(integration_method.lower())
    if method is None:
        raise ValueError(f"Invalid integration method '{integration_method}'")

    cutoff_index = 0
    match cutoff_method.lower():
        case "zerocrossing":  # threshold of 0
            cutoff_threshold = 0.0
        case "efolding" | "efoldingtime":  # threshold of 1/e
            cutoff_threshold = 1 / np.e
        case "threshold":  # use custom specified threshold
            if threshold is None:
                raise ValueError(
                    "To use threshold method, a value must be passed"
                )
            cutoff_threshold = threshold
        case "total":  # integrate over all lags
            cutoff_index = -1
        case _:
            raise ValueError(f"Invalid cutoff method '{cutoff_method}'")

    # cutoff_index is the integer index at which the cutoff threshold is first met
    # will be -1 if no such crossing is detected
    if cutoff_index == 0:
        vals = np.asarray(ac)
        mask = vals <= cutoff_threshold
        if np.any(mask):
            # argmax on a boolean array finds the first True instantly
            idx_pos = int(np.argmax(mask)) 
            cutoff_index = ac.index[idx_pos]
        else:
            cutoff_index = -1
        if (
            cutoff_method.lower() == "efoldingtime"
        ):  # special mode: no integration, just give folding time
            if cutoff_index != -1:
                return scale_factor * cutoff_index
            else:
                return scale_factor * ac.index[-1]
            
    return scale_factor * method(
        ac.iloc[:cutoff_index], ac.index[:cutoff_index]
    )


def welch_psd(
    s: pd.Series,
    frequency: int | float,
    nperseg: int,
    freq_zero: bool = False,
    max_freq: float | str | None = "nyquist",
) -> pd.Series:
    _s = s.interpolate(method="linear") if s.isna().any() else s

    f, Pxx = welch(
        _s.values,
        frequency,
        window="hann",
        nperseg=nperseg,
        noverlap=nperseg // 2,
        scaling="density",
    )

    if max_freq == "half_nyquist":
        max_freq = frequency / 4
    elif max_freq == "nyquist":
        max_freq = frequency / 2

    start_idx = 0 if freq_zero else 1
    end_idx = len(f)
    
    if max_freq is not None:
        # searchsorted finds the cutoff index
        end_idx = np.searchsorted(f, max_freq, side='right')

    return pd.Series(data=Pxx[start_idx:end_idx], index=f[start_idx:end_idx])

def _kaimal_psd_model(f, X, sigma):
    # Kaimal spectrum parameterized by time scale X = L/V_hub
    # S(f) = 4 * sigma^2 * X / (1 + 6 * f * X)^(5/3)
    num = 4 * (sigma**2) * X
    den = (1 + 6 * f * X) ** (5 / 3)
    return num / den

def _von_karman_u_model(f, X, sigma):
    # Standard von Karman for the longitudinal (u) component
    num = 4 * (sigma**2) * X
    den = (1 + 70.8 * (f * X)**2) ** (5 / 6)
    return num / den

def _von_karman_vw_model(f, X, sigma):
    # Modified von Karman for transverse (v) and vertical (w) components
    num = 2 * (sigma**2) * X * (1 + 188.4 * (f * X)**2)
    den = (1 + 70.8 * (f * X)**2) ** (11 / 6)
    return num / den

def log_bin_spectrum(psd: pd.Series, num_bins: int = 50) -> pd.Series:
    # Averages a linearly-spaced PSD into logarithmically spaced bins
    f = psd.index.values
    S = psd.values
    
    valid = f > 0
    f = f[valid]
    S = S[valid]

    bins = np.logspace(np.log10(f.min()), np.log10(f.max()), num_bins + 1)
    
    S_binned, _, _ = binned_statistic(f, S, statistic='mean', bins=bins)
    f_binned, _, _ = binned_statistic(f, f, statistic='mean', bins=bins)
    
    mask = ~np.isnan(S_binned)
    
    return pd.Series(data=S_binned[mask], index=f_binned[mask])

def spectral_integral_time_scale(psd: pd.Series, sigma: float, component: str) -> tuple[float, dict[str, float]]:
    if psd.empty or psd.isna().all():
        return np.nan, {"kaimal": np.nan, "vonkarman": np.nan}
    
    _psd = log_bin_spectrum(psd)

    if len(_psd) < 3:
        return np.nan, {"kaimal": np.nan, "vonkarman": np.nan}
    
    f = _psd.index.to_numpy(dtype=np.float64)
    y_safe = _psd.clip(lower=1e-12).to_numpy(dtype=np.float64)
    log_y = np.log10(y_safe)
    
    def kaimal(f, X):
        S = 4 * (sigma**2) * X / (1 + 6 * f * X)**(5/3)
        return np.log10(np.maximum(S, 1e-12))
        
    def kaimal_jac(f, X):
        grad = (1 / np.log(10)) * ((1 / X) - (10 * f) / (1 + 6 * f * X))
        return grad.reshape(-1, 1)

    def vk_u(f, X):
        S = 4 * (sigma**2) * X / (1 + 70.8 * (f * X)**2)**(5/6)
        return np.log10(np.maximum(S, 1e-12))
        
    def vk_u_jac(f, X):
        grad = (1 / np.log(10)) * ((1 / X) - (118.0 * (f**2) * X) / (1 + 70.8 * (f * X)**2))
        return grad.reshape(-1, 1)

    def vk_vw(f, X):
        S = 2 * (sigma**2) * X * (1 + 188.4 * (f * X)**2) / (1 + 70.8 * (f * X)**2)**(11/6)
        return np.log10(np.maximum(S, 1e-12))
        
    def vk_vw_jac(f, X):
        grad = (1 / np.log(10)) * (
            (1 / X) 
            + (376.8 * (f**2) * X) / (1 + 188.4 * (f * X)**2) 
            - (259.6 * (f**2) * X) / (1 + 70.8 * (f * X)**2)
        )
        return grad.reshape(-1, 1)

    models_to_test = {
        "kaimal": (kaimal, kaimal_jac),
        "vonkarman" : (vk_u, vk_u_jac) if component == "u" else (vk_vw, vk_vw_jac)
    }

    best_X = np.nan
    best_r2 = -np.inf
    r2_scores = {}

    # Iterate through selected models, fit, and track the best performing one
    for name, (model_func, jac_func) in models_to_test.items():
        try:
            popt, _ = curve_fit(
                model_func, 
                f, 
                log_y, 
                p0=[15.0], 
                bounds=(0.1, 600.0),
                jac=jac_func
            )
            X_fit = popt[0]
            y_pred_log = model_func(f, X_fit)
            
            r2 = stats.r2_score(log_y, y_pred_log)
            r2_scores[name] = r2
            
            if r2 > best_r2:
                best_r2 = r2
                best_X = X_fit
                
        except Exception:
            r2_scores[name] = np.nan

    return best_X, r2_scores
