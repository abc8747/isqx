from fractions import Fraction

import pytest

from isq import (
    DAY,
    HOUR,
    BaseUnit,
    Dimensionless,
    Exp,
    M,
    Mul,
    S,
    Scaled,
)


def test_exp_invalid() -> None:
    with pytest.raises(ValueError):
        _u1 = Exp(M, 0)


def test_exp_eq() -> None:
    assert Exp(M, 2) == Exp(M, Fraction(4, 2))


def test_exp_dimension() -> None:
    assert Exp(M, 2).dimension == Exp(M.dimension, 2)
    assert Exp(Exp(M, 2), 3).dimension == Exp(Exp(M.dimension, 2), 3)


def test_exp_simplify() -> None:
    expr0 = Exp(Exp(M, 2), Fraction(1, 2))
    expr0s = expr0.simplify()
    assert isinstance(expr0s, BaseUnit)
    assert expr0s == M


def test_mul_invalid() -> None:
    with pytest.raises(ValueError):
        _u0 = Mul(tuple())
    with pytest.raises(ValueError):
        _u1 = Mul((Exp(M, 1), Exp(M.dimension, 1)))


MPERS = Mul((Exp(M, 1), Exp(S, -1)))


def test_mul_dimension() -> None:
    assert MPERS.dimension == Mul((Exp(M.dimension, 1), Exp(S.dimension, -1)))


def test_mul_simplify_basic() -> None:
    tg = Mul(
        (Exp(M, 1), Exp(S, -1), Exp(M, 2), Exp(S, -2))
    ).simplify()  # all root nodes
    assert isinstance(tg, Mul)
    assert len(tg.terms) == 2
    assert Exp(M, 3) in tg.terms
    assert Exp(S, -3) in tg.terms


def test_mul_simplify_nested() -> None:
    expr1 = Mul((Exp(M, 1),))
    expr1s = expr1.simplify()
    assert isinstance(expr1s, BaseUnit)
    assert expr1s == M

    assert isinstance(
        Mul((Exp(MPERS, 1), Exp(MPERS, -1))).simplify(), Dimensionless
    )


def test_mul_simplify_ordering() -> None:
    PERSM = Mul((Exp(S, -1), Exp(M, 1))).simplify()
    assert isinstance(PERSM, Mul)
    assert PERSM.terms == MPERS.terms


def test_scaled_dimension() -> None:
    from isq import FT

    assert FT.dimension == M.dimension


def test_scaled_simplify_nested() -> None:
    from isq import CENTURY

    CENTURY_SIMPL = CENTURY.simplify()
    assert isinstance(CENTURY_SIMPL, Scaled)
    assert CENTURY_SIMPL.reference == S
    assert CENTURY_SIMPL.factor == 86400 * 365.25 * 100


def test_scaled_simplify_mixed() -> None:
    from isq import FT, MIN

    FPERM = Mul((Exp(FT, 1), Exp(MIN, -1))).simplify()
    assert isinstance(FPERM, Scaled)
    assert FPERM.reference == MPERS

    assert FPERM.to_reference(100) == 0.508  # m per s
    assert FPERM.from_reference(0.508) == 100  # feet per minute


def test_scaled_simplify_dimensionless() -> None:
    HOURS_PER_DAY = Mul((Exp(HOUR, 1), Exp(DAY, -1))).simplify()
    assert isinstance(HOURS_PER_DAY, Scaled)
    assert HOURS_PER_DAY.to_reference(24) == 1  # day
    assert HOURS_PER_DAY.from_reference(1) == 24  # hours per day


def test_scaled_simplify_complex() -> None:
    # https://what-if.xkcd.com/11/
    from math import pi

    from isq import BaseDimension, BaseUnit

    BIRD = BaseUnit("bird", BaseDimension("bird"))
    POOP = BaseUnit("poop", BaseDimension("poop"))
    MOUTH = BaseUnit("mouth", BaseDimension("mouth"))
    CM = Scaled("centimeter", M, factor=0.01)
    KM = Scaled("kilometer", M, factor=1000)

    BIRD_PERKM2 = Mul((Exp(BIRD, 1), Exp(KM, -2)))
    POOP_PERBIRD_PERHOUR = Mul((Exp(POOP, 1), Exp(BIRD, -1), Exp(HOUR, -1)))
    HOURS_PERDAY = Mul((Exp(HOUR, 1), Exp(DAY, -1)))
    MOUTHS_PERPOOP = Mul((Exp(MOUTH, 1), Exp(POOP, -1)))
    CM2_PERMOUTH = Mul((Exp(CM, 2), Exp(MOUTH, -1)))

    PERIOD = Exp(
        Mul(
            (
                Exp(BIRD_PERKM2, 1),
                Exp(POOP_PERBIRD_PERHOUR, 1),
                Exp(HOURS_PERDAY, 1),
                Exp(MOUTHS_PERPOOP, 1),
                Exp(CM2_PERMOUTH, 1),
            ),
        ),
        -1,
    ).simplify()  # = (km^2 * day) / cm^2
    assert isinstance(PERIOD, Scaled)
    assert PERIOD.factor == 100_000**2 * 86400
    assert PERIOD.reference == S

    num_birds = 300e9
    earth_surface_area = 4 * pi * 6378**2
    period_s = PERIOD.to_reference(
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


def test_scaled_convert_invalid() -> None:
    with pytest.raises(ValueError):  # dimension -> unit
        _u1 = Scaled("s", S.dimension, 1).to(S)
    with pytest.raises(ValueError):  # unit -> dimension
        _u1 = HOUR.to(S.dimension)

    # from isq import DEGC, K


def test_convert() -> None:
    from isq import MIN

    assert DAY.to(S)(1) == 86400  # seconds
    assert MIN.to(HOUR)(60) == 1  # hour
