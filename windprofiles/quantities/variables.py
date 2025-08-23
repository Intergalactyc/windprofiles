from windprofiles.quantities.structures import (
    Dimension,
    Variable,
)

_v_timestamp = Variable(
    "Timestamp", Dimension.Timestamp, ["Datetime"], ["time"]
)

_v_temperature = Variable(
    "Temperature",
    Dimension.Temperature,
    ["T", "Temp"],
    [
        "tmpr",
        "air_temp",
        "air_temperature",
        "ta",
        "at",
        "2t",
        "t2",
        "tmp",
        "tair",
    ],
)  # Variable.Temperature

_v_dewpoint = Variable(
    "Dewpoint",
    Dimension.Temperature,
    ["Td"],
    ["dwpt", "dewpt", "dew_point", "dew", "tdew", "d2m"],
)  # Variable.Dewpoint

_v_relative_humidity = Variable(
    "Relative Humidity",
    Dimension.Dimless,
    ["RH", "Humidity"],
    [
        "relative_humidity",
        "rhum",
        "relh",
        "rel_hum",
        "rel_humidity",
        "humid",
        "RH_pct",
        "rh2",
    ],
)  # Variable.RelativeHumidity

_v_wind_direction = Variable(
    "Wind Direction",
    Dimension.Angle,
    ["Direction", "WD"],
    [
        "wdir",
        "dir",
        "wind_dir",
        "wind_direction",
        "theta_w",
    ],
)  # Variable.WindDirection

_v_wind_speed = Variable(
    "Wind Speed",
    Dimension.Speed,
    ["Speed", "WS"],
    ["wind_speed", "ws", "wspd", "wind_spd", "speed", "spd", "mws", "ff10"],
)  # Variable.WindSpeed

_v_u_wind = Variable(
    "East Wind",
    Dimension.Speed,
    ["U", "Ux"],
    ["u_x", "u_vel", "x_vel", "u_comp", "u_component", "u_wind", "u10", "ua"],
)  # Variable.U

_v_v_wind = Variable(
    "North Wind",
    Dimension.Speed,
    ["V", "Uy"],
    ["u_y", "v_vel", "y_vel", "v_comp", "v_component", "v_wind", "v10", "va"],
)  # Variable.V

_v_w_wind = Variable(
    "Vertical Wind",
    Dimension.Speed,
    ["W", "Uz"],
    ["u_z", "w_vel", "z_vel", "w_comp", "w_component", "w_wind"],
)  # Variable.W

_v_pressure = Variable(
    "Pressure",
    Dimension.Pressure,
    ["P"],
    ["pres", "sp", "psfc", "press", "pa"],
)  # Variable.Pressure

_v_sonic_temp = Variable(
    "Sonic Temperature",
    Dimension.Temperature,
    ["Ts"],
    ["tsonic", "tson", "t_sonic", "sonic_temperature"],
)  # Variable.SonicTemperature

_v_potential_temp = Variable(
    "Potential Temperature",
    Dimension.Temperature,
    ["Tp"],
    ["tpot", "theta", "pot_temp", "potential_temperature"],
)  # Variable.PotentialTemperature

_v_virtual_temp = Variable(
    "Virtual Temperature",
    Dimension.Temperature,
    ["Tv"],
    ["virtual_temp", "virtual_temperature"],
)  # Variable.VirtualTemperature

_v_vp_temp = Variable(
    "Virtual Potential Temperature",
    Dimension.Temperature,
    ["VPT"],
    ["theta_v", "virt_pot_temp", "virtual_potential_temperature"],
)  # Variable.VPT

_v_friction_velocity = Variable(
    "Friction Velocity", Dimension.Speed, ["UStar"], ["u*"]
)  # Variable.FrictionVelocity

_v_specific_humidity = Variable(
    "Specific Humidity",
    Dimension.Specific,
    ["q"],
    ["spec_hum", "specific_humidity", "sh", "q2", "humidity_specific"],
)  # Variable.SpecificHumidity

_v_absolute_humidity = Variable(
    "Absolute Humidity",
    Dimension.Density,
    ["AH"],
    ["abs_hum", "air_density_water", "h2o_density", "rho_v"],
)  # Variable.AbsoluteHumidity

_v_mixing_ratio = Variable(
    "Mixing Ratio",
    Dimension.Specific,
    ["r"],
    ["mix_ratio", "mixing_ratio", "mr", "qv", "qvapor", "mixr", "mix"],
)  # Variable.MixingRatio
