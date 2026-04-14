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


def constrained_linear_fit(
    xvals, yvals, a: float | None = None, b: float | None = None
):
    """
    ls_linear_fit but with either a or b fixed
    """
    if a is None and b is None:
        raise ValueError(
            "Either a or b must be specified (for unconstrained, use ls_linear_fit)"
        )
    if a is not None and b is not None:
        raise ValueError("Only one of a or b may be specified")

    xvals = list(xvals)
    if len(yvals) != len(xvals):
        raise RuntimeError("Lists must be of equal size")
    for x, y in zip(xvals, yvals):
        if math.isnan(x) or math.isnan(y):
            xvals.remove(x)
            yvals.remove(y)
    n = len(xvals)

    if a is not None:  # a (intercept) given
        if n == 0:
            return a, 0.0
        sum_x2 = sum(x * x for x in xvals)
        sum_xdy = sum(xvals[i] * (yvals[i] - a) for i in range(n))
        B = sum_xdy / sum_x2
        return a, B

    # otherwise, b (slope) given
    if n == 0:
        return 0.0, b
    A = (sum(yvals) - b * sum(xvals)) / n
    return A, b


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


# def power_fit_r2(xvals, yvals, *args, **kwargs):
#     a, b = power_fit(xvals, yvals, *args, **kwargs)
#     y_pred = [a * (x ** b) for x in xvals]
#     r2 = r2_score(yvals, y_pred)
#     return a, b, r2
# # TODO: make this a wrapper instead, have model functions, wrapper takes in model function, gets model parameters from call
# # e.g. instead of calling power_fit(xvals, yvals), call r2_wrap(power_fit, power_model, xvals, yvals)
# # >>> maybe separate these things into a new `profiles` module?


def log_fit(xvals, yvals):
    """
    Least squares fit to relationship y = a + b*log(x)
    Outputs the pair a,b describing fit
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


def constrained_log_fit(
    xvals, yvals, a: float | None = None, b: float | None = None
):
    """
    log_fit but with either a or b fixed
    """
    xconsider = []
    yconsider = []
    for x, y in zip(xvals, yvals):
        if not (math.isnan(x) or math.isnan(y)):
            if x <= 0:
                raise ValueError("Cannot do log fit with nonpositive x values")
            xconsider.append(x)
            yconsider.append(y)
    return constrained_linear_fit(np.log(xconsider), yconsider, a=a, b=b)


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
    z0 = np.exp(-A / B) if not np.isclose(B, 0.0, atol=1e-6) else 0.0
    if z0 > 10.0 or abs(ustar) > 10.0:
        z0 = np.nan
        ustar = np.nan
    return ustar, z0


def constrained_neutral_loglaw_fit(
    zvals, uvals, ustar: float, displacement: float = 0.0
):
    """
    neutral_loglaw_fit, but ustar is fixed
    """
    zconsider = []
    uconsider = []
    for z, u in zip(zvals, uvals):
        if z > displacement:
            zconsider.append(z - displacement)
            uconsider.append(u)
    A, B = constrained_log_fit(zconsider, uconsider, b=ustar / KAPPA)
    z0 = np.exp(-A / B)
    z0 = np.exp(-A / B) if not np.isclose(B, 0.0, atol=1e-6) else 0.0
    if z0 > 10.0:
        z0 = np.nan
    return z0


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
    return float(cor)  # pyright: ignore[reportArgumentType]


def get_correlations(
    df: pd.DataFrame, which: list | None = None
) -> pd.DataFrame:
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


def cohens_kappa(a, b, c, d):
    """
    a: pos_pos
    b: pos_neg
    c: neg_pos
    d: neg_neg
    """
    N = a + b + c + d
    if N == 0:
        return float("nan")

    Po = (a + d) / N

    pA_pos = (a + b) / N
    pA_neg = (c + d) / N
    pB_pos = (a + c) / N
    pB_neg = (b + d) / N

    Pe = pA_pos * pB_pos + pA_neg * pB_neg

    if np.isclose(Pe, 1.0):
        return float("nan")
    return (Po - Pe) / (1 - Pe)


def sign_cohens_kappa(df, col1, col2):
    a = len(df[(df[col1] > 0.0) & (df[col2] > 0.0)])
    b = len(df[(df[col1] > 0.0) & (df[col2] < 0.0)])
    c = len(df[(df[col1] < 0.0) & (df[col2] > 0.0)])
    d = len(df[(df[col1] < 0.0) & (df[col2] < 0.0)])
    return cohens_kappa(a, b, c, d)


def get_kappas(df: pd.DataFrame, which: list | None = None) -> pd.DataFrame:
    """
    Get sign-agreement Cohen's kappa pairwise between a list of columns (will use all columns
    in dataframe if no list is specified)
    """
    if which is None:
        which = list(df.columns)
    kapps = pd.DataFrame(data=0.0, index=which, columns=which)
    for i, col1 in enumerate(which):
        kapps.iloc[i, i] = 1.0
        for j, col2 in enumerate(which[:i]):
            k12 = sign_cohens_kappa(df, col1, col2)
            kapps.iloc[i, j] = k12
            kapps.iloc[j, i] = k12
    return kapps


def get_agreement_fractions(
    df: pd.DataFrame, classifier, which: list | None = None
) -> pd.DataFrame:
    if which is None:
        which = list(df.columns)
    aggs = pd.DataFrame(data=0.0, index=which, columns=which)
    for i, col1 in enumerate(which):
        aggs.iloc[i, i] = 1.0
        for j, col2 in enumerate(which[:i]):
            a12 = sum(classifier(df[col1]) == classifier(df[col2])) / len(df)
            aggs.iloc[i, j] = a12
            aggs.iloc[j, i] = a12
    return aggs


def get_spearman(df: pd.DataFrame, which: list | None = None) -> pd.DataFrame:
    """
    Get Spearman's rho values pairwise between a list of columns (will use all columns
    in dataframe if no list is specified)
    """
    if which is None:
        which = list(df.columns)
    rhos = pd.DataFrame(data=0.0, index=which, columns=which)
    for i, col1 in enumerate(which):
        rhos.iloc[i, i] = 1.0
        for j, col2 in enumerate(which[:i]):
            k12 = st.spearmanr(df[col1], df[col2]).statistic
            rhos.iloc[i, j] = k12
            rhos.iloc[j, i] = k12
    return rhos


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


def detrend(s: pd.Series, mode: str = "linear", m=None, b=None):
    # requires s be a series whose index is the independent variable over which s trends
    match mode.lower():
        case "linear":
            if m is None or b is None:
                not_nan = ~np.isnan(s)
                m, b, _, _, _ = st.linregress(s.index[not_nan], s[not_nan])
            return s - m * s.index - b  # type: ignore
        case "constant":
            return s - s.mean()
        case _:
            raise ValueError(f"Mode {mode} not recognized")
