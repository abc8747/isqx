use crate::quantity::{define_quantity, Quantity};
use crate::unit::{pow, Unit, J, KG, KG_PERM2, KG_PERM3, M, M3_PERKG, N, N_M, PA, PA_S, S, W};

/// Momentum
const KG_M_PER_S: Unit = Unit::from_groups(&[pow!(KG), pow!(M), pow!(S, -1)]);
/// Angular Momentum, Action
const J_S: Unit = Unit::from_groups(&[pow!(J), pow!(S)]);
/// Moment of Inertia
const KG_M2: Unit = Unit::from_groups(&[pow!(KG), pow!(M, 2)]);
/// Strain
const STRAIN_UNIT: Unit = Unit::from_groups(&[pow!(M), pow!(M, -1)]);
/// Kinematic Viscosity
const M2_PERS: Unit = Unit::from_groups(&[pow!(M, 2), pow!(S, -1)]);

define_quantity!(
    /// Mass
    MASS, KG, "m"
);
define_quantity!(
    /// Density, $\rho = \frac{m}{V}$
    DENSITY, KG_PERM2, "\\rho"
);
define_quantity!(
    /// Surface Density, $\rho_A = \frac{m}{A}$
    SURFACE_DENSITY, KG_PERM3, "\\rho_A"
);
define_quantity!(
    /// Specific Volume, $v = \frac{1}{\rho}$
    SPECIFIC_VOLUME, M3_PERKG, "v"
);
define_quantity!(
    /// Momentum, $\mathbf{p} = m \mathbf{v}$
    MOMENTUM, KG_M_PER_S, "p"
);
define_quantity!(
    /// Angular Momentum, $\mathbf{L} = \mathbf{r} \cross \mathbf{p}$
    ANGULAR_MOMENTUM, J_S, "L"
);
define_quantity!(
    /// Moment of Inertia, $I = \int r^2 dm$
    MOMENT_OF_INERTIA, KG_M2, "I"
); // tensor property
define_quantity!(
    /// Moment, $\mathbf{M} = \mathbf{r} \cross \mathbf{F}$
    MOMENT, N_M, "M"
); // torque?
define_quantity!(
    /// Force, $\mathbf{F} = \frac{d\mathbf{p}}{dt} = m \mathbf{a}$
    FORCE, N, "F"
);
define_quantity!(
    /// Weight, $\mathbf{W} = m \mathbf{g}$
    WEIGHT, N, "W"
);
define_quantity!(
    /// Lift
    LIFT, N, "L"
);
define_quantity!(
    /// Drag
    DRAG, N, "D"
);
define_quantity!(
    /// Thrust
    THRUST, N, "T"
);
define_quantity!(
    /// Energy
    ENERGY, J, "E"
);
define_quantity!(
    /// Potential Energy, $E_p(r) = -\int_r^\infty \mathbf{F} \cdot d\mathbf{r}$
    POTENTIAL_ENERGY, J, "E_p"
); // or, V
define_quantity!(
    /// Kinetic Energy, $E_k = \frac{1}{2} m v^2$
    KINETIC_ENERGY, J, "E_k"
); // or, T
define_quantity!(
    /// Work, $W = \int \mathbf{F} \cdot d\mathbf{r}$
    WORK, J, "W"
);
define_quantity!(
    /// Power, $P = \mathbf{F} \cdot \mathbf{v} = \frac{dW}{dt}$
    POWER, W, "P"
);
define_quantity!(
    /// Lagrangian, $L(q, \dot{q}) = T(q, \dot{q}) - V(q)$
    LAGRANGIAN, J, "L"
);
// hamiltonian
define_quantity!(
    /// Action, $S = \int L dt$
    ACTION, J_S, "S"
);
define_quantity!(
    /// Pressure, $p = \frac{F}{A}$
    PRESSURE, PA, "p"
);
define_quantity!(
    /// Static Pressure, $p_s$
    STATIC_PRESSURE, PA, "p_s"
);
define_quantity!(
    /// Dynamic Pressure, $q = \frac{1}{2} \rho v^2$
    DYNAMIC_PRESSURE, PA, "q"
);
define_quantity!(
    /// Impact Pressure. For compressible flow, the impact pressure would be higher than the dynamic
    /// pressure
    IMPACT_PRESSURE, PA, "q"
);
define_quantity!(
    /// Stagnation Pressure, is what the pressure would be if the all the kinetic energy of the flow
    /// were converted to pressure reversibly
    STAGNATION_PRESSURE, PA, "p_0"
);
define_quantity!(
    /// Normal Stress, $\sigma = \frac{F}{A}$
    NORMAL_STRESS, PA, "\\sigma"
);
define_quantity!(
    /// Shear Stress, $\tau = \frac{F}{A}$
    SHEAR_STRESS, PA, "\\tau"
);
define_quantity!(
    /// Linear strain, $\varepsilon = \frac{\Delta L}{L}$
    LINEAR_STRAIN, STRAIN_UNIT, "\\varepsilon"
);
define_quantity!(
    /// Young's Modulus, $E = \frac{\sigma}{\varepsilon}$
    YOUNGS_MODULUS, PA, "E"
);
define_quantity!(
    /// Shear Strain, $\gamma = \frac{\Delta x}{d}$
    SHEAR_STRAIN, STRAIN_UNIT, "\\gamma"
);
define_quantity!(
    /// Shear Modulus, $G = \frac{\tau}{\gamma}$
    SHEAR_MODULUS, PA, "G"
);
define_quantity!(
    /// Volume Strain, $\delta = \frac{\Delta V}{V_0}$
    VOLUME_STRAIN, STRAIN_UNIT, "\\delta"
);
define_quantity!(
    /// Bulk Modulus, $K = -V_0 \frac{dp}{dV}$
    BULK_MODULUS, PA, "K"
);
define_quantity!(
    /// Poisson's Ratio, $\nu = -\frac{\Delta d}{d} / \frac{\Delta L}{L}$
    POISSONS_RATIO, STRAIN_UNIT, "\\nu"
);
define_quantity!(
    /// Viscosity (dynamic), $\tau_{xz} = \mu \frac{dv_x}{dz}$
    VISCOSITY, PA_S, "\\mu"
);
define_quantity!(
    /// Kinematic Viscosity, $\nu = \frac{\mu}{\rho}$
    KINEMATIC_VISCOSITY, M2_PERS, "\\nu"
);
