/// ICAO definitions:
/// - altitude: measured from the mean sea level (MSL)
/// - height: measured from a specific datum
use crate::quantity::{define_quantity, Quantity};
use crate::unit::{Unit, HZ, M, M2, M3, M_PERS, M_PERS2, RAD, RAD_PERS, S, SR};

define_quantity!(
    /// As measured from mean sea level
    GEOMETRIC_ALTITUDE, M, "h_G"
);
define_quantity!(
    /// As measured by altimeter
    PRESSURE_ALTITUDE, M, "h_p"
);
define_quantity!(
    /// As measured by altimeter
    DENSITY_ALTITUDE, M, "h_d"
);
define_quantity!(
    /// As measured from mean sea level, used in geodesy
    GEOPOTENTIAL_ALTITUDE, M, "Z"
);
define_quantity!(
    /// As measured from a specific datum
    GEODETIC_HEIGHT, M, "h"
);
define_quantity!(RADIUS, M, "r");

define_quantity!(AREA, M2, "A");
define_quantity!(VOLUME, M3, "V");

define_quantity!(PLANE_ANGLE, RAD, "\\theta");
define_quantity!(ANGLE_OF_ATTACK, RAD, "\\alpha");
define_quantity!(ANGLE_OF_SIDESLIP, RAD, "\\beta");
define_quantity!(HEADING, RAD, "\\Psi");

define_quantity!(SOLID_ANGLE, SR, "\\Omega");

define_quantity!(TIME, S, "t");
define_quantity!(DURATION, S, "\\Delta t");
define_quantity!(PERIOD, S, "T");
define_quantity!(FREQUENCY, HZ, "f");
define_quantity!(ANGULAR_FREQUENCY, RAD_PERS, "\\omega"); // NOT Hz
define_quantity!(TIME_CONSTANT, S, "\\tau");

define_quantity!(
    /// Vector perpendicular to the plane of rotation, $v = \omega \times r$
    ANGULAR_VELOCITY, RAD_PERS, "\\omega"
);

define_quantity!(VELOCITY, M_PERS, "v");
define_quantity!(SPEED, M_PERS, "v");
define_quantity!(
    /// Indicated airspeed, as measured by the pitot tube
    IAS, M_PERS, "V_I"
);
define_quantity!(
    /// Calibrated airspeed, as corrected for instrument and position errors
    CAS, M_PERS, "V_c"
);
define_quantity!(
    /// Equivalent airspeed
    EAS, M_PERS, "V_e"
);
define_quantity!(
    /// True airspeed
    TAS, M_PERS, "V"
);
define_quantity!(
    /// Ground speed, inertial reference frame
    GS, M_PERS, "V_g"
);
define_quantity!(
    /// Wind speed, inertial reference frame, $V_w = V - V_g$
    WIND_SPEED, M_PERS, "V_w"
);
define_quantity!(
    /// Speed of sound
    SPEED_OF_SOUND, M_PERS, "a"
);
const MACH: Unit = Unit::new_dimensionless(None);
define_quantity!(
    /// Mach number, $M = \frac{V}{a}$
    MACH_NUMBER, MACH, "M"
);

define_quantity!(ACCELERATION, M_PERS2, "a");
