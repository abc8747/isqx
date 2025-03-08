use crate::exponent::Exponent;

// e.g. T, L, M, I, Θ, N, J
#[derive(Debug, Clone)]
pub struct BaseDimension<'d> {
    name: &'d str,
}

impl<'b, 'd> BaseDimension<'d> {
    pub const fn new(name: &'d str) -> Self {
        Self { name }
    }

    pub const fn name(&self) -> &'d str {
        self.name
    }

    pub const fn pow(&'b self, exponent: Exponent) -> BaseDimensionGroup<'b, 'd> {
        BaseDimensionGroup {
            base: self,
            exponent,
        }
    }
}

#[derive(Debug, Clone)]
pub struct BaseDimensionGroup<'b, 'd> {
    pub base: &'b BaseDimension<'d>,
    pub exponent: Exponent,
}

#[derive(Debug, Clone)]
pub struct Dimension<'g, 'b, 'd> {
    groups: &'g [BaseDimensionGroup<'b, 'd>],
}

impl<'g, 'b, 'd> Dimension<'g, 'b, 'd> {
    pub const fn new(groups: &'g [BaseDimensionGroup<'b, 'd>]) -> Self {
        Self { groups }
    }

    pub const fn groups(self) -> &'g [BaseDimensionGroup<'b, 'd>] {
        self.groups
    }

    pub const fn is_dimensionless(self) -> bool {
        self.groups.is_empty()
    }

    // e.g. [s, s] -> [s^2]
    pub fn simplify(self) -> Self {
        todo!()
    }
}

pub const LENGTH: Dimension = Dimension::new(&[BaseDimension::new("T").pow(Exponent::ONE)]);
pub const TIME: Dimension = Dimension::new(&[BaseDimension::new("L").pow(Exponent::ONE)]);
pub const MASS: Dimension = Dimension::new(&[BaseDimension::new("M").pow(Exponent::ONE)]);
pub const CURRENT: Dimension = Dimension::new(&[BaseDimension::new("I").pow(Exponent::ONE)]);
pub const TEMPERATURE: Dimension = Dimension::new(&[BaseDimension::new("Θ").pow(Exponent::ONE)]);
pub const AMOUNT: Dimension = Dimension::new(&[BaseDimension::new("N").pow(Exponent::ONE)]);
pub const INTENSITY: Dimension = Dimension::new(&[BaseDimension::new("J").pow(Exponent::ONE)]);
