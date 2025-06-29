"""
Units as defined by the International System of Units (SI)

References:

- [SI] The International System of Units (SI): Text in English (updated in 2024),
    9th edition 2019, V3.01 August 2024. Sèvres Cedex BIPM 2024, 2024.
    Available: https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf
- [IUPAP1] C. C2, "C2: Commission on Symbols, Units, Nomenclature, Atomic Masses and
    Fundamental Constants - IUPAP: The International Union of Pure and Applied
    Physics," Mar. 04, 2021. Available: https://archive2.iupap.org/wp-content/uploads/2014/05/A4.pdf
- [SP811] "NIST Special Publication 811 - 2008 Edition - Guide for the Use of the
    International System of Units (SI)," NIST, Available: https://www.nist.gov/pml/special-publication-811
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from typing import TYPE_CHECKING, Annotated, Literal

from .core import PI as _PI
from .core import (
    BaseDimension,
    BaseUnit,
    Dimensionless,
    LazyProduct,
    Logarithmic,
    Prefix,
    Translated,
)
from .core import E as _E

if TYPE_CHECKING:
    from .core import Aliased, Exp, Mul, Scaled, Tagged

#
# base units [SI page 130 & section 2.3.3] [IUPAP1 page 20 & table 4]
#

DIM_TIME = BaseDimension("T")
S = BaseUnit(DIM_TIME, "second")
"""Second, a unit of time."""
DIM_LENGTH = BaseDimension("L")
M = BaseUnit(DIM_LENGTH, "meter")
"""Meter, a unit of length."""
DIM_MASS = BaseDimension("M")
KG = BaseUnit(DIM_MASS, "kilogram")
"""Kilogram, a unit of mass."""
GRAM = (Fraction(1, 1000) * KG).alias("gram", allow_prefix=True)
"""Gram, a unit of mass."""
DIM_CURRENT = BaseDimension("I")
A = BaseUnit(DIM_CURRENT, "ampere")
"""Ampere, a unit of electric current."""
DIM_TEMPERATURE = BaseDimension("Θ")
K = BaseUnit(DIM_TEMPERATURE, "kelvin")
"""Kelvin, a unit of thermodynamic temperature."""
DIM_AMOUNT = BaseDimension("N")
MOL = BaseUnit(DIM_AMOUNT, "mole")
"""Mole, a unit of amount of substance."""
DIM_LUMINOUS_INTENSITY = BaseDimension("J")
CD = BaseUnit(DIM_LUMINOUS_INTENSITY, "candela")
"""Candela, a unit of luminous intensity."""

#
# derived units [SI, page 137, section 2.3.4] [IUPAP1, page 22, table 5]
# important and widely used, but which do not properly fall within the SI.
#

RAD = Dimensionless("radian")
"""Radian, a unit of plane angle. Not to be confused with m m⁻¹."""
SR = Dimensionless("steradian")
"""Steradian, a unit of solid angle. Not to be confused with m² m⁻²."""
HZ = (S**-1).alias("hertz", allow_prefix=True)
"""Hertz, a unit of frequency. Shall only be used for periodic phenomena."""
M_PERS = M * S**-1
M_PERS2 = M * S**-2
N = (KG * M_PERS2).alias("newton", allow_prefix=True)
"""Newton, a unit of force."""
PA = (N * M**-2).alias("pascal", allow_prefix=True)
"""Pascal, a unit of pressure and stress."""
J = (N * M).alias("joule", allow_prefix=True)
"""Joule, a unit of energy, work, and amount of heat."""
W = (J * S**-1).alias("watt", allow_prefix=True)
"""Watt, a unit of power and radiant flux."""
C = (A * S).alias("coulomb", allow_prefix=True)
"""Coulomb, a unit of electric charge."""
V = (W * A**-1).alias("volt", allow_prefix=True)
"""Volt, a unit of electric potential difference and voltage, also known as
`electric tension` or `tension`."""
F = (C * V**-1).alias("farad", allow_prefix=True)
"""Farad, a unit of capacitance."""
OHM = (V * A**-1).alias("ohm", allow_prefix=True)
"""Ohm, a unit of electric resistance."""
SIEMENS = (A * V**-1).alias("siemens", allow_prefix=True)
"""Siemens, a unit of electric conductance."""
WB = (V * S).alias("weber", allow_prefix=True)
"""Weber, a unit of magnetic flux."""
T = (WB * M**-2).alias("tesla", allow_prefix=True)
"""Tesla, a unit of magnetic flux density."""
H = (WB * A**-1).alias("henry", allow_prefix=True)
"""Henry, a unit of inductance."""
CELSIUS = Translated(K, Decimal("-273.15"), "celsius")
"""Celsius, a unit of thermodynamic temperature. An absolute, translated scale.
Cannot be composed with other units."""
# NOTE: The symbol `sr` for must be included to distinguish luminous flux (lumen)
# from luminous intensity (candela)
LM = (CD * SR).alias("lumen", allow_prefix=True)
"""Lumen, a unit of luminous flux."""
LX = (LM * M**-2).alias("lux", allow_prefix=True)
"""Lux, a unit of illuminance."""
BQ = (S**-1).alias("becquerel", allow_prefix=True)
"""Becquerel, a unit of activity referred to a radionuclide. Shall only be used for
stochastic processes in activity referred to a radionuclide.
Not to be confused with "radioactivity"."""
GY = (J * KG**-1).alias("gray", allow_prefix=True)
"""Gray, a unit of absorbed dose and kerma."""
SV = (J * KG**-1).alias("sievert", allow_prefix=True)
"""Sievert, a unit of dose equivalent."""
KAT = (MOL * S**-1).alias("katal", allow_prefix=True)
"""Katal, a unit of catalytic activity."""

#
# si prefixes [SI page 143] [IUPAP1 page 4 & table 1]
#

YOTTA = Prefix(10**24, "yotta")
ZETTA = Prefix(10**21, "zetta")
EXA = Prefix(10**18, "exa")
PETA = Prefix(10**15, "peta")
TERA = Prefix(10**12, "tera")
GIGA = Prefix(10**9, "giga")
MEGA = Prefix(10**6, "mega")
KILO = Prefix(10**3, "kilo")
HECTO = Prefix(10**2, "hecto")
DECA = Prefix(10**1, "deca")
DECI = Prefix(Fraction(1, 10**1), "deci")
CENTI = Prefix(Fraction(1, 10**2), "centi")
MILLI = Prefix(Fraction(1, 10**3), "milli")
MICRO = Prefix(Fraction(1, 10**6), "micro")
NANO = Prefix(Fraction(1, 10**9), "nano")
PICO = Prefix(Fraction(1, 10**12), "pico")
FEMTO = Prefix(Fraction(1, 10**15), "femto")
ATTO = Prefix(Fraction(1, 10**18), "atto")
ZEPTO = Prefix(Fraction(1, 10**21), "zepto")
YOCTO = Prefix(Fraction(1, 10**24), "yocto")

KIBI = Prefix(1024**1, "kibi")
MEBI = Prefix(1024**2, "mebi")
GIBI = Prefix(1024**3, "gibi")
TEBI = Prefix(1024**4, "tebi")
PEBI = Prefix(1024**5, "pebi")
EXBI = Prefix(1024**6, "exbi")
ZEBI = Prefix(1024**7, "zebi")
YOBI = Prefix(1024**8, "yobi")


#
# non-si units accepted for use with the si [SI table 8] [SP811 table 6 & 7]
#

# time
MIN = (60 * S).alias("minute")
HOUR = (60 * MIN).alias("hour")
DAY = (24 * HOUR).alias("day")
YEAR = (Decimal("365.25") * DAY).alias("year")
ANNUS = (Decimal("365.25") * DAY).alias("annus", allow_prefix=True)

# length
AU = (149_597_870_700 * M).alias("astronomical_unit")
"""Astronomical unit, as defined by IAU 2012 Resolution B2."""
PC = (LazyProduct((648_000, (_PI, -1))) * AU).alias("parsec")
"""Parsec"""
CONST_SPEED_OF_LIGHT: Annotated[int, M_PERS] = 299_792_458
"""Speed of light in vacuum, defined by the 17th CGPM in 1983."""
LY = (CONST_SPEED_OF_LIGHT * YEAR).alias("light_year", allow_prefix=True)
"""Light-year"""

# plane and phase angle
DEG = (LazyProduct((_PI, (180, -1))) * RAD).alias("degree")
"""Degrees (°), a unit of plane angle."""
MIN_ANGLE = (Fraction(1, 60) * DEG).alias("minute_angle")
"""Minutes (′), a unit of plane angle."""
SEC_ANGLE = (Fraction(1, 60) * MIN_ANGLE).alias("second_angle")
"""Seconds (″) or arcseconds in astronomy, a unit of plane angle."""
REV = (LazyProduct((2, _PI)) * RAD).alias("revolution")
"""Revolutions, a unit of plane angle."""

# area
SQ_M = M**2
ARE = (100 * SQ_M).alias("are")
HECTARE = (100 * ARE).alias("hectare")
"""Hectare, a unit of land area, as adopted by the CIPM in 1879."""

# volume
CU_M = M**3
L = (Fraction(1, 10**3) * CU_M).alias("liter", allow_prefix=True)
"""Liter, as adopted by the 16th CGPM in 1979."""

# mass
TONNE = (1_000 * KG).alias("tonne", allow_prefix=True)
"""Tonne, also known as the [`metric ton`][isq.us_customary.TON_METRIC] in the
U.S."""
U = (Decimal("1.660538782e-27") * KG).alias("unified_atomic_mass_unit")
# NOTE: `amu` is not acceptable [SP811 Table 7]
"""Unified atomic mass unit, also known as the `dalton`."""

# energy
CONST_ELEMENTARY_CHARGE: Annotated[Decimal, C] = Decimal("1.602176634e-19")
EV = (CONST_ELEMENTARY_CHARGE * J).alias("electronvolt", allow_prefix=True)
"""Electronvolt, the kinetic energy acquired by an electron in passing through a
potential difference of 1 [volt][isq.V] in vacuum."""


# logarithmic quantities [ISO 80000-3:2006] [SP811 8.7]
# TODO: bel
def decibel(
    reference: BaseUnit | Exp | Mul | Scaled | Aliased | Tagged,
    quantity_type: Literal["field", "power"],
    name: str,
) -> Logarithmic:
    if not name.startswith("dB"):
        raise ValueError(f"{name=} should start with `dB`")
    return Logarithmic(
        reference, quantity_type=quantity_type, log_base=10, name=name
    )


def neper(
    reference: BaseUnit | Exp | Mul | Scaled | Aliased | Tagged,
    quantity_type: Literal["field", "power"],
    name: str,
) -> Logarithmic:
    if not name.startswith("Np"):
        raise ValueError(f"{name=} should start with `Np`")
    return Logarithmic(
        reference,
        quantity_type=quantity_type,
        log_base=_E,
        name=name,
        allow_prefix=True,
    )


# TODO: a-weighting
DBV = decibel(V, "field", "dBV")
DBUV = decibel(MICRO * V, "field", "dBμV")
DBZ = decibel((MILLI * M) ** 6 * M**-3, "field", "dBZ")
NPV = neper(V, quantity_type="field", name="NpV")

DBM = decibel(MILLI * W, "power", "dBm")
DBW = decibel(W, "power", "dBW")
NPW = neper(W, quantity_type="power", name="NpW")
# information theory [ISO 80000-1, Annex C]
# TODO: bit, baud, erlang
_NUMBER = BaseUnit(BaseDimension("_number"), name="number")
SHANNON = Logarithmic(
    reference=_NUMBER, quantity_type="field", log_base=2, name="shannon"
)
"""Logarithmic unit of information (base 2)."""
NAT = Logarithmic(
    reference=_NUMBER, quantity_type="field", log_base=_E, name="nat"
)
"""Natural unit of information (base e)."""
HARTLEY = Logarithmic(
    reference=_NUMBER, quantity_type="field", log_base=10, name="hartley"
)
"""Logarithmic unit of information (base 10), also known as a `ban` or `dit`."""

# [SP811 table 9]
ANGSTROM = (Fraction(1, 10**10) * M).alias("angstrom")
"""Ångström, a unit of length."""
BARN = (Fraction(1, 10**28) * SQ_M).alias("barn", allow_prefix=True)
"""Barn, a unit of area for nuclear cross sections."""
BAR = (10**5 * PA).alias("bar", allow_prefix=True)
"""Bar, a unit of pressure."""
CONST_DENSITY_HG: Annotated[Decimal, KG * CU_M**-1] = Decimal("13595.1")
"""Density of mercury at 0 °C and 101.325 kPa. For use in [isq.MMHG][]."""
CONST_STANDARD_GRAVITY: Annotated[Decimal, M_PERS2] = Decimal("9.80665")
"""Standard acceleration of gravity, defined by the 3rd CGPM (1901)."""
G0 = CONST_STANDARD_GRAVITY * M_PERS2  # for KGF and LBF
MMHG = (
    LazyProduct((CONST_DENSITY_HG, CONST_STANDARD_GRAVITY)) * (MILLI * M)
).alias("millimeter_of_hg")
"""Millimeter of mercury, a unit of pressure."""
CONST_DENSITY_H2O: Annotated[int, KG * CU_M**-1] = 1000
"""Conventional density of water. For use in [isq.MMH2O][]."""
MMH2O = (
    LazyProduct((CONST_DENSITY_H2O, CONST_STANDARD_GRAVITY)) * (MILLI * M)
).alias("millimeter_of_h2o")
"""Millimeter of water (conventional), a unit of pressure."""  # [H44 C-59, footnote 12]
CURIE = (Decimal("3.7e10") * BQ).alias("curie")
"""Curie, a legacy unit of radioactivity.
The SI unit [becquerel][isq.BQ] is preferred."""
ROENTGEN = (Decimal("2.58e-4") * (C * KG**-1)).alias("roentgen")
"""Roentgen, a legacy unit of exposure to ionizing radiation.
The SI unit [coulomb][isq.C] per [kilogram][isq.KG] is preferred."""
RD_ABSORBED = (Fraction(1, 100) * GY).alias("rd")
"""Rad, a legacy unit of absorbed dose. The SI unit [gray][isq.GY] is preferred.
Not to be confused with the [radian][isq.RAD]."""
REM = (Fraction(1, 100) * SV).alias("rem")
"""Rem (roentgen equivalent in man), a legacy unit of dose equivalent.
The SI unit [sievert][isq.SV] is preferred."""

# NOTE: not defining CGS(-EMU/ESU) units [SP811 table 10]
# as they are not accepted for use with the SI

# examples of other unacceptable units [SP811 table 11]
FERMI = (Fraction(1, 10**5) * M).alias("fermi")
"""Fermi, an obsolete name for the femtometer."""
ATM = (101325 * PA).alias("atmosphere")
"""Standard atmosphere, a unit of pressure."""  # SP811 B.8
TORR = (Fraction(1, 760) * ATM).alias("torr")
"""Torr, a unit of pressure."""  # SP811 Table 11
KGF = (KG * G0).alias("kg_force")
"""Kilogram-force."""
KWH = ((KILO * W) * HOUR).alias("kilowatt_hour")
"""Kilowatt-hour, commonly used as a billing unit for electric energy."""
KPH = ((KILO * M) * HOUR**-1).alias("kph")
"""Kilometers per hour."""
# TODO: octave, phon, sone

# NOTE: not defining ampere-hour, clo, darcy, denier, langley [SP811 B.8]
