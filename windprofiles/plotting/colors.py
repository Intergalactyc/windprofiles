import matplotlib.colors as mc
import colorsys


def change_luminosity(color, amount=1):
    """
    Multiplies the luminosity by the given amount.
    Values > 1 darken, < 1 lighten.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> change_luminosity('g', 0.3)
    >> change_luminosity('#F034A3', 0.6)
    >> change_luminosity((.3,.55,.1), 1.5)
    """
    try:
        c = mc.cnames[color]
    except Exception:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])
