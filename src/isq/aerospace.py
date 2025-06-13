"""
Units defined by the International Civil Aviation Organization (ICAO)

[4] "Annex 5 - Units of Measurement to be Used in the Air and Ground Services,"
    ICAO. [Online]. Available: https://store.icao.int/en/annex-5-units-of-measurement-to-be-used-in-the-air-and-ground-services
"""

from .core import Disambiguated
from .si import M_PERS, M

M_ALT_GEOP = Disambiguated(M, ("altitude", "geopotential"))
M_ALT_GEOM = Disambiguated(M, ("altitude", "geometric"))

M_PERS_TAS = Disambiguated(M_PERS, ("airspeed", "true"))
M_PERS_CAS = Disambiguated(M_PERS, ("airspeed", "calibrated"))
M_PERS_EAS = Disambiguated(M_PERS, ("airspeed", "equivalent"))
M_PERS_GS = Disambiguated(M_PERS, ("airspeed", "ground"))
M_PERS_WIND = Disambiguated(M_PERS, ("wind"))
