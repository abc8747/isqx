#![cfg_attr(not(any(test, feature = "std")), no_std)]
/// A system for representing physical units.
///
/// Unlike libraries like `uom` (Rust), or `pint` (Python), it does not seek to "wrap" numerical
/// values with their units. It is common for different rows in a matrix to represent different
/// quantities, making it very difficult to annotate properly. This crate instead intends to provide
/// *documentation* for the Python side, with good support for static typing and IDE autocompletion.
///
/// In the future, we should provide static checking at definition time, very much like `impunity`,
/// though it is not the main focus right now.
///
/// [1] The International System of Units (SI): Text in English (updated in 2024), 9th edition 2019,
///     V3.01 August 2024. Sèvres Cedex BIPM 2024, 2024.
///     Available: https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf
///
/// [2] “NIST Handbook 44 - 2024 - Appendix C. General Tables of Units of Measurement,” NIST,
///     Available: https://www.nist.gov/document/nist-handbook-44-2024-appendix-c-pdf

/// Dimensional exponents: an integer or a fraction
pub mod exponent;
/// A unit.
pub mod unit;
