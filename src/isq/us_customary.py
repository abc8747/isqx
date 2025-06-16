"""
United States customary units.

[3] "NIST Handbook 44 - 2024 - Appendix C. General Tables of Units of
    Measurement," NIST, Available: https://www.nist.gov/document/nist-handbook-44-2024-appendix-c-pdf
"""

from decimal import Decimal
from fractions import Fraction

from .core import Exp, Mul, Scaled, Translated
from .si import G0, KG, K, M, S

FT = Scaled(M, Decimal("0.3048"), "ft")
IN = Scaled(FT, Fraction(1, 12), "in")

LB = Scaled(KG, Decimal("0.45359237"), "lb")
LBF = Mul((LB, G0), "lbf")

PSI = Mul((LBF, Exp(IN, -2)), "psi")

FT_PERS2 = Mul((FT, Exp(S, -2)))
SLUG = Mul((LBF, Exp(FT_PERS2, -1)), "slug")
"""Mass that is accelerated by 1 [ft s⁻²][isq.FT_PERS2] under 1 [lbf][isq.LBF] of force."""

R = Scaled(K, Fraction(5, 9), "rankine")
"""Thermodynamic Temperature (Rankine). Absolute scale."""
FARENHEIT = Translated(R, Decimal("-459.67"), "farenheit")
"""Thermodynamic Temperature (Farenheit). Absolute, translated scale."""
