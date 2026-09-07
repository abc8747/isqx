"""
Units and quantities common in aerospace engineering.

See: [isqx._citations.ICAO][]
"""
# TODO: ISO 2533:1975 (standard atmosphere)
# TODO: ISO 1151

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated

from ._core import (
    DELTA,
    CompositionError,
    Dimensionless,
    Expr,
    HasTagValidation,
    OriginAt,
    QtyKind,
    Quantity,
    Tag,
    dimension,
    ratio,
    slots,
)
from ._iso80000 import (
    ALTITUDE,
    AREA,
    DENSITY,
    DISTANCE,
    DRAG,
    DRAG_COEFFICIENT,
    DYNAMIC_PRESSURE,
    HOUR,
    KG,
    LENGTH,
    LIFT,
    M_PERS,
    MACH_NUMBER,
    MASS,
    MASS_FLOW_RATE,
    MIN,
    MOMENT_OF_FORCE,
    PA,
    POWER,
    PRESSURE,
    RAD,
    RAD_PERS,
    SPECIFIC_ENERGY,
    STATIC_PRESSURE,
    TEMPERATURE,
    VELOCITY,
    VOLUME,
    K,
    L,
    M,
    N,
    S,
    W,
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
GEODETIC_HEIGHT = QtyKind(M, ("height", "geodetic"))
"""Height above the reference ellipsoid."""
HEIGHT_ABOVE_GROUND_LEVEL = QtyKind(M, ("height", "above_ground_level"))
"""Height above ground level (radio altimeter)."""
# do we define AAL (above aerodrome level)?

L_OVER_D = ratio(LIFT(N), DRAG(N))

K_PERM = K * M**-1
"""Kelvin per meter, a unit of temperature gradient. For use in ISA."""
ENERGY_HEIGHT = LENGTH["energy_height"]
"""Specific energy expressed as a height."""
SPECIFIC_EXCESS_POWER = QtyKind(M_PERS, ("specific_excess_power",))

#
# aircraft geometry
#

WINGSPAN = LENGTH["wingspan"]
CHORD = LENGTH["chord"]
MEAN_AERODYNAMIC_CHORD = CHORD["mean_aerodynamic"]
"""Mean aerodynamic chord (MAC)."""
MEAN_AERODYNAMIC_CHORD_LEADING_EDGE_POSITION = CHORD[
    "mean_aerodynamic", "leading_edge"
]
"""Longitudinal position of the leading edge of the mean aerodynamic chord."""
MEAN_GEOMETRIC_CHORD = CHORD["mean_geometric"]
"""Mean geometric chord (Standard Mean Chord)."""
WING_AREA = AREA["wing"]
"""Reference wing area."""  # TODO Wimpress and W(airbus)
WETTED_AREA = AREA["wetted"]
PLANFORM_AREA = AREA["planform"]
FRONTAL_AREA = AREA["frontal"]
"""Cross-sectional area perpendicular to the flow."""
DISK_AREA = AREA["disk"]
"""Area swept by a propeller or rotor."""
TAIL_AREA = AREA["tail"]
TAIL_MOMENT_ARM = LENGTH["tail_moment_arm"]
ASPECT_RATIO = Dimensionless("aspect_ratio")
TAPER_RATIO = Dimensionless("taper_ratio")
SWEEP_ANGLE = QtyKind(RAD, ("angle", "sweep"))
DIHEDRAL_ANGLE = QtyKind(RAD, ("angle", "dihedral"))
TWIST_ANGLE = QtyKind(RAD, ("angle", "twist"))
"""Washout or washin angle."""
FINENESS_RATIO = Dimensionless("fineness_ratio")
"""Ratio of length to maximum diameter for a fuselage or body."""

#
# aerodynamics
#

ANGLE_OF_ATTACK = QtyKind(RAD, ("angle", "angle_of_attack"))
"""Angle between the chord line and the relative wind vector."""
SIDESLIP_ANGLE = QtyKind(RAD, ("angle", "sideslip"))
"""Angle between the relative wind vector and the plane of symmetry."""
DOWNWASH_ANGLE = QtyKind(RAD, ("angle", "downwash"))

CRITICAL_MACH_NUMBER = MACH_NUMBER["critical"]
DRAG_DIVERGENCE_MACH_NUMBER = MACH_NUMBER["drag_divergence"]

ZERO_LIFT_DRAG_COEFFICIENT = DRAG_COEFFICIENT["zero_lift"]
LIFT_INDUCED_DRAG_COEFFICIENT = DRAG_COEFFICIENT["lift_induced"]
INDUCED_DRAG_COEFFICIENT = DRAG_COEFFICIENT["induced"]

OSWALD_EFFICIENCY = Dimensionless("oswald_efficiency_factor")
"""Span efficiency factor."""
# TODO: stability derivatives
PITCHING_MOMENT_COEFFICIENT = Dimensionless("pitching_moment_coefficient")
ROLLING_MOMENT_COEFFICIENT = Dimensionless("rolling_moment_coefficient")
YAWING_MOMENT_COEFFICIENT = Dimensionless("yawing_moment_coefficient")
PRESSURE_COEFFICIENT = Dimensionless("pressure_coefficient")
SKIN_FRICTION_COEFFICIENT = Dimensionless("skin_friction_coefficient")
LIFT_SLOPE = Dimensionless("lift_slope")
"""Change in lift coefficient per unit angle of attack (per radian)."""

CIRCULATION = QtyKind(M**2 * S**-1, ("circulation",))

#
# mass buildup
# NOTE: technically 'aircraft weight' should be named 'aircraft mass'
# but we choose to adopt standard operational abbreviations (OEW, DOW, ZFW, etc.).
#

AIRCRAFT_MASS = MASS["aircraft"]
STANDARD_ITEMS_WEIGHT = AIRCRAFT_MASS["standard_items"]
"""Mass of *standard items* used in aircraft weight-and-balance.

Equipment and fluids that are not integral to a particular aircraft and do not
vary between aircraft of the same type. Examples include unusable fuel and
fluids, engine oil, toilet fluid, emergency equipment, galley structure, and
supplementary electronic equipment ([FAA AC 120-27F, Appendix A.31][isqx._citations.FAA_AC_120_27F]).
"""
BASIC_WEIGHT = AIRCRAFT_MASS["basic"]
"""Basic weight, a load-control starting weight. Also known as Basic Empty
Weight or Fleet Empty Weight.

Includes fixed equipment, system fluids, unusable fuel, and configuration
equipment including galley structure ([IATA AIDM](https://airtechzone.iata.org/aidm_model/25.2/index.htm?goto=5:1:2:8054)).
It is the aircraft empty weight adjusted for variations in
[standard items][isqx.aerospace.STANDARD_ITEMS_WEIGHT]
([FAA AC 120-27F, Appendix A.2][isqx._citations.FAA_AC_120_27F]).
"""
OPERATING_ITEMS_WEIGHT = AIRCRAFT_MASS["operating_items"]
"""Aggregate mass of operating items (OI) included in [dry operating weight][isqx.aerospace.DRY_OPERATING_WEIGHT].

Personnel, equipment, and supplies necessary for a particular
operation but not included in the [basic empty weight][isqx.aerospace.BASIC_WEIGHT].
These items may vary for a particular aircraft.
([FAA AC 120-27F, Appendix A.23][isqx._citations.FAA_AC_120_27F])

[EASA Air Operations][isqx._citations.EASA_EAR_OPS] requires the operator to
determine the mass of operating items and crew members included in dry
operating mass.
"""
OPERATING_EMPTY_WEIGHT = AIRCRAFT_MASS["operating_empty"]
"""Operating empty weight (OEW).

The [basic weight][isqx.aerospace.BASIC_WEIGHT] plus [operating items][isqx.aerospace.OPERATING_EMPTY_WEIGHT]
excluding usable fuel and payload.

Whether crew/crew baggage and catering/service items are included depends on the
manufacturer or operator.

This term is typically used interchangeably with the [dry operating weight][isqx.aerospace.DRY_OPERATING_WEIGHT]
"""
DRY_OPERATING_WEIGHT = AIRCRAFT_MASS["dry_operating"]
"""Dry operating weight/mass (DOW).

Total mass of the aircraft **ready for a specific type of operation**, excluding
usable fuel and traffic load
([EASA Air Operations, Annex I, 2025/133(41)][isqx._citations.EASA_EAR_OPS]).

This term is typically used interchangeably with the [operating empty weight][isqx.aerospace.OPERATING_EMPTY_WEIGHT].
It typically includes crew/crew baggage, catering/service equipment, potable
water and other operator-specific items ([IATA AIDM](https://airtechzone.iata.org/aidm_model/25.2/index.htm?goto=5:1:2:8054)).
"""
PAYLOAD = AIRCRAFT_MASS["payload"]
"""Mass carried as payload. Typically includes weight of occupants, cargo and
baggage (FAA-H-8083-1B, GAMA)."""
TRAFFIC_LOAD = AIRCRAFT_MASS["traffic_load"]
"""Operational traffic load.

Load carried in addition to dry operating mass, including passengers, baggage,
freight/cargo and, where applicable, ballast or other non-revenue load
([EASA Air Operations, Annex I, 2025/133(120)][isqx._citations.EASA_EAR_OPS]).
"""
CARGO_CAPACITY = AIRCRAFT_MASS["cargo_capacity"]

ZERO_FUEL_WEIGHT = AIRCRAFT_MASS["zero_fuel"]
"""Total aircraft mass excluding usable fuel (ZFW)."""
MAXIMUM_ZERO_FUEL_WEIGHT = ZERO_FUEL_WEIGHT["maximum"]
RAMP_WEIGHT = AIRCRAFT_MASS["ramp"]
"""Aircraft mass before taxi, normally including the fuel expected to be consumed before takeoff."""
MAXIMUM_RAMP_WEIGHT = RAMP_WEIGHT["maximum"]
TAKEOFF_WEIGHT = AIRCRAFT_MASS["takeoff"]
"""Aircraft mass at the start of the takeoff roll."""
MAXIMUM_TAKEOFF_WEIGHT = TAKEOFF_WEIGHT["maximum"]
REGULATED_TAKEOFF_WEIGHT = TAKEOFF_WEIGHT["regulated"]
LANDING_WEIGHT = AIRCRAFT_MASS["landing"]
MAXIMUM_LANDING_WEIGHT = LANDING_WEIGHT["maximum"]

#
# CAT.OP.MPA.181 fuel planning
#

FUEL_MASS = MASS["aircraft", "fuel"]
"""Mass of aircraft fuel."""
FUEL_VOLUME = VOLUME["aircraft", "fuel"]
"""Volume of aircraft fuel."""
FUEL_DENSITY = DENSITY["aircraft", "fuel"]
"""Fuel mass per unit volume."""
FUEL_MASS_FLOW_RATE = MASS_FLOW_RATE["aircraft", "fuel"]
"""Rate of fuel-mass consumption."""


@dataclass(frozen=True, **slots)
class _FuelRole(HasTagValidation):
    """Semantic role applied to an aircraft fuel mass or fuel volume."""

    name: str

    def __hash__(self) -> int:  # required for py39
        return hash((self.__class__.__name__, self.name))

    def __validate_tag__(self, reference: Expr, tags: tuple[Tag, ...]) -> None:
        if "aircraft" not in tags or "fuel" not in tags:
            raise CompositionError(
                outer=_FuelRole,
                inner=reference,
                msg="fuel roles require an aircraft-fuel expression",
                help="apply the role to FUEL_MASS or FUEL_VOLUME",
            )
        if dimension(reference) not in (dimension(KG), dimension(L)):
            raise CompositionError(
                outer=_FuelRole,
                inner=reference,
                msg="fuel roles apply only to mass or volume quantities",
                help="apply the role to FUEL_MASS or FUEL_VOLUME",
            )
        if sum(isinstance(tag, _FuelRole) for tag in tags) > 1:
            raise CompositionError(
                outer=_FuelRole,
                inner=self,
                msg="a fuel quantity cannot have multiple fuel roles",
            )


# to be used with FUEL_MASS[...] or FUEL_VOLUME[...].
TAXI_FUEL = _FuelRole("taxi_fuel")
"""Fuel expected to be used before takeoff ([CAT.OP.MPA.181(c)(1)][isqx._citations.EU_2021_1296])."""
TRIP_FUEL = _FuelRole("trip_fuel")
"""Fuel required from takeoff, or an in-flight replanning point, to landing at the destination aerodrome ([CAT.OP.MPA.181(c)(2)][isqx._citations.EU_2021_1296])."""
# not defining a "reserve fuel"
CONTINGENCY_FUEL = _FuelRole("contingency_fuel")
"""Fuel required to compensate for unforeseen factors ([CAT.OP.MPA.181(c)(3)][isqx._citations.EU_2021_1296])."""
ALTERNATE_FUEL = _FuelRole("alternate_fuel")
"""Fuel required from the destination to the destination alternate, or the prescribed destination holding amount when no alternate is required ([CAT.OP.MPA.181(c)(4)][isqx._citations.EU_2021_1296])."""
FINAL_RESERVE_FUEL = _FuelRole("final_reserve_fuel")
"""Fuel calculated at holding speed at 1500 ft above aerodrome elevation, subject to the prescribed reciprocating- or turbine-engine minimum duration ([CAT.OP.MPA.181(c)(5)][isqx._citations.EU_2021_1296])."""
ADDITIONAL_FUEL = _FuelRole("additional_fuel")
"""Fuel required for the critical fuel en-route-alternate scenario after a consumption-increasing aircraft failure when the other specified components are insufficient ([CAT.OP.MPA.181(c)(6)][isqx._citations.EU_2021_1296])."""
EXTRA_FUEL = _FuelRole("extra_fuel")
"""Fuel carried for anticipated delays or specific operational constraints ([CAT.OP.MPA.181(c)(7)][isqx._citations.EU_2021_1296])."""
DISCRETIONARY_FUEL = _FuelRole("discretionary_fuel")
"""Fuel required at the commander's discretion ([CAT.OP.MPA.181(c)(8)][isqx._citations.EU_2021_1296])."""

TANKERING_FUEL = _FuelRole("tankering_fuel")  # nonstandard
"""Supplementary fuel carried for operational reasons (for example, to offset higher fuel price at the destination)."""

# there are some operational fuel aggregates, such as:
# takeoff fuel, fuel on board (FOB), minimum diversion fuel, destination hold fuel
# but we do not define them here because of a lack of standardised definition

AIRCRAFT_LOAD_INDEX = Dimensionless(
    "aircraft_load_index"
)  # TODO DOI = BI + \Delta I_op? LIZFW, fuel index?, LITOW, LILAW?
"""Dimensionless load-distribution index used in weight-and-balance."""
CENTER_OF_GRAVITY_MAC = Dimensionless(
    "center_of_gravity_mean_aerodynamic_chord"
)  # TODO: MACZFW, MACTOW, MACTOW
"""Centre-of-gravity position as a fraction of mean aerodynamic chord."""

#
# aircraft design: misc
#

TANK_CAPACITY = QtyKind(L, ("aircraft", "tank_capacity"))  # ICAO 1.14
ENDURANCE = QtyKind(HOUR, ("aircraft", "endurance"))  # ICAO 1.6

WING_LOADING = QtyKind(N * M**-2, ("wing_loading",))
"""Weight of the aircraft divided by the wing area."""
POWER_LOADING = QtyKind(N * W**-1, ("power_loading",))
"""Weight of the aircraft divided by the engine power."""
THRUST_LOADING = Dimensionless("thrust_loading")
"""Thrust to weight ratio."""

#
# flight dynamics
#

LOAD_FACTOR = Dimensionless("load_factor")
"""Ratio of lift to weight (n)."""

ANGULAR_VELOCITY = QtyKind(RAD_PERS, ("angular_velocity",))
ROLL_RATE = ANGULAR_VELOCITY["roll"]
"""Angular velocity about the body X axis."""
PITCH_RATE = ANGULAR_VELOCITY["pitch"]
"""Angular velocity about the body Y axis."""
YAW_RATE = ANGULAR_VELOCITY["yaw"]
"""Angular velocity about the body Z axis."""
TURN_RATE = ANGULAR_VELOCITY["turn"]
"""Rate of change of heading."""

ATTITUDE = QtyKind(RAD, ("attitude",))
BANK_ANGLE = ATTITUDE["bank"]
PITCH_ANGLE = ATTITUDE["pitch"]
FLIGHT_PATH_ANGLE = ATTITUDE["flight_path"]
"""Angle between the velocity vector and the horizon."""

AIRCRAFT_MOMENT = MOMENT_OF_FORCE["aircraft"]
PITCHING_MOMENT = AIRCRAFT_MOMENT["pitching"]
ROLLING_MOMENT = AIRCRAFT_MOMENT["rolling"]
YAWING_MOMENT = AIRCRAFT_MOMENT["yawing"]

#
# stability and control
#

STATIC_MARGIN = Dimensionless("static_margin")
"""Distance between the neutral point and the center of gravity, normalized by MAC."""
NEUTRAL_POINT = DISTANCE["neutral_point"]
"""Longitudinal position of the aerodynamic center of the whole aircraft."""
CENTER_OF_GRAVITY = DISTANCE["center_of_gravity"]
TAIL_VOLUME_COEFFICIENT = Dimensionless("tail_volume_coefficient")
HORIZONTAL_TAIL_VOLUME_COEFFICIENT = TAIL_VOLUME_COEFFICIENT["horizontal"]
VERTICAL_TAIL_VOLUME_COEFFICIENT = TAIL_VOLUME_COEFFICIENT["vertical"]

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

TEMPERATURE_RATIO = ratio(
    STATIC_TEMPERATURE(K), Quantity(CONST_TEMPERATURE_ISA, K)
)
CONST_PRESSURE_ISA: Annotated[int, STATIC_PRESSURE(PA)] = 101325
PRESSURE_RATIO = ratio(STATIC_PRESSURE(PA), Quantity(CONST_PRESSURE_ISA, PA))
CONST_DENSITY_ISA: Annotated[Decimal, DENSITY(KG * M**-3)] = Decimal("1.225")
DENSITY_RATIO = ratio(
    DENSITY(KG * M**-3), Quantity(CONST_DENSITY_ISA, KG * M**-3)
)

# linear velocity
AIRSPEED = QtyKind(M_PERS, ("airspeed",))
INDICATED_AIRSPEED = AIRSPEED["indicated"]
"""Indicated airspeed (IAS), as measured directly from the pitot-static system."""
CALIBRATED_AIRSPEED = AIRSPEED["calibrated"]
"""Calibrated airspeed (CAS), [IAS][isqx.aerospace.INDICATED_AIRSPEED] corrected for instrument and position errors."""
EQUIVALENT_AIRSPEED = AIRSPEED["equivalent"]
"""Equivalent airspeed (EAS), [CAS][isqx.aerospace.CALIBRATED_AIRSPEED] corrected for compressibility."""
TRUE_AIRSPEED = AIRSPEED["true"]
"""True airspeed (TAS), speed relative to the airmass."""
GROUND_SPEED = AIRSPEED["ground"]
"""Speed relative to the ground."""
STALL_SPEED = AIRSPEED["stall"]
APPROACH_SPEED = AIRSPEED["approach"]
TAKEOFF_SPEED = AIRSPEED["takeoff"]
ROTATE_SPEED = AIRSPEED["rotate"]
V1_SPEED = AIRSPEED["v1"]
V2_SPEED = AIRSPEED["v2"]
VREF_SPEED = AIRSPEED["vref"]
# TODO: other v speeds
CORNER_SPEED = AIRSPEED["corner"]
"""The speed at which the maximum lift coefficient and the maximum load factor are reached simultaneously."""
WIND_SPEED = QtyKind(M_PERS, ("wind",))
"""Wind speed."""
SPEED_OF_SOUND = QtyKind(M_PERS, ("sound",))
"""Speed of sound."""
DENSITY_FACTOR = Dimensionless("density_factor")
"""Square root of local air density divided by a stated reference density."""
COMPRESSIBILITY_FACTOR = Dimensionless("compressibility_factor")
"""Dimensionless correction factor used when relating compressible-flow airspeeds."""

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
TAKEOFF_DISTANCE = DISTANCE["takeoff"]
LANDING_DISTANCE = DISTANCE["landing"]
TURN_RADIUS = DISTANCE["turn_radius"]

#
# propulsion
#
SHAFT_POWER = POWER["shaft"]
"""Power delivered to a shaft (e.g. turboprop)."""
BRAKE_POWER = POWER["brake"]
EQUIVALENT_SHAFT_POWER = SHAFT_POWER["equivalent"]

ENGINE_MASS_FLOW_RATE = MASS_FLOW_RATE["engine"]
SPECIFIC_THRUST = QtyKind(N * S * KG**-1, ("specific_thrust",))
KG_PERS = KG * S**-1
THRUST_SPECIFIC_FUEL_CONSUMPTION = QtyKind(KG_PERS * N**-1, ("engine",))
"""Fuel mass flow rate per unit thrust."""
POWER_SPECIFIC_FUEL_CONSUMPTION = QtyKind(
    KG_PERS * W**-1, ("engine", "power_specific")
)
"""Fuel mass flow rate per unit power."""
FUEL_SPECIFIC_ENERGY = SPECIFIC_ENERGY["fuel"]
EXHAUST_VELOCITY = VELOCITY["exhaust"]
BYPASS_RATIO = ratio(
    ENGINE_MASS_FLOW_RATE["bypass"].si_coherent(),
    ENGINE_MASS_FLOW_RATE["core"].si_coherent(),
)
# TODO: make efficieny kinds more specific
PROPULSIVE_EFFICIENCY = Dimensionless("efficiency_propulsive")
PROPELLER_EFFICIENCY = Dimensionless("efficiency_propeller")
ADVANCE_RATIO = Dimensionless("advance_ratio")
"""Ratio of freestream speed to tip speed for propellers."""

#
# aeroacoustics
#
# TODO: dBA, EPNdB etc.

#
# navigation
#


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
