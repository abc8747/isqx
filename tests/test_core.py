from fractions import Fraction

import pytest

from isq import (
    DAY,
    FT,
    HOUR,
    MIN,
    RAD,
    BaseUnit,
    Dimensionless,
    Disambiguated,
    Exp,
    LazyFactor,
    M,
    Mul,
    S,
    Scaled,
)
from isq.aerospace import M_ALT_GEOM, M_ALT_GEOP

#
# Exp
#


def test_exp_invalid() -> None:
    with pytest.raises(ValueError):
        _u1 = Exp(M, 0)


def test_exp_eq() -> None:
    assert Exp(M, 2) == Exp(M, Fraction(4, 2))


def test_exp_dimension() -> None:
    assert Exp(M, 2).dimension == Exp(M.dimension, 2)
    assert Exp(Exp(M, 2), 3).dimension == Exp(Exp(M.dimension, 2), 3)


def test_exp_simplify() -> None:
    # distribute exponent

    expr0s = Exp(Exp(M, 2), Fraction(1, 2)).simplify()
    assert isinstance(expr0s, BaseUnit)
    assert expr0s == M

    expr0s = Exp(Exp(M, 2), 3).simplify()
    assert isinstance(expr0s, Exp)
    assert expr0s == Exp(M, 6)


#
# Mul
#


def test_mul_invalid() -> None:
    with pytest.raises(ValueError):
        _u0 = Mul(tuple())
    with pytest.raises(ValueError):
        _u1 = Mul((M, M.dimension))


M_PERS = Mul((M, Exp(S, -1)))
FT_PERMIN = Mul((FT, Exp(MIN, -1)))


def test_mul_dimension() -> None:
    assert M_PERS.dimension == Mul((M.dimension, Exp(S.dimension, -1)))


def test_mul_simplify_basic() -> None:
    # cancel terms
    expr1s = Mul((M, Exp(M, -1))).simplify()
    assert isinstance(expr1s, Dimensionless)

    # distribute inner
    expr2s = Exp(M_PERS, 2).simplify()
    assert isinstance(expr2s, Mul)
    assert expr2s.terms == Mul((Exp(M, 2), Exp(S, -2))).terms

    # combine terms with same base
    expr_s = Mul((M, Exp(S, -1), Exp(M, 2), Exp(S, -2))).simplify()
    assert isinstance(expr_s, Mul)
    assert expr_s.terms == Mul((Exp(M, 3), Exp(S, -3))).terms

    # return lone term if it is raised to power of one
    expr_s = Mul((Exp(M, 1),)).simplify()
    assert isinstance(expr_s, BaseUnit)
    assert expr_s == M


def test_mul_simplify_nested() -> None:
    assert isinstance(Mul((M_PERS, Exp(M_PERS, -1))).simplify(), Dimensionless)


def test_mul_simplify_ordering() -> None:
    PERSM = Mul((Exp(S, -1), M)).simplify()
    assert isinstance(PERSM, Mul)
    assert PERSM.terms == M_PERS.terms


#
# Scaled
#


def test_scaled_dimension() -> None:
    assert FT.dimension == M.dimension


def test_scaled_simplify_nested() -> None:
    from isq import CENTURY

    # century is defined w.r.t. to decade, and decade is defined w.r.t. year etc
    # we want to "collapse" it so century is defined w.r.t. seconds
    expr3s = CENTURY.simplify()
    assert isinstance(expr3s, Scaled)
    assert expr3s.reference == S
    assert isinstance(expr3s.factor, LazyFactor)
    assert expr3s.factor.to_exact() == 86400 * 365.25 * 100


def test_scaled_simplify_mixed() -> None:
    expr4s = Mul(
        (Exp(Scaled(M, 2, "x"), 3), Exp(Scaled(S, 3, "y"), 2))
    ).simplify()
    assert isinstance(expr4s, Scaled)
    assert expr4s.reference == Mul((Exp(M, 3), Exp(S, 2)))
    assert isinstance(expr4s.factor, LazyFactor)
    assert expr4s.factor.to_exact() == 2**3 * 3**2

    expr4s = FT_PERMIN.simplify()
    assert isinstance(expr4s, Scaled)
    assert expr4s.reference == M_PERS
    assert isinstance(expr4s.factor, LazyFactor)
    assert expr4s.factor.to_exact() == Fraction(3048, 10000) / 60


def test_scaled_simplify_dimensionless() -> None:
    expr5s = Mul((HOUR, Exp(DAY, -1))).simplify()
    assert isinstance(expr5s, Scaled)
    assert isinstance(expr5s.reference, Dimensionless)
    assert isinstance(expr5s.factor, LazyFactor)
    assert expr5s.factor.to_exact() == Fraction(1, 24)  # day per hour


def test_scaled_simplify_with_lazy_factor() -> None:
    from isq import IN  # -> ft -> m

    result = Exp(IN.simplify(), 2).simplify()

    assert isinstance(result, Scaled)
    assert result.reference == Exp(M, 2)
    assert isinstance(result.factor, LazyFactor)

    assert result.factor.to_approx() == pytest.approx((0.3048 / 12) ** 2)


def test_scaled_simplify_with_lazy_factor_multiple_terms() -> None:
    from isq import PSI  # defined by lbf -> lbm -> kg and in -> ft -> m

    psi_simplified = PSI.simplify()  # Scaled(PA.simplify(), LazyFactor(...))
    assert isinstance(psi_simplified, Scaled)
    assert isinstance(psi_simplified.factor, LazyFactor)
    assert isinstance(psi_simplified.reference, Mul)
    from isq import PA

    pa_simplified = PA.simplify()
    assert isinstance(pa_simplified, Mul)
    assert set(psi_simplified.reference.terms) == set(pa_simplified.terms)
    PSI_TO_PA_FACTOR = (0.45359237 * 9.80665) / ((0.3048 / 12) ** 2)
    assert psi_simplified.factor.to_approx() == pytest.approx(PSI_TO_PA_FACTOR)

    result = Exp(psi_simplified, 2).simplify()
    assert isinstance(result, Scaled)
    assert isinstance(result.factor, LazyFactor)

    from isq import KG, M, S

    result_ref_simplified = result.reference.simplify()
    assert isinstance(result_ref_simplified, Mul)
    # P**2 = (F/A)**2
    #      = ((M*L*T**-2) / L**2)**2
    #      = (M * L**-1 * T**-2)**2
    assert set(result_ref_simplified.terms) == set(
        (Exp(KG, 2), Exp(M, -2), Exp(S, -4))
    )
    assert result.factor.to_approx() == pytest.approx(PSI_TO_PA_FACTOR**2)


def test_scaled_simplify_complex() -> None:
    # https://what-if.xkcd.com/11/
    from decimal import Decimal
    from math import pi

    from isq import BaseDimension, BaseUnit

    BIRD = BaseUnit(BaseDimension("bird"), "bird")
    POOP = BaseUnit(BaseDimension("poop"), "poop")
    MOUTH = BaseUnit(BaseDimension("mouth"), "mouth")
    CM = Scaled(M, Decimal("0.01"), "centimeter")
    KM = Scaled(M, Decimal("1000"), "kilometer")

    BIRD_PERKM2 = Mul((BIRD, Exp(KM, -2)))
    POOP_PERBIRD_PERHOUR = Mul((POOP, Exp(BIRD, -1), Exp(HOUR, -1)))
    HOURS_PERDAY = Mul((HOUR, Exp(DAY, -1)))
    MOUTHS_PERPOOP = Mul((MOUTH, Exp(POOP, -1)))
    CM2_PERMOUTH = Mul((Exp(CM, 2), Exp(MOUTH, -1)))

    PERIOD = Exp(
        Mul(
            (
                BIRD_PERKM2,
                POOP_PERBIRD_PERHOUR,
                HOURS_PERDAY,
                MOUTHS_PERPOOP,
                CM2_PERMOUTH,
            ),
        ),
        -1,
    ).simplify()  # = (km^2 * day) / cm^2
    assert isinstance(PERIOD, Scaled)
    assert isinstance(PERIOD.factor, LazyFactor)
    assert PERIOD.factor.to_exact() == 100_000**2 * 86400
    assert PERIOD.reference == S

    num_birds = 300e9
    earth_surface_area = 4 * pi * 6378**2
    period_s = PERIOD.to(S)(
        1
        / (
            (num_birds / earth_surface_area)  # bird / km^2
            * 1  # poop / (bird * hour)
            * 16  # hours / day
            * 1  # mouth / poop
            * 15  # cm^2 / mouth
        )
    )
    assert period_s / (365 * 24 * 3600) == pytest.approx(195, abs=0.5)


#
# prefix
#


def test_prefix_invalid() -> None:
    from isq import GRAM, KG, KILO, W

    KW = KILO * W
    assert KW.name == KILO.name + W.name  # type: ignore
    with pytest.raises(TypeError):
        _ = KILO * KG.dimension  # type: ignore
    with pytest.raises(TypeError):
        _ = KILO * KG
    with pytest.raises(TypeError):
        _ = KILO * Mul((KG, Exp(S, -1)))
    with pytest.raises(TypeError):
        _ = KILO * KW
    with pytest.raises(TypeError):
        _ = KILO * GRAM
    with pytest.raises(TypeError):
        _ = KILO * Exp(M, 3)  # type: ignore


#
# disambiguated
#


def test_disambiguated_invalid_construction() -> None:
    with pytest.raises(ValueError, match="nesting"):
        _ = Disambiguated(M_ALT_GEOP, "another_context")


def test_disambiguated_simplify_cancellation() -> None:
    expr_same_ctx = Mul((M_ALT_GEOP, Exp(M_ALT_GEOP, -1)))
    simplified_same = expr_same_ctx.simplify()
    assert isinstance(simplified_same, Dimensionless)

    expr_diff_ctx = Mul((M_ALT_GEOP, Exp(M_ALT_GEOM, -1)))
    simplified_diff = expr_diff_ctx.simplify()
    assert isinstance(simplified_diff, Mul)  # shouldn't cancel
    assert set(simplified_diff.terms) == set(expr_diff_ctx.terms)


FT_ALT_GEOP = Disambiguated(FT, ("altitude", "geopotential"))


def test_disambiguated_simplify_propagates_to_reference() -> None:
    simplified = FT_ALT_GEOP.simplify()  # Scaled(Disambiguated(M, ...), ...)
    assert isinstance(simplified, Disambiguated)
    assert simplified.context == M_ALT_GEOP.context
    assert isinstance(simplified.reference, Scaled)
    assert simplified.reference.reference == M


def test_disambiguated_conversion() -> None:
    converter_ok = M_ALT_GEOP.to(FT_ALT_GEOP)
    assert converter_ok(1) == pytest.approx(1 / 0.3048)

    with pytest.raises(ValueError):
        _ = M_ALT_GEOP.to(M_ALT_GEOM)
    with pytest.raises(ValueError):
        _ = M_ALT_GEOP.to(M)
    with pytest.raises(ValueError):
        _ = M.to(M_ALT_GEOP)


#
# Unit conversions
#


def test_convert_dimensionless() -> None:
    from isq import SR

    assert RAD.to(RAD)(1) == 1  # -> Dimensionless

    with pytest.raises(ValueError):
        _fn = RAD.to(SR)  # incompatible dim


def test_convert_base_dimension() -> None:
    from isq import DIM_LENGTH, DIM_TIME

    with pytest.raises(ValueError):
        _fn = DIM_LENGTH.to(DIM_TIME)  # incompatible dim
    with pytest.raises(ValueError):
        _fn = DIM_LENGTH.to(RAD.dimension)  # -> Dimensionless
    assert DIM_TIME.to(DIM_TIME)(1) == 1  # -> BaseDimension
    with pytest.raises(ValueError):
        _fn = Scaled(DIM_TIME, 1, "s").to(S)  # -> BaseUnit
    assert DIM_TIME.to(Exp(DIM_TIME, 1))(1) == 1  # -> Exp
    assert DIM_TIME.to(Mul((DIM_TIME,), "dim_time1"))(1) == 1  # -> Mul
    assert DIM_TIME.to(Scaled(DIM_TIME, 2, "dim_time1"))(1) == 0.5  # -> Scaled


def test_convert_base_unit() -> None:
    with pytest.raises(ValueError):
        _fn = S.to(M)  # incompatible dim
    with pytest.raises(ValueError):
        _fn = S.to(RAD)  # -> Dimensionless
    assert S.to(S)(1) == 1  # -> BaseUnit
    with pytest.raises(ValueError):
        _fn = S.to(S.dimension)  # -> BaseDimension
    assert S.to(Exp(S, 1))(1) == 1  # -> Exp
    assert S.to(Mul((S,), "s1"))(1) == 1  # -> Mul
    assert S.to(Scaled(S, 2, "2s1"))(1) == 0.5  # -> Scaled


def test_convert_exp() -> None:
    M2 = Exp(M, 2)
    with pytest.raises(ValueError):
        _fn = M2.to(M)  # incompatible dim
    with pytest.raises(ValueError):
        _fn = M2.to(RAD)  # -> Dimensionless
    with pytest.raises(ValueError):
        _fn = M2.to(M2.dimension)  # unit -> dimension
    assert M2.to(M2)(1) == 1  # -> Exp
    assert M2.to(Mul((M2,)))(1) == 1  # -> Mul
    assert M2.to(Scaled(M2, 2, "2m^2"))(1) == 0.5  # -> Scaled


def test_convert_mul() -> None:
    with pytest.raises(ValueError):
        _fn = M_PERS.to(M)  # incompatible dim
    with pytest.raises(ValueError):
        _fn = M_PERS.to(RAD)  # -> Dimensionless
    assert M_PERS.to(M_PERS)(1) == 1  # -> Mul
    assert M_PERS.to(Scaled(M_PERS, 2, "2m/s"))(1) == 0.5  # -> Scaled

    M2_PERS2 = Exp(M_PERS, 2)  # would be simplified to Mul((Exp(...), ...))
    FT2_PERMIN2 = Exp(FT_PERMIN, 2)
    assert M2_PERS2.to(FT2_PERMIN2)(1) == 60**2 * 0.3048**-2
    assert M2_PERS2.to(M2_PERS2)(1) == 1


def test_convert_scaled() -> None:
    from isq import MIN

    with pytest.raises(ValueError):
        _fn = DAY.to(M)  # incompatible dim
    with pytest.raises(ValueError):
        _fn = DAY.to(RAD)  # -> Dimensionless
    assert DAY.to(S)(1) == 86400  # -> BaseUnit
    with pytest.raises(ValueError):
        _value = HOUR.to(S.dimension)  # -> BaseDimension
    assert DAY.to(Exp(S, 1))(1) == 86400  # -> Exp
    assert DAY.to(Mul((S,), "s1"))(1) == 86400  # -> Mul
    assert MIN.to(HOUR)(60) == 1  # -> Scaled
    assert DAY.to(DAY)(1) == 1
