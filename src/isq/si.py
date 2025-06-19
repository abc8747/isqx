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

from decimal import Decimal
from fractions import Fraction
from typing import Annotated

from .core import PI as _PI
from .core import (
    BaseDimension,
    BaseUnit,
    Dimensionless,
    Exp,
    LazyFactor,
    Logarithmic,
    Mul,
    Prefix,
    Scaled,
    Translated,
)
from .core import E as _E

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
GRAM = Scaled(KG, Fraction(1, 1000), "gram", allow_prefix=True)
"""Gram, a unit of mass."""
DIM_CURRENT = BaseDimension("I")
A = BaseUnit(DIM_CURRENT, "ampere")
"""Ampere, a unit of electric current."""
DIM_TEMPERATURE = BaseDimension("Θ")
K = BaseUnit(DIM_TEMPERATURE, "kelvin")
"""Kelvin, a unit of thermodynamic temperature."""
DIM_AMOUNT = BaseDimension("N")
MOLE = BaseUnit(DIM_AMOUNT, "mole")
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
HZ = Mul((Exp(S, -1),), "hertz")
"""Hertz, a unit of frequency. Shall only be used for periodic phenomena."""
M_PERS = Mul((M, Exp(S, -1)))
M_PERS2 = Mul((M, Exp(S, -2)))
N = Mul((KG, M_PERS2), "newton")
"""Newton, a unit of force."""
PA = Mul((N, Exp(M, -2)), "pascal")
"""Pascal, a unit of pressure and stress."""
J = Mul((N, M), "joule")
"""Joule, a unit of energy, work, and amount of heat."""
W = Mul((J, Exp(S, -1)), "watt")
"""Watt, a unit of power and radiant flux."""
C = Mul((A, S), "coulomb")
"""Coulomb, a unit of electric charge."""
V = Mul((W, Exp(A, -1)), "volt")
"""Volt, a unit of electric potential difference and voltage, also known as
`electric tension` or `tension`."""
F = Mul((C, Exp(V, -1)), "farad")
"""Farad, a unit of capacitance."""
OHM = Mul((V, Exp(A, -1)), "ohm")
"""Ohm, a unit of electric resistance."""
SIEMENS = Mul((A, Exp(V, -1)), "siemens")
"""Siemens, a unit of electric conductance."""
WB = Mul((V, S), "weber")
"""Weber, a unit of magnetic flux."""
T = Mul((WB, Exp(M, -2)), "tesla")
"""Tesla, a unit of magnetic flux density."""
H = Mul((WB, Exp(A, -1)), "henry")
"""Henry, a unit of inductance."""
CELSIUS = Translated(K, Decimal("-273.15"), "celsius")
"""Celsius, a unit of thermodynamic temperature. An absolute, translated scale.
Cannot be composed with other units."""
# NOTE: The symbol `sr` for must be included to distinguish luminous flux (lumen)
# from luminous intensity (candela)
LM = Mul((CD, SR), "lumen")
"""Lumen, a unit of luminous flux."""
LX = Mul((LM, Exp(M, -2)), "lux")
"""Lux, a unit of illuminance."""
BQ = Mul((Exp(S, -1),), "becquerel")
"""Becquerel, a unit of activity referred to a radionuclide. Shall only be used for
stochastic processes in activity referred to a radionuclide.
Not to be confused with "radioactivity"."""
GY = Mul((J, Exp(KG, -1)), "gray")
"""Gray, a unit of absorbed dose and kerma."""
SV = Mul((J, Exp(KG, -1)), "sievert")
"""Sievert, a unit of dose equivalent."""
KAT = Mul((MOLE, Exp(S, -1)), "katal")
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
MIN = Scaled(S, 60, "minute")
HOUR = Scaled(MIN, 60, "hour")
DAY = Scaled(HOUR, 24, "day")
YEAR = Scaled(DAY, Decimal("365.25"), "year")  # approx, on average
DECADE = Scaled(YEAR, 10, "decade")
CENTURY = Scaled(DECADE, 10, "century")

# length
AU = Scaled(M, 149_597_870_700, "astronomical_unit")
"""Astronomical unit, as defined by IAU 2012 Resolution B2."""

# plane and phase angle
DEG = Scaled(RAD, LazyFactor((_PI, (180, -1))), "degree")
"""Degrees (°), a unit of plane angle."""
MIN_ANGLE = Scaled(DEG, Fraction(1, 60), "minute_angle")
"""Minutes (′), a unit of plane angle."""
SEC_ANGLE = Scaled(MIN_ANGLE, Fraction(1, 60), "second_angle")
"""Seconds (″) or arcseconds in astronomy, a unit of plane angle."""
REV = Scaled(RAD, LazyFactor((2, _PI)), "revolution")
"""Revolutions, a unit of plane angle."""

# area
SQ_M = Exp(M, 2)
ARE = Scaled(SQ_M, 100, "are")
HECTARE = Scaled(ARE, 100, "hectare")
"""Hectare, a unit of land area, as adopted by the CIPM in 1879."""

# volume
CU_M = Exp(M, 3)
L = Scaled(CU_M, Fraction(1, 10**3), "liter", allow_prefix=True)
"""Liter, as adopted by the 16th CGPM in 1979."""

# mass
TONNE = Scaled(KG, 1_000, "tonne", allow_prefix=True)
"""Tonne, also known as the [`metric ton`][isq.TON_METRIC] in the U.S."""
U = Scaled(
    KG, Decimal("1.660538782e-27"), "unified_atomic_mass_unit"
)  # NOTE: `amu` is not acceptable [SP811 Table 7]
"""Unified atomic mass unit, also known as the `dalton`."""

# energy
CONST_ELEMENTARY_CHARGE: Annotated[Decimal, C] = Decimal("1.602176634e-19")
EV = Scaled(J, CONST_ELEMENTARY_CHARGE, "electronvolt", allow_prefix=True)
"""Electronvolt, the kinetic energy acquired by an electron in passing through a
potential difference of 1 [volt][isq.V] in vacuum."""

# logarithmic quantities [ISO 80000-3:2006] [SP811 8.7]
# NOTE: not defining the abstract neper, bel and decibel. maybe use factory fn?
DBV = Logarithmic(V, quantity_type="field", log_base=10, name="dBV")
DBUV = Logarithmic(MICRO * V, quantity_type="field", log_base=10, name="dBμV")
NPV = Logarithmic(
    V, quantity_type="field", log_base=_E, name="NpV", allow_prefix=True
)

DBM = Logarithmic(MILLI * W, quantity_type="power", log_base=10, name="dBm")
DBW = Logarithmic(W, quantity_type="power", log_base=10, name="dBW")
NPW = Logarithmic(
    W, quantity_type="power", log_base=_E, name="NpW", allow_prefix=True
)
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
ANGSTROM = Scaled(M, Fraction(1, 10**10), "angstrom")
"""Ångström, a unit of length."""
BARN = Scaled(SQ_M, Fraction(1, 10**28), "barn", allow_prefix=True)
"""Barn, a unit of area for nuclear cross sections."""
BAR = Scaled(PA, 10**5, "bar", allow_prefix=True)
"""Bar, a unit of pressure."""
CONST_DENSITY_HG: Annotated[Decimal, Mul((KG, Exp(CU_M, -1)))] = Decimal(
    "13595.1"
)
"""Density of mercury at 0 °C and 101.325 kPa. For use in [isq.MMHG][]."""
CONST_STANDARD_GRAVITY: Annotated[Decimal, M_PERS2] = Decimal("9.80665")
"""Standard acceleration of gravity, defined by the 3rd CGPM (1901)."""
MMHG = Scaled(
    MILLI * M,
    LazyFactor((CONST_DENSITY_HG, CONST_STANDARD_GRAVITY)),
    "millimeter_of_hg",
)
"""Millimeter of mercury, a unit of pressure."""
CONST_DENSITY_H2O: Annotated[int, Mul((KG, Exp(CU_M, -1)))] = 1000
"""Conventional density of water. For use in [isq.MMH2O][]."""
MMH2O = Scaled(
    MILLI * M,
    LazyFactor((CONST_DENSITY_H2O, CONST_STANDARD_GRAVITY)),
    "millimeter_of_h2o",
)
"""Millimeter of water (conventional), a unit of pressure."""  # [H44 C-59, footnote 12]
CURIE = Scaled(BQ, Decimal("3.7e10"), "curie")
"""Curie, a legacy unit of radioactivity.
The SI unit [becquerel][isq.BQ] is preferred."""
ROENTGEN = Scaled(Mul((C, Exp(KG, -1))), Decimal("2.58e-4"), "roentgen")
"""Roentgen, a legacy unit of exposure to ionizing radiation.
The SI unit [coulomb][isq.C] per [kilogram][isq.KG] is preferred."""
RAD_ABSORBED = Scaled(GY, Fraction(1, 10**2), "rad_absorbed")
"""Rad, a legacy unit of absorbed dose.
The SI unit [gray][isq.GY] is preferred."""
REM = Scaled(SV, Fraction(1, 10**2), "rem")
"""Rem (roentgen equivalent in man), a legacy unit of dose equivalent.
The SI unit [sievert][isq.SV] is preferred."""

# NOTE: not defining CGS(-EMU/ESU) units [SP811 table 10]
# as they are not accepted for use with the SI

# examples of other unacceptable units [SP811 table 11]
FERMI = Scaled(M, Fraction(1, 10**5), "fermi")
"""Fermi, an obsolete name for the femtometer."""
ATM = Scaled(PA, 101325, "atmosphere")
"""Standard atmosphere, a unit of pressure."""  # SP811 B.8
TORR = Scaled(ATM, Fraction(1, 760), "torr")
"""Torr, a unit of pressure."""  # SP811 Table 11
KGF = Scaled(KG, CONST_STANDARD_GRAVITY, "kg_force")
"""Kilogram-force."""  # FIXME: WRONG!
KWH = Mul((KILO * W, HOUR), "kilowatt_hour")
"""Kilowatt-hour, commonly used as a billing unit for electric energy."""
KPH = Mul((KILO * M, Exp(HOUR, -1)), "kph")
"""Kilometers per hour."""
# TODO: octave, phon, sone

# NOTE: not defining ampere-hour, clo, darcy, denier, langley [SP811 B.8]
