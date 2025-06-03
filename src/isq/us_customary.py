"""
United States customary units.

[3] "NIST Handbook 44 - 2024 - Appendix C. General Tables of Units of
    Measurement," NIST, Available: https://www.nist.gov/document/nist-handbook-44-2024-appendix-c-pdf
"""

from decimal import Decimal

from .core import Scaled
from .si import M

FT = Scaled(M, Decimal("0.3048"), "feet")
