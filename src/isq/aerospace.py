"""
Units and quantities common in aerospace engineering.

References:

- [ICAO] "Annex 5 - Units of Measurement to be Used in the Air and Ground Services," ICAO. [Online].
    Available: https://store.icao.int/en/annex-5-units-of-measurement-to-be-used-in-the-air-and-ground-services
"""
# TODO: ISO 2533:1975 (standard atmosphere)
# TODO: ISO 1151

from .core import Dimensionless, QtyKind
from .si import HOUR, KG, KWH, M_PERS, MIN, PA, RAD, K, L, M, W
from .us_customary import FT

#
# aircraft performance: state
#

# heading: [0, 360) degrees
HEADING_TRUE = QtyKind(RAD, ("heading", "true"))
HEADING_MAG = QtyKind(RAD, ("heading", "magnetic"))
HEADING_TRUE_WIND = QtyKind(RAD, ("heading", "true", "wind"))
HEADING_MAG_WIND = QtyKind(RAD, ("heading", "magnetic", "wind"))

ALT_PRESSURE = QtyKind(M, ("altitude", "pressure"))
"""Pressure altitude, as measured by the altimeter."""
ALT_DENSITY = QtyKind(M, ("altitude", "density"))
"""Density altitude, as measured by the altimeter."""
ALT_GEOP = QtyKind(M, ("altitude", "geopotential"))
"""Geopotential altitude, as measured from mean sea level."""
ALT_GEOM = QtyKind(M, ("altitude", "geometric"))
"""Geometric altitude, as measured from mean sea level."""
# height: measured from *specific* datum
ELEVATION = QtyKind(M, ("elevation",))  # ICAO 1.5
HEIGHT_GEODETIC = QtyKind(M, ("height", "geodetic"))
"""Geodetic height. See https://en.wikipedia.org/wiki/Geodetic_coordinates."""
HEIGHT_AGL = QtyKind(M, ("height", "above_ground_level"))
"""Height above ground level. Not to be confused with altitude."""  # ICAO 1.7

K_PERM = K * M**-1
"""Kelvin per meter, a unit of temperature gradient. For use in ISA."""

#
# aircraft parameters and geometry
#

_AC = "aircraft"
_ENGINE = "engine"
_MAX = "maximum"
# mass: ICAO 2.8
GROSS = QtyKind(KG, (_AC, "gross"))
CARGO_CAPACITY = QtyKind(KG, (_AC, "cargo_capacity"))
FUEL_CAPACITY = QtyKind(KG, (_AC, "fuel_capacity", "gravimetric"))
MTOW = QtyKind(KG, (_AC, "takeoff_weight", _MAX))
MZFW = QtyKind(KG, (_AC, "zero_fuel_weight", _MAX))
PAYLOAD = QtyKind(KG, (_AC, "payload"))
LANDING_WEIGHT = QtyKind(KG, (_AC, "landing_weight"))
MLW = QtyKind(KG, (_AC, "landing_weight", _MAX))

TANK_CAPACITY = QtyKind(L, (_AC, "tank_capacity"))  # ICAO 1.14

ENDURANCE = QtyKind(HOUR, ("aircraft", "endurance"))  # ICAO 1.6

#
# aircraft performance: state vector
#
# TODO: move to .fluid mod
# - static, dynamic, total temperature
# - static, dynamic, impact, total pressure
# - Cp, Cv, R, Rhat...

# temperature 6.7
TEMP_SAT = QtyKind(K, ("static",))
TEMP_TAT = QtyKind(K, ("total",))
TEMP_ISA = QtyKind(K, ("static", "isa"))
"""static air temperature (international standard atmosphere)."""

# linear velocity
IAS = QtyKind(M_PERS, ("airspeed", "indicated"))
"""Indicated airspeed, as measured directly from the airspeed indicator."""
CAS = QtyKind(M_PERS, ("airspeed", "calibrated"))
"""Calibrated airspeed, [IAS][isq.aerospace.IAS] corrected for instrument and position errors."""
EAS = QtyKind(M_PERS, ("airspeed", "equivalent"))
"""Equivalent airspeed."""
TAS = QtyKind(M_PERS, ("airspeed", "true"))
"""True airspeed."""
GS = QtyKind(M_PERS, ("airspeed", "ground"))
"""Ground speed."""
WIND_SPEED = QtyKind(M_PERS, ("wind",))
"""Wind speed."""
SPEED_OF_SOUND = QtyKind(M_PERS, ("sound",))
"""Speed of sound."""

FT_PER_MIN = FT * MIN**-1
VS = QtyKind(M_PERS, ("vertical_speed",))  # ICAO 4.15
"""Vertical speed, rate of climb or descent.
Commonly expressed in [feet per minute][isq.aerospace.FT_PER_MIN]."""

MACH = Dimensionless("mach")
"""Mach number, the ratio between the [TAS][isq.aerospace.TAS]
and the [speed of sound][isq.aerospace.SPEED_OF_SOUND]."""

#
# engine
#
SHAFT_POWER = QtyKind(W, (_AC, _ENGINE, "shaft"))
TSFC = QtyKind(KG * KWH**-1, (_AC, _ENGINE))  # ICAO 5.3
KG_PERS = KG * M_PERS**-1  # ICAO 5.4
MASS_FLOW_RATE = QtyKind(KG_PERS, (_AC, _ENGINE))

#
# aeroacoustics
#
# TODO: dBA, EPNdB etc.

#
# pilot specific
#
PRESSURE_ALTIMETER = QtyKind(PA, ("altimeter",))
"""Altimeter setting."""
RUNWAY_LENGTH = QtyKind(M, ("runway", "length"))  # ICAO 1.12
RVR = QtyKind(M, ("runway", "visual_range"))  # ICAO 1.13
VISIBILITY = QtyKind(M, ("meteo", "visibility"))  # ICAO 1.15
