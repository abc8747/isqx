import math
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
    Exp,
    LazyFactor,
    M,
    Mul,
    S,
    Scaled,
    Tagged,
)
from isq.aerospace import ALT_GEOM, ALT_GEOP

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
    expr4s = Mul((Exp(Scaled(M, 2), 3), Exp(Scaled(S, 3), 2))).simplify()
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


#
# prefix
#


def test_prefix_invalid() -> None:
    from isq import GRAM, KG, KILO, M_PERS, W

    KW = KILO * W
    assert KW.name == KILO.name + W.name
    with pytest.raises(TypeError):
        _ = KILO * KG.dimension  # type: ignore
    with pytest.raises(TypeError):
        _ = KILO * KG
    with pytest.raises(TypeError):
        _ = KILO * GRAM
    with pytest.raises(TypeError):
        _ = KILO * M_PERS  # type: ignore
    with pytest.raises(TypeError):
        _ = KILO * KW


#
# tagged
#

M_ALT_GEOM = ALT_GEOM[M]
M_ALT_GEOP = ALT_GEOP[M]


def test_tagged_invalid_construction() -> None:
    with pytest.raises(ValueError, match="nesting"):
        _ = Tagged(M_ALT_GEOP, "another_context")


def test_tagged_simplify_cancellation() -> None:
    expr_same_ctx = Mul((M_ALT_GEOP, Exp(M_ALT_GEOP, -1)))
    simplified_same = expr_same_ctx.simplify()
    assert isinstance(simplified_same, Dimensionless)

    expr_diff_ctx = Mul((M_ALT_GEOP, Exp(M_ALT_GEOM, -1)))
    simplified_diff = expr_diff_ctx.simplify()
    assert isinstance(simplified_diff, Mul)  # shouldn't cancel
    assert set(simplified_diff.terms) == set(expr_diff_ctx.terms)


FT_ALT_GEOP = Tagged(FT, ("altitude", "geopotential"))


def test_tagged_simplify_propagates_to_reference() -> None:
    simplified = FT_ALT_GEOP.simplify()  # Scaled(Disambiguated(M, ...), ...)
    assert isinstance(simplified, Tagged)
    assert simplified.context == M_ALT_GEOP.context
    assert isinstance(simplified.reference, Scaled)
    assert simplified.reference.reference == M


def test_tagged_conversion() -> None:
    converter_ok = M_ALT_GEOP.to(FT_ALT_GEOP)
    assert converter_ok(1) == pytest.approx(1 / 0.3048)

    with pytest.raises(ValueError):
        _ = M_ALT_GEOP.to(M_ALT_GEOM)
    with pytest.raises(ValueError):
        _ = M_ALT_GEOP.to(M)
    with pytest.raises(ValueError):
        _ = M.to(M_ALT_GEOP)


def test_qty_kind_getitem() -> None:
    from isq import KNOT, M_PERS
    from isq.aerospace import TAS

    tas_mps = TAS[M_PERS]
    assert isinstance(tas_mps, Tagged)
    assert tas_mps.reference == M_PERS
    assert tas_mps.context == ("airspeed", "true")

    tas_knots = TAS[KNOT]
    assert isinstance(tas_knots, Tagged)
    assert tas_knots.reference == KNOT
    assert tas_knots.context == ("airspeed", "true")

    mps_to_knots = tas_mps.to(tas_knots)
    assert mps_to_knots(1.0) == pytest.approx(1.94384449)

    with pytest.raises(ValueError):
        _ = TAS[M]

    with pytest.raises(ValueError):
        _ = ALT_GEOP[M_PERS]

    alt_m = ALT_GEOP[M]
    alt_ft = ALT_GEOP[FT]
    assert alt_m.to(alt_ft)(100) == pytest.approx(328.08399)

    with pytest.raises(ValueError):
        _ = tas_mps.to(alt_m)


#
# alias
#


def test_alias_fail() -> None:
    from isq import DBV, Alias

    with pytest.raises(TypeError):
        _ = Alias(M, "fail")  # type: ignore
    with pytest.raises(TypeError):
        _ = Alias(DBV, "fail")


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
        _fn = Scaled(DIM_TIME, 1).to(S)  # -> BaseUnit
    assert DIM_TIME.to(Exp(DIM_TIME, 1))(1) == 1  # -> Exp
    assert DIM_TIME.to(Mul((DIM_TIME,)))(1) == 1  # -> Mul
    assert DIM_TIME.to(Scaled(DIM_TIME, 2))(1) == 0.5  # -> Scaled


def test_convert_base_unit() -> None:
    with pytest.raises(ValueError):
        _fn = S.to(M)  # incompatible dim
    with pytest.raises(ValueError):
        _fn = S.to(RAD)  # -> Dimensionless
    assert S.to(S)(1) == 1  # -> BaseUnit
    with pytest.raises(ValueError):
        _fn = S.to(S.dimension)  # -> BaseDimension
    assert S.to(Exp(S, 1))(1) == 1  # -> Exp
    assert S.to(Mul((S,)))(1) == 1  # -> Mul
    assert S.to(Scaled(S, 2))(1) == 0.5  # -> Scaled


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
    assert M2.to(Scaled(M2, 2))(1) == 0.5  # -> Scaled


def test_convert_mul() -> None:
    with pytest.raises(ValueError):
        _fn = M_PERS.to(M)  # incompatible dim
    with pytest.raises(ValueError):
        _fn = M_PERS.to(RAD)  # -> Dimensionless
    assert M_PERS.to(M_PERS)(1) == 1  # -> Mul
    assert M_PERS.to(Scaled(M_PERS, 2))(1) == 0.5  # -> Scaled

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
    assert DAY.to(Mul((S,)))(1) == 86400  # -> Mul
    assert MIN.to(HOUR)(60) == 1  # -> Scaled
    assert DAY.to(DAY)(1) == 1


def test_translated_is_terminal() -> None:
    from isq import CELSIUS, KILO, Translated

    with pytest.raises(ValueError):
        Exp(CELSIUS, 2)
    with pytest.raises(ValueError):
        Mul((CELSIUS, M))
    with pytest.raises(ValueError):
        Scaled(CELSIUS, 2)
    with pytest.raises(TypeError):
        KILO * CELSIUS  # type: ignore
    with pytest.raises(TypeError):
        Translated(CELSIUS, 1, "celsius + 1")
    with pytest.raises(TypeError):
        Translated(M_PERS, 1, "m/s + 1")


def test_convert_translated() -> None:
    from isq import CELSIUS, DIM_TEMPERATURE, FAHRENHEIT, K, R

    assert CELSIUS.dimension == DIM_TEMPERATURE

    assert K.to(CELSIUS)(1.1) == -272.04999999999995  # inexact
    assert K.to(CELSIUS, exact=True)(Fraction(11, 10)) == Fraction(-27205, 100)

    c_to_f = CELSIUS.to(FAHRENHEIT, exact=True)
    assert isinstance(c_to_f.scale, Fraction) and c_to_f.scale == Fraction(9, 5)
    assert isinstance(c_to_f.offset, Fraction) and c_to_f.offset == Fraction(
        32, 1
    )
    assert c_to_f(100) == 212
    assert CELSIUS.to(FAHRENHEIT).scale == 1.7999999999999998  # inexact

    f_to_c = FAHRENHEIT.to(CELSIUS, exact=True)
    assert f_to_c(32) == 0
    assert f_to_c(212) == 100
    c_to_r = CELSIUS.to(R, exact=True)
    assert c_to_r(0) == Fraction("273.15") * Fraction(9, 5)


def test_convert_tagged_translated() -> None:
    from isq import CELSIUS, K

    SURFACE_TEMP_C = Tagged(CELSIUS, "surface")
    SURFACE_TEMP_K = Tagged(K, "surface")

    c_to_k_exact = SURFACE_TEMP_C.to(SURFACE_TEMP_K, exact=True)
    assert c_to_k_exact(10) == Fraction(28315, 100)
    k_to_c_exact = SURFACE_TEMP_K.to(SURFACE_TEMP_C, exact=True)
    assert k_to_c_exact(c_to_k_exact(10)) == 10

    with pytest.raises(ValueError):
        SURFACE_TEMP_C.to(K)
    with pytest.raises(ValueError):
        K.to(SURFACE_TEMP_C)


def test_logarithmic_is_terminal() -> None:
    from isq import DBV, DIM_LENGTH, KILO
    from isq.core import Exp, Logarithmic, Mul, Scaled

    with pytest.raises(ValueError):
        Exp(DBV, 2)
    with pytest.raises(ValueError):
        Mul((DBV, M))
    with pytest.raises(ValueError):
        Scaled(DBV, 2)
    with pytest.raises(TypeError):
        _ = KILO * DBV
    with pytest.raises(TypeError):
        Logarithmic(DBV, "power", log_base=10, name="fail")  # type: ignore
    with pytest.raises(TypeError):
        Logarithmic(DIM_LENGTH, "power", log_base=10, name="fail")  # type: ignore


def test_convert_logarithmic() -> None:
    from isq import DBM, DBUV, DBV, DBW, NPV, NPW

    assert isinstance(DBM.dimension, Dimensionless)

    dbw_to_dbm = DBW.to(DBM, exact=True)
    assert dbw_to_dbm.scale == 1
    assert dbw_to_dbm.offset == Fraction(30, 1)
    assert dbw_to_dbm(10) == 40
    npw_to_dbw = NPW.to(DBW)
    assert npw_to_dbw.scale == pytest.approx(20 / math.log(10))
    assert npw_to_dbw.offset == 0
    assert npw_to_dbw(1) == pytest.approx(8.6858896)

    dbv_to_dbuv = DBV.to(DBUV, exact=True)
    assert dbv_to_dbuv.scale == 1
    assert dbv_to_dbuv.offset == Fraction(120, 1)
    assert dbv_to_dbuv(1) == 121
    assert DBV.to(DBUV).offset == 119.99999999999999  # inexact
    dbv_to_npv = DBV.to(NPV)
    assert dbv_to_npv.offset == 0
    assert dbv_to_npv.scale == pytest.approx(math.log(10) / 20)
    assert dbv_to_npv(20) == pytest.approx(2.302585)
    npv_to_dbv = NPV.to(DBV)
    assert npv_to_dbv.offset == 0
    assert npv_to_dbv.scale == pytest.approx(20 / math.log(10))


def test_convert_logarithmic_with_prefix() -> None:
    from isq import DBV, DECI, MILLI, NPV

    npv_to_decinpv = NPV.to(DECI * NPV, exact=True)
    assert npv_to_decinpv.offset == 0
    assert npv_to_decinpv.scale == 10
    millinpv_to_decinpv = (MILLI * NPV).to(DECI * NPV, exact=True)
    assert millinpv_to_decinpv.scale == Fraction(1, 100)
    decinpv_to_npv = (DECI * NPV).to(DBV)
    assert decinpv_to_npv.offset == 0
    assert decinpv_to_npv.scale == pytest.approx(20e-1 / math.log(10))


def test_convert_logarithmic_fail() -> None:
    from isq import DBM, DBV, V

    with pytest.raises(TypeError):
        V.to(DBV)
    with pytest.raises(TypeError):
        DBV.to(V)
    with pytest.raises(ValueError):
        DBV.to(DBM)


def test_angle_conversion() -> None:
    from decimal import Decimal, localcontext

    from isq import DEG, PI, REV, E

    with localcontext() as ctx:
        assert PI.to_decimal(ctx) == Decimal("3.141592653589793238462643383")
        assert E.to_decimal(ctx) == Decimal("2.718281828459045235360287471")

    deg_to_rad = DEG.to(RAD)
    assert deg_to_rad(180) == pytest.approx(math.pi)
    assert deg_to_rad(360) == pytest.approx(2 * math.pi)

    rad_to_deg = RAD.to(DEG)
    assert rad_to_deg(math.pi) == pytest.approx(180.0)
    assert rad_to_deg(1) == pytest.approx(180 / math.pi)

    with localcontext() as ctx:
        ctx.prec = 100
        pi_100 = PI.to_decimal(ctx)

        assert DEG.to(RAD, exact=True, ctx=ctx)(180) == pi_100
        assert RAD.to(DEG, exact=True, ctx=ctx)(Fraction(pi_100)) == 180

    assert REV.to(RAD)(1) == pytest.approx(2 * math.pi)
    assert RAD.to(REV)(math.pi) == pytest.approx(0.5)
    assert DEG.to(REV)(360) == pytest.approx(1.0)


def test_derived_angle_conversion() -> None:
    from isq import DEG

    DEG_PER_S = Mul((DEG, Exp(S, -1)))
    RAD_PER_S = Mul((RAD, Exp(S, -1)))

    assert DEG_PER_S.to(RAD_PER_S)(180) == pytest.approx(math.pi)

    result = DEG_PER_S.to(RAD_PER_S, exact=True)(Fraction(180))
    assert isinstance(result, Fraction)
    assert result == pytest.approx(Fraction(math.pi))


#
# integration test
#


def test_xkcd_whatif_11() -> None:  # https://what-if.xkcd.com/11/
    from math import pi

    from isq import CENTI, KILO, YEAR, BaseDimension, BaseUnit

    BIRD = BaseUnit(BaseDimension("bird"), "bird")
    POOP = BaseUnit(BaseDimension("poop"), "poop")
    MOUTH = BaseUnit(BaseDimension("mouth"), "mouth")

    BIRD_PERKM2 = Mul((BIRD, Exp(KILO * M, -2)))
    POOP_PERBIRD_PERHOUR = Mul((POOP, Exp(BIRD, -1), Exp(HOUR, -1)))
    HOURS_PERDAY = Mul((HOUR, Exp(DAY, -1)))
    MOUTHS_PERPOOP = Mul((MOUTH, Exp(POOP, -1)))
    CM2_PERMOUTH = Mul((Exp(CENTI * M, 2), Exp(MOUTH, -1)))

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
    period_yr = PERIOD.to(YEAR)(
        1
        / (
            (num_birds / earth_surface_area)  # bird / km^2
            * 1  # poop / (bird * hour)
            * 16  # hours / day
            * 1  # mouth / poop
            * 15  # cm^2 / mouth
        )
    )
    assert period_yr == pytest.approx(195, abs=0.7)

    from isq import FL_OZ, MI, MILLI, MPG, YEAR

    MM2 = Exp(MILLI * M, 2)
    assert Exp(MPG, -1).to(MM2)(1 / 20) == pytest.approx(0.11760729)
    poop_dropping_rate = 0.5  # fl_oz / (day * bird)
    total_distance_driven_rate = 3e12  # mi / year
    assert 1 / (
        Mul(
            (
                BIRD,
                Mul((FL_OZ, Exp(DAY, -1), Exp(BIRD, -1))),
                Exp(Mul((MI, Exp(YEAR, -1))), -1),
            )
        ).to(Exp(MPG, -1))(
            num_birds * poop_dropping_rate / total_distance_driven_rate
        )
    ) == pytest.approx(7.009, rel=1e-3)  # NOTE: xkcd's 13MPG is wrong
