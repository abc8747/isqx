use core::num::NonZero;

// keeping it simple, no generics for now
// avoids 0/0, 1/-2
#[derive(Debug, Clone)]
pub struct IrreducibleFraction {
    numerator: NonZero<i16>,
    denominator: NonZero<u16>,
}

impl IrreducibleFraction {
    pub const fn new(numerator: i16, denominator: u16) -> Self {
        Self {
            numerator: NonZero::<i16>::new(numerator).unwrap(),
            denominator: NonZero::<u16>::new(denominator).unwrap(),
        }
    }

    pub const fn numerator(self) -> NonZero<i16> {
        self.numerator
    }

    pub const fn denominator(self) -> NonZero<u16> {
        self.denominator
    }
}

/// An exponent should be a rational number.
#[derive(Debug, Clone)]
pub enum Exponent {
    Integer(i16),
    Fraction(IrreducibleFraction),
}

impl Exponent {
    pub const fn integer(value: i16) -> Self {
        Self::Integer(value)
    }

    pub const fn fraction(numerator: i16, denominator: u16) -> Self {
        Self::Fraction(IrreducibleFraction::new(numerator, denominator))
    }

    pub const ONE: Self = Self::integer(1);
}
