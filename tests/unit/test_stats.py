import math

from pytest import approx

from windprofiles.lib.stats import constrained_linear_fit, ls_linear_fit


def test_ls_linear_fit_basic():
    # y = 10 + 0.25 * x, exactly
    xvals = [1.0, 2.0, 3.0, 4.0]
    yvals = [10.25, 10.5, 10.75, 11.0]
    a, b = ls_linear_fit(xvals, yvals)
    assert a == approx(10.0, abs=1e-9)
    assert b == approx(0.25, abs=1e-9)


def test_ls_linear_fit_duplicate_values_with_nan():
    # Regression test: duplicate x/y values alongside NaN pairs used to be
    # able to break the old xvals.remove(x)/yvals.remove(y)-while-iterating
    # NaN filter, since list.remove() removes the *first* matching element,
    # not necessarily the one paired with the NaN being dropped.
    xvals = [1.0, 2.0, 2.0, float("nan"), 3.0, 2.0]
    yvals = [10.0, 20.0, 21.0, 99.0, 30.0, float("nan")]

    a, b = ls_linear_fit(xvals, yvals)

    # Reference: manually filter to the correct pairs (dropping only the
    # (nan, 99.0) and (2.0, nan) pairs) and fit with the same least-squares formula.
    pairs = [(x, y) for x, y in zip(xvals, yvals) if not (math.isnan(x) or math.isnan(y))]
    assert pairs == [(1.0, 10.0), (2.0, 20.0), (2.0, 21.0), (3.0, 30.0)]
    n = len(pairs)
    sum_x = sum(p[0] for p in pairs)
    sum_y = sum(p[1] for p in pairs)
    sum_x2 = sum(p[0] * p[0] for p in pairs)
    sum_xy = sum(p[0] * p[1] for p in pairs)
    det = n * sum_x2 - sum_x * sum_x
    expected_a = (sum_y * sum_x2 - sum_x * sum_xy) / det
    expected_b = (n * sum_xy - sum_x * sum_y) / det

    assert a == approx(expected_a, abs=1e-9)
    assert b == approx(expected_b, abs=1e-9)


def test_constrained_linear_fit_fixed_intercept():
    xvals = [1.0, 2.0, 3.0, 4.0]
    yvals = [10.0, 12.0, 14.0, 16.0]  # y = 8 + 2x
    a, b = constrained_linear_fit(xvals, yvals, a=8.0)
    assert a == 8.0
    assert b == approx(2.0, abs=1e-9)


def test_constrained_linear_fit_duplicate_values_with_nan():
    xvals = [1.0, 2.0, 2.0, float("nan"), 3.0, 2.0]
    yvals = [10.0, 20.0, 21.0, 99.0, 30.0, float("nan")]

    a, b = constrained_linear_fit(xvals, yvals, a=0.0)

    pairs = [(x, y) for x, y in zip(xvals, yvals) if not (math.isnan(x) or math.isnan(y))]
    n = len(pairs)
    sum_x2 = sum(p[0] * p[0] for p in pairs)
    sum_xdy = sum(p[0] * (p[1] - 0.0) for p in pairs)
    expected_b = sum_xdy / sum_x2

    assert a == 0.0
    assert b == approx(expected_b, abs=1e-9)
