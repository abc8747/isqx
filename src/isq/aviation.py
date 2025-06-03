"""
Units defined by the International Civil Aviation Organization (ICAO)

[4] "Annex 5 - Units of Measurement to be Used in the Air and Ground Services,"
    ICAO. [Online]. Available: https://store.icao.int/en/annex-5-units-of-measurement-to-be-used-in-the-air-and-ground-services
"""

from .core import Disambiguation
from .si import DIM_LENGTH

GEOPOTENTIAL_ALTITUDE = Disambiguation(DIM_LENGTH)
