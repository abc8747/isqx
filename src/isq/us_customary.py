"""
United States customary and British Imperial units.

References:

- [SP811] "NIST Special Publication 811 - 2008 Edition - Guide for the Use of the
    International System of Units (SI)," NIST, Available: https://www.nist.gov/pml/special-publication-811
- [H44] "NIST Handbook 44 - 2024 - Appendix C. General Tables of Units of
    Measurement," NIST, Available: https://www.nist.gov/document/nist-handbook-44-2024-appendix-c-pdf
- [WMA1985] "Weights and Measures Act 1985", legislation.gov.uk.
    Available: https://www.legislation.gov.uk/ukpga/1985/72/contents
"""

from decimal import Decimal
from fractions import Fraction

from .core import PI, Alias, Exp, LazyFactor, Mul, Scaled, Translated
from .si import (
    CONST_DENSITY_H2O,
    CONST_DENSITY_HG,
    CONST_STANDARD_GRAVITY,
    G0,
    GRAM,
    HOUR,
    KG,
    KGF,
    MILLI,
    MIN,
    PA,
    TONNE,
    J,
    K,
    L,
    M,
    S,
    W,
)

#
# temperature [H44 C-23]
#

R = Alias(Scaled(K, Fraction(5, 9)), "rankine")
"""Thermodynamic Temperature (Rankine). Absolute scale."""
FAHRENHEIT = Translated(R, Decimal("-459.67"), "fahrenheit")
"""Thermodynamic Temperature (Fahrenheit). Absolute, translated scale.
Cannot be composed with other units."""

#
# length [H44 C-24]
#

FT = Alias(Scaled(M, Decimal("0.3048")), "foot")
"""International foot."""
FT_US_SURVEY = Alias(Scaled(M, Fraction(1200, 3937)), "foot_us_survey")
"""U.S. survey foot, deprecated since Dec 31, 2022."""  # H44 C-10
IN = Alias(Scaled(FT, Fraction(1, 12)), "inch")
"""International inch."""
YD = Alias(Scaled(FT, 3), "yard")
"""International yard."""  # H44 C-25
MI = Alias(Scaled(FT, 5280), "mile")
"""International mile, also known as statute mile."""  # H44 C-25
NMI = Alias(Scaled(M, 1852), "nautical_mile")
"""International nautical mile."""  # H44 C-25
MIL = Alias(Scaled(IN, Fraction(1, 1000)), "mil")
"""Thousandth of an inch, a unit of thickness (also known as thou)."""
HAND = Alias(Scaled(IN, 4), "hand")
"""Unit of length, for measuring the height of horses."""
POINT = Alias(Scaled(IN, Fraction(1, 72)), "point")
"""Typographical point (desktop publishing)."""  # H44 C-25


# gunter's or surveyors chain units
ROD = Alias(Scaled(FT, Fraction(33, 2)), "rod")
"""Rod, also known as pole or perch."""  # H44 C-5, C-25
FURLONG = Alias(Scaled(ROD, 40), "furlong")
"""Furlong."""
FATHOM = Alias(Scaled(FT, 6), "fathom")
"""Fathom, a unit of length used for water depth."""
CABLE = Alias(Scaled(FATHOM, 120), "cable")
"""Cable length."""
LEAGUE = Alias(Scaled(MI, 3), "league")
"""League."""
LINK = Alias(Scaled(FT, Fraction(66, 100)), "link")
"""Gunter's link."""
CHAIN = Alias(Scaled(LINK, 100), "chain")
"""Gunter's chain."""

#
# area
#

SQ_YD = Exp(YD, 2)
ROOD = Alias(Scaled(SQ_YD, 1210), "rood")
"""Rood, an imperial unit of area."""  # WMA1985 1VI
SQ_FT = Exp(FT, 2)
ACRE = Alias(Scaled(SQ_FT, 43560), "acre")
"""International acre."""  # H44 C-25
ACRE_SURVEY = Alias(Scaled(Exp(FT_US_SURVEY, 2), 43560), "acre_survey")
"""U.S. survey acre."""  # H44 C-14
SQ_BUILDING = Alias(Scaled(SQ_FT, 100), "square_building")
"""Square building, used in the U.S. construction industry."""
SQ_MI = Exp(MI, 2)
SQ_MIL = Exp(MIL, 2)
CIRCULAR_MIL = Alias(Scaled(SQ_MIL, LazyFactor((PI, (4, -1)))), "circular_mil")
"""Circular mil, a unit of area for wire cross-sections."""  # SP811 B.8

#
# volume [H44 C-6]
#

# liquid, US
CU_IN = Exp(IN, 3)
GAL = Alias(Scaled(CU_IN, 231), "gallon")
"""U.S. liquid gallon."""
QUART = Alias(Scaled(GAL, Fraction(1, 4)), "quart")
"""U.S. liquid quart."""
PINT = Alias(Scaled(QUART, Fraction(1, 2)), "pint")
"""U.S. liquid pint."""
CUP = Alias(Scaled(PINT, Fraction(1, 2)), "cup_measuring")
"""U.S. customary cup."""  # H44 C-27
GILL = Alias(Scaled(PINT, Fraction(1, 4)), "gill")
"""U.S. liquid gill."""
FL_OZ = Alias(Scaled(GAL, Fraction(1, 128)), "ounce_fluid")
"""U.S. fluid ounce."""
TABLESPOON = Alias(Scaled(FL_OZ, Fraction(1, 2)), "tablespoon_measuring")
"""U.S. customary tablespoon."""  # H44 C-28
TEASPOON = Alias(Scaled(TABLESPOON, Fraction(1, 3)), "teaspoon_measuring")
"""U.S. customary teaspoon."""  # H44 C-28
# consult federal and state laws for the appropriate barrel definition [H44 C-26]
BBL_FEDERAL_FERMENTED_LIQUOR = Alias(
    Scaled(GAL, 31), "bbl_federal_fermented_liquor"
)
BBL_STATE_LIQUID = Alias(Scaled(GAL, 31 + Fraction(1, 2)), "bbl_state_liquid")
BBL_FEDERAL_CISTERN = Alias(Scaled(GAL, 36), "bbl_federal_cistern")
BBL_PROOF_SPIRIT = Alias(Scaled(GAL, 50), "bbl_proof_spirit")
BBL_OIL = Alias(Scaled(GAL, 42), "bbl_oil", allow_prefix=True)
"""U.S. standard barrel for crude oil and petroleum products."""

# fluid, apothecaries
DRAM_FL = Alias(Scaled(FL_OZ, Fraction(1, 8)), "dram_fluid")
"""U.S. apothecaries' fluid dram."""
MINIM = Alias(Scaled(DRAM_FL, Fraction(1, 60)), "minim")
"""U.S. apothecaries' minim."""

# dry, US
BUSHEL = Alias(Scaled(CU_IN, Decimal("2150.42")), "bushel")
"""U.S. dry bushel."""  # H44 C-26
BUSHEL_HEAPED = Alias(Scaled(CU_IN, Decimal("2747.715")), "bushel_heaped")
"""U.S. heaped bushel."""  # H44 C-26
PECK = Alias(Scaled(BUSHEL, Fraction(1, 4)), "peck")
"""U.S. dry peck."""
QUART_DRY = Alias(Scaled(PECK, Fraction(1, 8)), "quart_dry")
"""U.S. dry quart."""
PINT_DRY = Alias(Scaled(QUART_DRY, Fraction(1, 2)), "pint_dry")
"""U.S. dry pint."""
BBL_DRY = Alias(Scaled(CU_IN, 7056), "bbl_dry")
"""U.S. standard barrel for fruits, vegetables and dry commodities
(excluding cranberries)."""  # H44 C-26
BBL_CRANBERRY = Alias(Scaled(CU_IN, 5826), "bbl_cranberry")
"""U.S. standard barrel for cranberries."""  # H44 C-26

# british imperial [WMA1985 1VI]
GAL_IMP = Alias(Scaled(L, Decimal("4.54609")), "gallon_imperial")
"""British Imperial gallon."""
BUSHEL_IMP = Alias(Scaled(GAL_IMP, 8), "bushel_imperial")
"""British Imperial bushel."""
PECK_IMP = Alias(Scaled(GAL_IMP, 2), "peck_imperial")
"""British Imperial peck."""  # H44 C-8
QUARTER_IMP = Alias(Scaled(BUSHEL_IMP, 8), "quarter_imperial")
"""British Imperial quarter."""  # H44 C-8
QUART_IMP = Alias(Scaled(GAL_IMP, Fraction(1, 4)), "quart_imperial")
"""British Imperial quart."""
PINT_IMP = Alias(Scaled(QUART_IMP, Fraction(1, 2)), "pint_imperial")
"""British Imperial pint."""
FL_OZ_IMP = Alias(Scaled(GAL_IMP, Fraction(1, 160)), "ounce_fluid_imperial")
"""British Imperial fluid ounce."""
DRACHM_FL_IMP = Alias(
    Scaled(FL_OZ_IMP, Fraction(1, 8)), "drachm_fluid_imperial"
)
"""British Imperial fluid drachm."""
SCRUPLE_FL_IMP = Alias(
    Scaled(DRACHM_FL_IMP, Fraction(1, 3)), "scruple_fluid_imperial"
)
"""British Imperial fluid scruple."""  # H44 C-8
MINIM_IMP = Alias(Scaled(SCRUPLE_FL_IMP, Fraction(1, 20)), "minim_imperial")
"""British Imperial minim."""  # H44 C-8

# other
ACRE_FOOT = Alias(Mul((ACRE, FT)), "acre_foot")
"""Volume of water that covers one acre to a depth of one foot."""  # H44 C-19
CORD = Alias(Scaled(Exp(FT, 3), 128), "cord")
"""Cord, a unit of volume for firewood."""  # H44 C-26
WATER_TON = Alias(Scaled(GAL_IMP, 224), "water_ton")
"""Water ton, an English unit of volume,
approximately the volume of a long ton of water."""  # H44 C-28


#
# mass
#

# avoirdupois (common) [H44 C-7]
LB = Alias(Scaled(KG, Decimal("0.45359237")), "pound")
"""Avoirdupois pound mass."""  # H44 C-29
GRAIN = Alias(Scaled(LB, Fraction(1, 7000)), "grain")
"""Grain. Equivalent across Avoirdupois, Troy, and Apothecaries' systems."""  # H44 C-29
OZ = Alias(Scaled(LB, Fraction(1, 16)), "ounce")
"""Avoirdupois ounce."""
DRAM = Alias(Scaled(OZ, Fraction(1, 16)), "dram")
"""Avoirdupois dram."""
CWT = Alias(Scaled(LB, 100), "hundredweight")
"""Short hundredweight (also known as cental)"""
TON = Alias(Scaled(LB, 2000), "ton")
"""Short or net ton."""
TON_METRIC = TONNE  # SP811 Table 6
"""Metric ton, also known in tonne other countries."""

# british imperial [WMA1985 1VI]
STONE = Alias(Scaled(LB, 14), "stone")
"""Stone, a British unit of mass."""
QUARTER = Alias(Scaled(LB, 28), "quarter")
"""Quarter, a British unit of mass."""
CWT_LONG = Alias(Scaled(LB, 112), "hundredweight_long")
"""Long hundredweight."""
TON_LONG = Alias(Scaled(LB, 2240), "ton_long")
"""Long, gross or shipper's ton."""

# troy (for precious metals) [H44 C-7]
LB_T = Alias(Scaled(GRAIN, 5760), "pound_troy")
"""Troy pound mass."""
OZ_T = Alias(Scaled(LB_T, Fraction(1, 12)), "ounce_troy")
"""Troy ounce."""
DWT = Alias(Scaled(OZ_T, Fraction(1, 20)), "pennyweight")
"""Pennyweight."""

# apothecaries' (for medicine) [H44 C-8]
LB_AP = Alias(Scaled(GRAIN, 5760), "pound_apothecaries")
"""Apothecaries' pound mass."""
OZ_AP = Alias(Scaled(LB_AP, Fraction(1, 12)), "ounce_apothecaries")
"""Apothecaries' ounce."""
DRAM_AP = Alias(Scaled(OZ_AP, Fraction(1, 8)), "dram_apothecaries")
"""Apothecaries' dram."""
SCRUPLE = Alias(Scaled(DRAM_AP, Fraction(1, 3)), "scruple")
"""Apothecaries' scruple."""
# assaying and gemstones
CARAT = Alias(Scaled(MILLI * GRAM, 200), "carat")
"""Metric carat, for gemstones."""  # H44 C-29
POINT_MASS = Alias(Scaled(CARAT, Fraction(1, 100)), "point_mass")
"""Point, for gemstones."""  # H44 C-30
ASSAY_TON = Alias(Scaled(GRAM, Decimal("29.167")), "assay_ton")
"""Assay ton. The mass in milligrams of precious metal from one assay ton of ore
gives the troy ounces per short ton."""  # H44 C-29
QUINTAL = Alias(Scaled(KG, 100), "quintal")
"""Quintal, a historical unit of mass, now usually 100 kg."""  # WMA1985 1VI

#
# misc / engineering
#

# linear velocity
KNOT = Alias(Mul((NMI, Exp(HOUR, -1))), "knot")
"""Knot, one nautical mile per hour."""
MPH = Alias(Mul((MI, Exp(HOUR, -1))), "mph")
"""Miles per hour."""

# acceleration
FT_PERS2 = Mul((FT, Exp(S, -2)))
"""Feet per second squared."""
# force
LBF = Alias(Mul((LB, G0)), "pound_force")
"""Pound-force."""
POUNDAL = Alias(Mul((LB, FT, Exp(S, -2))), "poundal")
"""Poundal, the force required to accelerate 1 lb by 1 ft/s²."""
KIP = Alias(Scaled(LBF, 1000), "kip")

# pressure [H44 C-59]
PSI = Alias(Mul((LBF, Exp(IN, -2))), "psi")
"""Pound-force per square inch, a unit of pressure."""
KSI = Alias(Scaled(PSI, 1000), "ksi")
"""Kilo-pound-force per square inch, a unit of pressure."""
PSF = Alias(Mul((LBF, Exp(SQ_FT, -1))), "psf")
"""Pound-force per square foot, a unit of pressure."""
INHG = Alias(
    Scaled(
        IN,
        LazyFactor((CONST_DENSITY_HG, CONST_STANDARD_GRAVITY)),
    ),
    "inch_of_hg",
)
"""Inch of mercury, a unit of pressure."""  # SP811 B.8
INH2O = Alias(
    Scaled(
        IN,
        LazyFactor((CONST_DENSITY_H2O, CONST_STANDARD_GRAVITY)),
    ),
    "inch_of_h2o",
)
"""Inch of water (conventional), a unit of pressure."""
INH2O_4C = Alias(Scaled(PA, Decimal("249.082")), "inch_of_water_4c")  # approx
"""Inch of water at 4 °C (temperature of maximum water density)."""
INH2O_60F = Alias(Scaled(PA, Decimal("248.84")), "inch_of_water_60f")  # approx
"""Inch of water at 60 °F."""

SLUG = Alias(Mul((LBF, Exp(FT_PERS2, -1))), "slug")
"""A unit of mass that accelerates by 1 ft/s² when a force of 1 lbf is exerted on it."""

# energy
FT_LBF = Alias(Mul((FT, LBF)), "foot_pound")
"""Foot-pound, a unit of energy or work."""
# [SP811 B.8 (footnote 10), H44 C-59]
CAL_IT = Alias(Scaled(J, Decimal("4.1868")), "calorie_it")
"""Calorie (International Table)."""
CAL_TH = Alias(Scaled(J, Decimal("4.184")), "calorie_th")
"""Calorie (thermochemical)."""
CAL_MEAN = Alias(Scaled(J, Decimal("4.19002")), "calorie_mean")  # approx
"""Calorie (mean). The heat required to raise 1 g of water from 0 °C to 100 °C,
divided by 100."""
CAL_15C = Alias(Scaled(J, Decimal("4.18580")), "calorie_15c")  # approx
"""Calorie (at 15 °C). The heat required to raise 1 g of water from 14.5 °C to
15.5 °C."""
CAL_20C = Alias(Scaled(J, Decimal("4.18190")), "calorie_20c")  # approx
"""Calorie (at 20 °C). The heat required to raise 1 g of water from 19.5 °C to
20.5 °C."""
# [SP811 B.8 (footnote 9), H44 C-57]
BTU = BTU_IT = Alias(Scaled(J, Decimal("1055.05585262")), "btu_it")
"""British thermal unit (International Table). The most widely used definition."""
BTU_TH = Alias(Scaled(J, Decimal("1054.350")), "btu_th")  # approx
"""British thermal unit (thermochemical)."""
BTU_MEAN = Alias(Scaled(J, Decimal("1055.87")), "btu_mean")  # approx
"""British thermal unit (mean, from 32 °F to 212 °F, divided by 180)."""
BTU_39F = Alias(Scaled(J, Decimal("1059.67")), "btu_39f")  # approx
"""British thermal unit (at 39 °F)."""
BTU_59F = Alias(Scaled(J, Decimal("1054.80")), "btu_59f")  # approx
"""British thermal unit (at 59 °F). Used for American natural gas pricing."""
BTU_60F = Alias(Scaled(J, Decimal("1054.68")), "btu_60f")  # approx
"""British thermal unit (at 60 °F)."""
QUAD = Alias(Scaled(BTU_IT, 10**15), "quad")
"""Quad (International Table). Used by U.S. Department of Energy."""  # H44 B.8 footnote 9

# power [SP811 B.8]
HP = Alias(Scaled(Mul((FT, LBF, Exp(MIN, -1))), 33_000), "horsepower")
"""Mechanical horsepower (imperial)."""  # https://en.wikipedia.org/wiki/Horsepower#Imperial_horsepower
HP_METRIC = Alias(Scaled(Mul((KGF, M, Exp(S, -1))), 75), "horsepower_metric")
"""Metric horsepower."""  # https://en.wikipedia.org/wiki/Horsepower#Metric_horsepower_(PS,_KM,_cv,_hk,_pk,_k,_ks,_ch)
HP_BOILER = Alias(Scaled(W, Decimal("9809.50")), "horsepower_boiler")  # approx
"""Boiler horsepower."""
HP_ELECTRIC = Alias(Scaled(W, 746), "horsepower_electric")
"""Electrical horsepower."""
HP_UK = Alias(Scaled(W, Decimal("745.70")), "horsepower_uk")  # approx
"""UK horsepower."""
HP_WATER = Alias(Scaled(W, Decimal("746.043")), "horsepower_water")  # approx
"""Water horsepower."""

#
# misc
#
MPG = Alias(Mul((MI, Exp(GAL, -1))), "miles_per_gallon")
"""Miles per gallon, a unit of fuel economy."""  # SP811 B.5
# NOTE: not defining R-value (°F·ft²·h/Btu), U-factor (Btu/(h·ft²·°F)), K-value (Btu·in/(h·ft²·°F))
