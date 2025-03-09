pub mod classical_mechanics;
pub mod space_and_time;
use crate::unit::Unit;

// todo: separate lifetimes, but not now
#[derive(Debug, Clone)]
pub struct Quantity<'base, 'group, 'name> {
    si_unit: Unit<'base, 'group, 'name>,
    symbol: &'name str,
    /// A private "unique id" that does not change even after symbol changes
    slug: &'name str,
}

impl<'base, 'group, 'name> Quantity<'base, 'group, 'name> {
    pub const fn new(
        si_unit: Unit<'base, 'group, 'name>,
        symbol: &'name str,
        slug: &'name str,
    ) -> Self {
        Self {
            si_unit,
            symbol,
            slug,
        }
    }

    pub const fn symbol(self) -> &'name str {
        self.symbol
    }

    pub const fn si_unit(self) -> Unit<'base, 'group, 'name> {
        self.si_unit
    }

    /// Change the symbol.
    pub const fn with_symbol(self, symbol: &'name str) -> Self {
        Self {
            si_unit: self.si_unit,
            symbol,
            slug: self.slug,
        }
    }
}

macro_rules! define_quantity {
    ($(#[$meta:meta])* $slug:ident, $si_unit:ident, $symbol:literal) => {
        $(#[$meta])*
        pub const $slug: Quantity = Quantity::new($si_unit, $symbol, stringify!($slug));
    };
}
pub(crate) use define_quantity;
