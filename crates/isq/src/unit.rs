/// Each physical quantity has only one coherent SI unit, though it can be expressed in other forms.
/// However, several different quantities may share the same SI unit.
use crate::exponent::Exponent;

/// A unit raised to the power of a an integer or fraction.
#[derive(Debug, Clone)]
pub struct Pow<Q> {
    pub base: Q,
    pub exponent: Exponent,
}

/// A dimension, represented as a tree.
///
/// We want to be able to represent *derived* units.
/// For example, specific heat capacity = `J kg⁻¹ K⁻¹`, and a call to `.simplify()`
/// would use `J = kg m² s⁻²` to simplify it down to `m² K⁻¹ s⁻²`.
#[derive(Debug, Clone)]
pub enum Unit<'base, 'group, 'name> {
    /// A base unit, "root node"
    Base {
        /// Symbol of the unit, e.g. `kg`, `m`
        symbol: &'name str,
    },
    /// A derived unit, defined as products of powers of the base units
    Derived {
        groups: &'group [Pow<&'base Unit<'base, 'group, 'name>>],
    },
    Dimensionless,
    /// A named unit, used to disambiguate between units of the equivalent dimension.
    ///
    /// For example, Reynolds number (`Re`) and boundary layer shape factor (`H`) are both
    /// dimensionless but represent distinct quantities.
    SpecialSymbol {
        inner: &'base Unit<'base, 'group, 'name>,
        symbol: Option<&'name str>,
    },
}

impl<'base, 'group, 'name> Unit<'base, 'group, 'name> {
    pub const fn new_base(symbol: &'name str) -> Self {
        Self::Base { symbol }
    }

    pub const fn from_groups(groups: &'group [Pow<&'base Unit<'base, 'group, 'name>>]) -> Self {
        if groups.is_empty() {
            panic!("a physical dimension cannot have no base dimensions")
        }
        Self::Derived { groups }
    }

    pub const fn new_dimensionless(symbol: Option<&'name str>) -> Self {
        // "It is especially important to have a clear description of any quantity with the unit one
        // (see section 5.4.7) that is expressed as a ratio of quantities of the same kind (for
        // example length ratios or amount fractions) or as a number of entities (for example number
        // of photons or decays)."
        Self::SpecialSymbol {
            inner: &Self::Dimensionless,
            symbol,
        }
    }

    pub const fn with_special_symbol(&'base self, symbol: &'name str) -> Self {
        Self::SpecialSymbol {
            inner: &self,
            symbol: Some(symbol),
        }
    }

    pub const fn to_str(&self) -> Option<&'name str> {
        match self {
            &Self::Base { symbol: name } => Some(name),
            &Self::Derived { groups: _ } => todo!(),
            &Self::Dimensionless => None,
            &Self::SpecialSymbol { inner, symbol: _ } => inner.to_str(),
        }
    }

    pub fn simplify(self, with_name: &str) -> Self {
        match self {
            Self::Base { symbol: _ } | Self::Dimensionless => self,
            Self::Derived { groups: _ } => {
                todo!()
            }
            Self::SpecialSymbol { inner, symbol: _ } => {
                todo!("{:?} {:?}", inner, with_name)
            }
        }
    }
}

impl ::core::fmt::Display for Unit<'_, '_, '_> {
    fn fmt(&self, f: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
        if let Some(unit) = self.to_str() {
            f.write_str(unit)?;
        }
        Ok(())
    }
}

/*
 * 2.3.1 Base units (page 130)
 */

/// Time
pub const S: Unit = Unit::new_base("s");
/// Length
pub const M: Unit = Unit::new_base("m");
/// Mass
pub const KG: Unit = Unit::new_base("kg");
/// Electric Current
pub const A: Unit = Unit::new_base("A");
/// Thermodynamic Temperature
pub const K: Unit = Unit::new_base("K");
/// Amount of Substance
pub const MOL: Unit = Unit::new_base("mol");
/// Luminous Intensity
pub const CD: Unit = Unit::new_base("cd");

/*
 * 2.3.4 Derived Units (page 137)
 */

macro_rules! pow {
    ($base:expr) => {
        Pow {
            base: &$base,
            exponent: Exponent::integer(1),
        }
    };
    ($base:expr, $exp:literal) => {
        Pow {
            base: &$base,
            exponent: Exponent::integer($exp),
        }
    };
}
pub(crate) use pow;

/// Plane angle. Not to be confused with m m⁻¹.
pub const RAD: Unit = Unit::new_dimensionless(Some("rad"));
/// Solid angle. Not to be confused with m² m⁻².
pub const SR: Unit = Unit::new_dimensionless(Some("sr"));
/// Frequency. Shall only be used for periodic phenomena.
pub const HZ: Unit = Unit::from_groups(&[pow!(S, -1)]).with_special_symbol("Hz");
/// Force
pub const N: Unit = Unit::from_groups(&[pow!(KG), pow!(M), pow!(S, -2)]).with_special_symbol("N");
/// Pressure, stress
pub const PA: Unit = Unit::from_groups(&[pow!(N), pow!(M, -2)]).with_special_symbol("Pa");
/// Energy, work, amount of heat
pub const J: Unit = Unit::from_groups(&[pow!(N), pow!(M)]).with_special_symbol("J");
/// Power, radiant flux
pub const W: Unit = Unit::from_groups(&[pow!(J), pow!(S, -1)]).with_special_symbol("W");
/// Electric charge
pub const C: Unit = Unit::from_groups(&[pow!(A), pow!(S)]).with_special_symbol("C");
/// Electric potential difference. Also named "voltage", "electric tension", or "tension".
pub const V: Unit = Unit::from_groups(&[pow!(W), pow!(A, -1)]).with_special_symbol("V");
/// Capacitance
pub const F: Unit = Unit::from_groups(&[pow!(C), pow!(V, -1)]).with_special_symbol("F");
/// Electric resistance
pub const OHM: Unit = Unit::from_groups(&[pow!(V), pow!(A, -1)]).with_special_symbol("Ω");
/// Electric conductance
pub const SIEMENS: Unit = Unit::from_groups(&[pow!(A), pow!(V, -1)]).with_special_symbol("S");
/// Magnetic flux
pub const WB: Unit = Unit::from_groups(&[pow!(V), pow!(S)]).with_special_symbol("Wb");
/// Magnetic flux density
pub const T: Unit = Unit::from_groups(&[pow!(WB), pow!(M, -2)]).with_special_symbol("T");
/// Inductance
pub const H: Unit = Unit::from_groups(&[pow!(WB), pow!(A, -1)]).with_special_symbol("H");
/// Celsius temperature. The numerical value of a temperature difference is the same when expressed
/// in either degrees Celsius or in Kelvins.
pub const DEGC: Unit = Unit::from_groups(&[pow!(K)]).with_special_symbol("°C");
// NOTE: The symbol `sr` for must be included to distinguish luminous flux (lumen) from
// luminous intensity (candela)
/// Luminous flux
pub const LM: Unit = Unit::from_groups(&[pow!(CD), pow!(SR)]).with_special_symbol("lm");
/// Illuminance
pub const LX: Unit = Unit::from_groups(&[pow!(LM), pow!(M, -2)]).with_special_symbol("lx");
/// Activity referred to a radionuclide. Shall only be used for stochastic processes in activity
/// referred to a radionuclide. Not to be confused with "radioactivity".
pub const BQ: Unit = Unit::from_groups(&[pow!(S, -1)]).with_special_symbol("Bq");
/// Absorbed dose, kerma
pub const GY: Unit = Unit::from_groups(&[pow!(J), pow!(KG, -1)]).with_special_symbol("Gy");
/// Dose equivalent
pub const SV: Unit = Unit::from_groups(&[pow!(J), pow!(KG, -1)]).with_special_symbol("Sv");
/// Catalytic activity
pub const KAT: Unit = Unit::from_groups(&[pow!(MOL), pow!(S, -1)]).with_special_symbol("kat");

/*
 * Examples of Coherent Derived Units (Table 5, Page 139)
 */

/// Area
pub const M2: Unit = Unit::from_groups(&[pow!(M, 2)]);
/// Volume
pub const M3: Unit = Unit::from_groups(&[pow!(M, 3)]);
/// Speed, velocity
pub const M_PERS: Unit = Unit::from_groups(&[pow!(M), pow!(S, -1)]);
/// Acceleration
pub const M_PERS2: Unit = Unit::from_groups(&[pow!(M), pow!(S, -2)]);
/// Wavenumber
pub const M_INV: Unit = Unit::from_groups(&[pow!(M, -1)]);
/// Density, mass density, mass concentration
pub const KG_PERM3: Unit = Unit::from_groups(&[pow!(KG), pow!(M, -3)]);
/// Surface density
pub const KG_PERM2: Unit = Unit::from_groups(&[pow!(KG), pow!(M, -2)]);
/// Specific volume
pub const M3_PERKG: Unit = Unit::from_groups(&[pow!(M, 3), pow!(KG, -1)]);
/// Current density
pub const A_PERM2: Unit = Unit::from_groups(&[pow!(A), pow!(M, -2)]);
/// Magnetic field strength
pub const A_PERM: Unit = Unit::from_groups(&[pow!(A), pow!(M, -1)]);
/// Amount of substance concentration
pub const MOL_PERM3: Unit = Unit::from_groups(&[pow!(MOL), pow!(M, -3)]);
/// Luminance
pub const CD_PERM2: Unit = Unit::from_groups(&[pow!(CD), pow!(M, -2)]);

/*
 * Examples of SI coherent derived units whose names and symbols include
 * SI coherent derived units with special names and symbols (Table 6, Pages 139 - 140)
 */

/// Dynamic viscosity
pub const PA_S: Unit = Unit::from_groups(&[pow!(PA), pow!(S)]);
/// Moment of force, torque
pub const N_M: Unit = Unit::from_groups(&[pow!(N), pow!(M)]);
/// Surface tension
pub const N_PERM: Unit = Unit::from_groups(&[pow!(N), pow!(M, -1)]);
/// Angular velocity, angular frequency
pub const RAD_PERS: Unit = Unit::from_groups(&[pow!(RAD), pow!(S, -1)]);
/// Angular acceleration
pub const RAD_PERS2: Unit = Unit::from_groups(&[pow!(RAD), pow!(S, -2)]);
/// Heat flux density, irradiance
pub const W_PERM2: Unit = Unit::from_groups(&[pow!(W), pow!(M, -2)]);
/// Heat capacity, entropy
pub const J_PERK: Unit = Unit::from_groups(&[pow!(J), pow!(K, -1)]);
/// Specific heat capacity, specific entropy
pub const J_PERKG_PERK: Unit = Unit::from_groups(&[pow!(J), pow!(KG, -1), pow!(K, -1)]);
/// Specific energy
pub const J_PERKG: Unit = Unit::from_groups(&[pow!(J), pow!(KG, -1)]);
/// Thermal conductivity
pub const W_PERM_PERK: Unit = Unit::from_groups(&[pow!(W), pow!(M, -1), pow!(K, -1)]);
/// Energy density
pub const J_PERM3: Unit = Unit::from_groups(&[pow!(J), pow!(M, -3)]);
/// Electric field strength
pub const V_PERM: Unit = Unit::from_groups(&[pow!(V), pow!(M, -1)]);
/// Electric charge density
pub const C_PERM3: Unit = Unit::from_groups(&[pow!(C), pow!(M, -3)]);
/// Surface charge density, Electric flux density, electric displacement
pub const C_PERM2: Unit = Unit::from_groups(&[pow!(C), pow!(M, -2)]);
/// Permittivity
pub const F_PERM: Unit = Unit::from_groups(&[pow!(F), pow!(M, -1)]);
/// Permeability
pub const H_PERM: Unit = Unit::from_groups(&[pow!(H), pow!(M, -1)]);
/// Molar energy
pub const J_PERMOL: Unit = Unit::from_groups(&[pow!(J), pow!(MOL, -1)]);
/// Molar entropy, molar heat capacity
pub const J_PERMOL_PERK: Unit = Unit::from_groups(&[pow!(J), pow!(MOL, -1), pow!(K, -1)]);
/// Exposure (x- and γ-rays)
pub const C_PERKG: Unit = Unit::from_groups(&[pow!(C), pow!(KG, -1)]);
/// Absorbed dose rate
pub const GY_PERS: Unit = Unit::from_groups(&[pow!(GY), pow!(S, -1)]);
/// Radiant intensity
pub const W_PERSR: Unit = Unit::from_groups(&[pow!(W), pow!(SR, -1)]);
/// Radiance
pub const W_PERM2_PERSR: Unit = Unit::from_groups(&[pow!(W), pow!(M, -2), pow!(SR, -1)]);
/// Catalytic activity concentration
pub const KAT_PERM3: Unit = Unit::from_groups(&[pow!(KAT), pow!(M, -3)]);

// macro_rules! rate_constant {
//     ($order:expr) => {
//         Unit::from_groups(&[pow!(MOL, 1 - order), pow!(L, order - 1), pow!(S, -1)])
//     };
// }
