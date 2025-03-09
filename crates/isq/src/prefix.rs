#[derive(Debug, Clone)]
pub struct Factor {
    pub base: u8,
    pub exponent: i8,
}

#[derive(Debug, Clone)]
pub struct Prefix<'a> {
    pub factor: Factor,
    pub symbol: &'a str,
}

macro_rules! prefix {
    ($exponent:literal, $symbol:literal) => {
        Prefix {
            factor: Factor {
                base: 10,
                exponent: $exponent,
            },
            symbol: $symbol,
        }
    };
}

pub const DECA: Prefix = prefix!(1, "da");
pub const HECTO: Prefix = prefix!(2, "h");
pub const KILO: Prefix = prefix!(3, "k");
pub const MEGA: Prefix = prefix!(6, "M");
pub const GIGA: Prefix = prefix!(9, "G");
pub const TERA: Prefix = prefix!(12, "T");
pub const PETA: Prefix = prefix!(15, "P");
pub const EXA: Prefix = prefix!(18, "E");
pub const ZETTA: Prefix = prefix!(21, "Z");
pub const YOTTA: Prefix = prefix!(24, "Y");
pub const RONNA: Prefix = prefix!(27, "R");
pub const QUETTA: Prefix = prefix!(30, "Q");

pub const DECI: Prefix = prefix!(-1, "d");
pub const CENTI: Prefix = prefix!(-2, "c");
pub const MILLI: Prefix = prefix!(-3, "m");
pub const MICRO: Prefix = prefix!(-6, "µ");
pub const NANO: Prefix = prefix!(-9, "n");
pub const PICO: Prefix = prefix!(-12, "p");
pub const FEMTO: Prefix = prefix!(-15, "f");
pub const ATTO: Prefix = prefix!(-18, "a");
pub const ZEPTO: Prefix = prefix!(-21, "z");
pub const YOCTO: Prefix = prefix!(-24, "y");
pub const RONTO: Prefix = prefix!(-27, "r");
pub const QUECTO: Prefix = prefix!(-30, "q");

macro_rules! binary_prefix {
    ($exponent:literal, $symbol:literal) => {
        Prefix {
            factor: Factor {
                base: 2,
                exponent: $exponent,
            },
            symbol: $symbol,
        }
    };
}

pub const KIBI: Prefix = binary_prefix!(10, "Ki");
pub const MEBI: Prefix = binary_prefix!(20, "Mi");
pub const GIBI: Prefix = binary_prefix!(30, "Gi");
pub const TEBI: Prefix = binary_prefix!(40, "Ti");
pub const PEBI: Prefix = binary_prefix!(50, "Pi");
pub const EXBI: Prefix = binary_prefix!(60, "Ei");
pub const ZEBI: Prefix = binary_prefix!(70, "Zi");
pub const YOBI: Prefix = binary_prefix!(80, "Yi");
