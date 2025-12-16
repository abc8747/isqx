"""
Units and quantities common in aerospace engineering.

See: [isqx._citations.ICAO][]
"""
# TODO: ISO 2533:1975 (standard atmosphere)
# TODO: ISO 1151

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Literal

from ._core import (
    DELTA,
    Dimensionless,
    OriginAt,
    QtyKind,
    Quantity,
    ratio,
    slots,
)
from ._iso80000 import (
    ALTITUDE,
    DISTANCE,
    DRAG,
    DYNAMIC_PRESSURE,
    HOUR,
    KG,
    LIFT,
    M_PERS,
    MASS,
    MASS_FLOW_RATE,
    MIN,
    PA,
    POWER,
    PRESSURE,
    RAD,
    TEMPERATURE,
    K,
    L,
    M,
    N,
    S,
)
from .usc import FT

#
# aircraft performance: state
#

# heading: [0, 360) degrees
HEADING = QtyKind(RAD, ("heading",))
HEADING_TRUE = HEADING["true"]
HEADING_MAG = HEADING["magnetic"]
HEADING_TRUE_WIND = HEADING_TRUE["wind"]
HEADING_MAG_WIND = HEADING_MAG["wind"]
GROUND_TRACK = HEADING["ground_track"]
"""Direction of the aircraft's velocity vector relative to the ground."""

PRESSURE_ALTITUDE = ALTITUDE["pressure"]
"""Pressure altitude, as measured by the altimeter (standard pressure setting 1013.25 hPa)."""
DENSITY_ALTITUDE = ALTITUDE["density"]
"""Density altitude, as measured by the altimeter."""
GEOPOTENTIAL_ALTITUDE = ALTITUDE["geopotential"]
"""Geopotential altitude, as measured from mean sea level."""
GEOMETRIC_ALTITUDE = ALTITUDE["geometric"]
"""Altitude measured from mean sea level (e.g. via GNSS)."""
# height: measured from *specific* datum
ELEVATION = QtyKind(M, ("elevation",))  # ICAO 1.5
HEIGHT_GEODETIC = QtyKind(M, ("height", "geodetic"))
"""Height above the reference ellipsoid."""
HEIGHT_AGL = QtyKind(M, ("height", "above_ground_level"))
"""Height above ground level (radio altimeter)."""

L_OVER_D = ratio(LIFT(N), DRAG(N))

K_PERM = K * M**-1
"""Kelvin per meter, a unit of temperature gradient. For use in ISA."""

#
# aircraft design
#

AIRCRAFT_MASS = MASS["aircraft"]
GROSS = AIRCRAFT_MASS["gross"]
CARGO_CAPACITY = AIRCRAFT_MASS["cargo_capacity"]
FUEL_CAPACITY = AIRCRAFT_MASS["fuel_capacity"]
TAKEOFF_MASS = AIRCRAFT_MASS["takeoff"]
LANDING_MASS = AIRCRAFT_MASS["landing"]
MAXIMUM_TAKEOFF_WEIGHT = TAKEOFF_MASS["maximum"]
ZERO_FUEL_WEIGHT = AIRCRAFT_MASS["zero_fuel_weight"]
PAYLOAD = AIRCRAFT_MASS["payload"]

TANK_CAPACITY = QtyKind(L, ("aircraft", "tank_capacity"))  # ICAO 1.14
ENDURANCE = QtyKind(HOUR, ("aircraft", "endurance"))  # ICAO 1.6

#
# aircraft performance
#

STATIC_TEMPERATURE = TEMPERATURE["static"]
TOTAL_TEMPERATURE = TEMPERATURE["total"]
"""Also known as stagnation temperature."""
CONST_TEMPERATURE_ISA: Annotated[Decimal, STATIC_TEMPERATURE(K)] = Decimal(
    "288.15"
)
TEMPERATURE_DEVIATION_ISA = STATIC_TEMPERATURE[
    DELTA, OriginAt(Quantity(CONST_TEMPERATURE_ISA, K))
]
"""Deviation from the [ISA temperature at sea level][isqx.aerospace.CONST_TEMPERATURE_ISA]."""

TOTAL_PRESSURE = PRESSURE["total"]
IMPACT_PRESSURE = DYNAMIC_PRESSURE["impact"]

# linear velocity
AIRSPEED = QtyKind(M_PERS, ("airspeed",))
INDICATED_AIRSPEED = AIRSPEED["indicated"]
"""Indicated airspeed (IAS), as measured directly from the pitot-static system."""
CALIBRATED_AIRSPEED = AIRSPEED["calibrated"]
"""Calibrated airspeed (CAS), [IAS][isqx.aerospace.IAS] corrected for instrument and position errors."""
EQUIVALENT_AIRSPEED = AIRSPEED["equivalent"]
"""Equivalent airspeed (EAS), [CAS][isqx.aerospace.CAS] corrected for compressibility."""
TRUE_AIRSPEED = AIRSPEED["true"]
"""True airspeed (TAS), speed relative to the airmass."""
GROUND_SPEED = AIRSPEED["ground"]
"""Speed relative to the ground."""
WIND_SPEED = QtyKind(M_PERS, ("wind",))
"""Wind speed."""
SPEED_OF_SOUND = QtyKind(M_PERS, ("sound",))
"""Speed of sound."""

FT_PER_MIN = FT * MIN**-1
VERTICAL_RATE = QtyKind(M_PERS, ("vertical_rate",))
"""Rate of climb or descent.

Commonly expressed in [feet per minute][isqx.aerospace.FT_PER_MIN]."""
VERTICAL_RATE_INERTIAL = VERTICAL_RATE["inertial"]
"""Vertical rate derived from inertial sensors/GNSS."""
VERTICAL_RATE_BAROMETRIC = VERTICAL_RATE["barometric"]
"""Vertical rate derived from barometric pressure changes."""

SPECIFIC_IMPULSE = QtyKind(S, ("specific_impulse",))
RANGE = DISTANCE["range"]

#
# propulsion
#
ENGINE_POWER = POWER["engine"]
SHAFT_POWER = ENGINE_POWER["shaft"]
ENGINE_MASS_FLOW_RATE = MASS_FLOW_RATE["engine"]
KG_PERS = KG * S**-1
THRUST_SPECIFIC_FUEL_CONSUMPTION = QtyKind(KG_PERS * N**-1, ("engine",))
BPR = Dimensionless("bypass_ratio")
#
# aeroacoustics
#
# TODO: dBA, EPNdB etc.

#
# navigation
#


@dataclass(frozen=True, **slots)
class Aerodrome:
    ident: str
    ident_kind: Literal["icao", "iata"] | str


PRESSURE_ALTIMETER = QtyKind(PA, ("altimeter",))
"""Altimeter setting (QNH/QFE)."""
RUNWAY_LENGTH = QtyKind(M, ("runway", "length"))  # ICAO 1.12
RUNWAY_VISUAL_RANGE = QtyKind(M, ("runway", "visual_range"))  # ICAO 1.13
VISIBILITY = QtyKind(M, ("meteo", "visibility"))  # ICAO 1.15

#
# adsb/mode s
#

ICAO_ADDRESS = Dimensionless("icao_address_24_bit")
"""Unique 24-bit aircraft address assigned by ICAO."""
SQUAWK_CODE = Dimensionless("squawk_code_12_bit")
"""Mode A code (4 octal digits)."""

NAVIGATION_UNCERTAINTY_CATEGORY_POSITION = Dimensionless("adsb_nucp")
NAVIGATION_UNCERTAINTY_CATEGORY_VELOCITY = Dimensionless("adsb_nucv")
NAVIGATION_ACCURACY_CATEGORY_POSITION = Dimensionless("adsb_nacp")
NAVIGATION_ACCURACY_CATEGORY_VELOCITY = Dimensionless("adsb_nacv")
NAVIGATION_INTEGRITY_CATEGORY = Dimensionless("adsb_nic")
SURVEILLANCE_INTEGRITY_LEVEL = Dimensionless("adsb_sil")
