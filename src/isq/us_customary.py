"""
United States customary units.

[3] "NIST Handbook 44 - 2024 - Appendix C. General Tables of Units of
    Measurement," NIST, Available: https://www.nist.gov/document/nist-handbook-44-2024-appendix-c-pdf
"""

from decimal import Decimal
from fractions import Fraction

from .core import Exp, Mul, Scaled, Translated
from .si import G0, HOUR, KG, K, M, S

FT = Scaled(M, Decimal("0.3048"), "foot")
NMI = Scaled(M, 1852, "nautical_mile")
IN = Scaled(FT, Fraction(1, 12), "inch")
YD = Scaled(FT, 3, "yard")
MI = Scaled(FT, 5280, "mile")

KNOT = Mul((NMI, Exp(HOUR, -1)), "knot")
MPH = Mul((MI, Exp(HOUR, -1)), "mph")

LB = Scaled(KG, Decimal("0.45359237"), "pound_mass")
LBF = Mul((LB, G0), "pound_force")

PSI = Mul((LBF, Exp(IN, -2)), "psi")

FT_PERS2 = Mul((FT, Exp(S, -2)))
SLUG = Mul((LBF, Exp(FT_PERS2, -1)), "slug")
"""Mass that is accelerated by 1 [ft s⁻²][isq.FT_PERS2] under 1 [lbf][isq.LBF] of force."""

R = Scaled(K, Fraction(5, 9), "rankine")
"""Thermodynamic Temperature (Rankine). Absolute scale."""
FARENHEIT = Translated(R, Decimal("-459.67"), "farenheit")
"""Thermodynamic Temperature (Farenheit). Absolute, translated scale."""
