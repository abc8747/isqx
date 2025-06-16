"""
Units as defined by the International System of Units (SI)

[1] The International System of Units (SI): Text in English (updated in 2024),
    9th edition 2019, V3.01 August 2024. Sèvres Cedex BIPM 2024, 2024.
    Available: https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf

[2] C. C2, "C2: Commission on Symbols, Units, Nomenclature, Atomic Masses and
    Fundamental Constants - IUPAP: The International Union of Pure and Applied
    Physics," Mar. 04, 2021. Available: https://archive2.iupap.org/wp-content/uploads/2014/05/A4.pdf
"""

from decimal import Decimal
from fractions import Fraction

from .core import (
    BaseDimension,
    BaseUnit,
    Dimensionless,
    Exp,
    Mul,
    Prefix,
    Scaled,
    Translated,
)

#
# base units [1, page 130, section 2.3.3] [2, page 20, table 4]
#

DIM_TIME = BaseDimension("T")
S = BaseUnit(DIM_TIME, "second")
"""Time (seconds)"""
DIM_LENGTH = BaseDimension("L")
M = BaseUnit(DIM_LENGTH, "meter")
"""Length (meters)"""
DIM_MASS = BaseDimension("M")
KG = BaseUnit(DIM_MASS, "kilogram")
"""Mass (kilograms)"""
GRAM = Scaled(KG, Fraction(1, 1000), "gram", allow_prefix=True)
"""Mass (grams)"""
DIM_CURRENT = BaseDimension("I")
A = BaseUnit(DIM_CURRENT, "ampere")
"""Electric Current (amperes)"""
DIM_TEMPERATURE = BaseDimension("Θ")
K = BaseUnit(DIM_TEMPERATURE, "kelvin")
"""Thermodynamic Temperature (kelvins)"""
DIM_AMOUNT = BaseDimension("N")
MOLE = BaseUnit(DIM_AMOUNT, "mole")
"""Amount of Substance (moles)"""
DIM_LUMINOUS_INTENSITY = BaseDimension("J")
CD = BaseUnit(DIM_LUMINOUS_INTENSITY, "candela")
"""Luminous Intensity (candelas)"""

#
# derived units [1, page 137, section 2.3.4] [2, page 22, table 5]
# important and widely used, but which do not properly fall within the SI.
#

RAD = Dimensionless("radian")
"""Plane angle (radians). Not to be confused with m m⁻¹."""
SR = Dimensionless("steradian")
"""Solid angle (steradians). Not to be confused with m² m⁻²."""
HZ = Mul((Exp(S, -1),), "hertz")
"""Frequency (hertz). Shall only be used for periodic phenomena."""
M_PERS = Mul((M, Exp(S, -1)))
M_PERS2 = Mul((M, Exp(S, -2)))
N = Mul((KG, M_PERS2), "newton")  # F = ma
"""Force (newtons)"""
PA = Mul((N, Exp(M, -2)), "pascal")
"""Pressure, stress (pascals)"""
J = Mul((N, M), "joule")
"""Energy, work, amount of heat (joules)"""
W = Mul((J, Exp(S, -1)), "watt")
"""Power, radiant flux (watts)"""
C = Mul((A, S), "coulomb")
"""Electric charge (coulombs)"""
V = Mul((W, Exp(A, -1)), "volt")
"""Electric potential difference, voltage (volts).
Also named "electric tension" or "tension"."""
F = Mul((C, Exp(V, -1)), "farad")
"""Capacitance (farads)"""
OHM = Mul((V, Exp(A, -1)), "ohm")
"""Electric resistance (ohms)"""
SIEMENS = Mul((A, Exp(V, -1)), "siemens")
"""Electric conductance (siemens)"""
WB = Mul((V, S), "weber")
"""Magnetic flux (webers)"""
T = Mul((WB, Exp(M, -2)), "tesla")
"""Magnetic flux density (teslas)"""
H = Mul((WB, Exp(A, -1)), "henry")
"""Inductance (henries)"""
CELSIUS = Translated(K, Decimal("-273.15"), "celsius")
"""Thermodynamic temperature (Celsius). Absolute, translated scale."""
# NOTE: The symbol `sr` for must be included to distinguish luminous flux (lumen)
# from luminous intensity (candela)
LM = Mul((CD, SR), "lumen")
"""Luminous flux (lumens)"""
LX = Mul((LM, Exp(M, -2)), "lux")
"""Illuminance (lux)"""
BQ = Mul((Exp(S, -1),), "becquerel")
"""Activity referred to a radionuclide (becquerels). Shall only be used for
stochastic processes in activity referred to a radionuclide.
Not to be confused with "radioactivity"."""
GY = Mul((J, Exp(KG, -1)), "gray")
"""Absorbed dose, kerma (grays)"""
SV = Mul((J, Exp(KG, -1)), "sievert")
"""Dose equivalent (sieverts)"""
KAT = Mul((MOLE, Exp(S, -1)), "katal")
"""Catalytic activity (katal)"""

#
# si prefixes [1, page 143] [2, page 4, table 1]
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
# non-si units accepted for use in the si [1: page 145]
#

MIN = Scaled(S, 60, "minute")
HOUR = Scaled(MIN, 60, "hour")
DAY = Scaled(HOUR, 24, "day")
YEAR = Scaled(DAY, Decimal("365.25"), "year")  # on average
DECADE = Scaled(YEAR, 10, "decade")
CENTURY = Scaled(DECADE, 10, "century")

L = Scaled(Exp(M, 3), Fraction(1, 10**3), "liter", allow_prefix=True)
TONNE = Scaled(KG, 1000, "tonne", allow_prefix=True)

G0 = Scaled(M_PERS2, Decimal("9.80665"), "standard_gravity")  # page 159
