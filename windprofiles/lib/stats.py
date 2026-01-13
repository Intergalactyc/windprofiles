import math
import numpy as np
from scipy.optimize import curve_fit
import scipy.stats as st
import pandas as pd
from collections.abc import Iterable

from tqdm import tqdm

TRANSFORMS = {
    "linear": (lambda x: x),
    "log": (lambda x: np.log(x)),
    "exp": (lambda x: np.exp(x)),
    "inv": (lambda x: 1 / x),
    "square": (lambda x: x**2),
}


KAPPA = 0.41  # Von Karman constant


def ls_linear_fit(xvals, yvals):
    """
    Least squares fit to a relationship y = a + b*x
    Outputs a pair a,b describing fit
    """
    if len(yvals) == 0 or len(xvals) == 0:
        return 0, 0
    xvals = list(xvals)
    yvals = list(yvals)
    if len(yvals) != len(xvals):
        raise RuntimeError("Lists must be of equal size")
    for x, y in zip(xvals, yvals):
        if math.isnan(x) or math.isnan(y):
            xvals.remove(x)
            yvals.remove(y)
    n = len(xvals)
    sum_x = sum(xvals)
    sum_x2 = sum(x * x for x in xvals)
    sum_xy = sum(xvals[i] * yvals[i] for i in range(n))
    sum_y = sum(yvals)
    det = n * sum_x2 - sum_x * sum_x
    A = (sum_y * sum_x2 - sum_x * sum_xy) / det
    B = (n * sum_xy - sum_x * sum_y) / det
    return A, B


def power_fit(xvals, yvals, require=2):
    """
    Least squares fit to relationship y = a*x^b
    Outputs a pair a,b describing fit
    The b is exactly the wind shear coefficient for wind p.l. fit
    """
    xconsider = []
    yconsider = []
    for x, y in zip(xvals, yvals):
        if not (math.isnan(x) or math.isnan(y)):
            if y == 0:
                return 0, np.nan
            xconsider.append(x)
            yconsider.append(y)
    if len(yconsider) < require:
        return np.nan, np.nan
    lnA, B = ls_linear_fit(np.log(xconsider), np.log(yconsider))
    return np.exp(lnA), B


def log_fit(xvals, yvals):
    """
    Least squares fit to relationship y = a + b*log(x)
    Outputs a pair a,b describing fit
    """
    xconsider = []
    yconsider = []
    for x, y in zip(xvals, yvals):
        if not (math.isnan(x) or math.isnan(y)):
            if x <= 0:
                raise ValueError("Cannot do log fit with nonpositive x values")
            xconsider.append(x)
            yconsider.append(y)
    return ls_linear_fit(np.log(xconsider), yconsider)


def neutral_loglaw_fit(zvals, uvals, displacement: float = 0.0):
    """
    Least squares fit to relationship u = (ustar/kappa) * log((z-d)/z0),
        where kappa is the Von Karman constant and d is the given displacement.
    Ignores pairs (z,u) where z <= d.
    Outputs a pair ustar,z0 describing fit
    """
    zconsider = []
    uconsider = []
    for z, u in zip(zvals, uvals):
        if z > displacement:
            zconsider.append(z - displacement)
            uconsider.append(u)
    A, B = log_fit(zconsider, uconsider)
    ustar = B * KAPPA
    z0 = np.exp(-A / B)
    return ustar, z0


def sine_function(x, A, B, C, D):
    return (
        A * np.sin(B * x + C) + D
    )  # A: amplitude, B: period, C: normalized phase shift, D: offset


def fit_sine(
    x,
    y,
    yerrs,
    guess_period=2 * np.pi / 24,
    guess_shift=np.pi / 2,
    fix_period=False,
):
    """
    Find the best-fit sine function for a set of points (x,y).
    """
    x = np.array(x)
    y = np.array(y)
    yerrs = np.array(yerrs)

    guess_offset = np.mean(y)
    guess_amplitude = 3 * np.std(y) / np.sqrt(2)

    fitting_function = (
        (lambda t, a, c, d: sine_function(t, a, guess_period, c, d))
        if fix_period
        else sine_function
    )
    guess = (
        [guess_amplitude, guess_shift, guess_offset]
        if fix_period
        else [guess_amplitude, guess_period, guess_shift, guess_offset]
    )

    params, pcov = curve_fit(fitting_function, x, y, sigma=yerrs, p0=guess)

    params = (
        [params[0], guess_period, params[1], params[2]]
        if fix_period
        else params
    )

    return lambda t: sine_function(t, *params), params


def weibull_pdf(x: float, shape: float, scale: float):
    """
    Probability density function for Weibull distriubtion with given shape
    and scale parameters. All of x, shape, scale should be > 0.
    """
    return (
        (shape / scale)
        * (x / scale) ** (shape - 1)
        * np.exp(-((x / scale) ** shape))
    )


def fit_wind_weibull(data):
    """
    Fits a Weibull distribution to a dataset. Returns the pdf of the fit distribution
    as well as a pair (shape, scale) of the fit parameters.
    """
    _, shape, _, scale = st.exponweib.fit(data, floc=0, f0=1)
    return lambda x: weibull_pdf(x, shape, scale), (shape, scale)


def rcorrelation(df, col1, col2, transform=("linear", "linear")):
    """
    Get the Pearson correlation coefficient r between two columns in a dataframe.
    """
    tran_x = TRANSFORMS[transform[0]]
    tran_y = TRANSFORMS[transform[1]]
    dfr = df[~(np.isnan(tran_x(df[col1])) | np.isnan(tran_y(df[col2])))]
    cor = st.pearsonr(tran_x(dfr[col1]), tran_y(dfr[col2]))[0]
    return float(cor) # pyright: ignore[reportArgumentType]


def get_correlations(df: pd.DataFrame, which: list|None = None) -> pd.DataFrame:
    """
    Get correlation coefficients pairwise between a list of columns (will use all columns
    in dataframe if no list is specified)
    """
    if which is None:
        which = list(df.columns)
    corrs = pd.DataFrame(data=0.0, index=which, columns=which)
    for i, col1 in enumerate(which):
        corrs.iloc[i, i] = 1.0
        for j, col2 in enumerate(which[:i]):
            cor12 = rcorrelation(df, col1, col2, ("linear", "linear"))
            corrs.iloc[i, j] = cor12
            corrs.iloc[j, i] = cor12
    return corrs


def autocorrelations(
    s: pd.Series, lags: Iterable, progress_bar: bool = False
) -> pd.Series:
    # TODO: worth seeing if e.g. np.correlate is faster
    Raa = []
    iterable = tqdm(lags) if progress_bar else lags
    for lag in iterable:
        autocorr = s.autocorr(lag=lag)
        Raa.append(autocorr)
    return pd.Series(data=Raa)


def detrend(s: pd.Series, mode: str = "linear"):
    match mode.lower():
        case "linear":
            not_nan = ~np.isnan(s)
            m, b, _, _, _ = st.linregress(s.index[not_nan], s[not_nan])
            return s - m * s.index - b # type: ignore # TODO: test
        case "constant":
            return s - s.mean()
        case _:
            raise ValueError(f"Mode {mode} not recognized")
