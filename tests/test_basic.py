from fractions import Fraction

import pytest

from isq import DAY, HOUR, METER, SECOND, Dimensionless, Exp, Mul, Scaled


def test_exp_invalid() -> None:
    with pytest.raises(Exception):
        _u1 = Exp(METER, 0)


def test_exp_eq() -> None:
    assert Exp(METER, 2) == Exp(METER, Fraction(4, 2))


def test_mul_invalid() -> None:
    with pytest.raises(Exception):
        _u0 = Mul(tuple())
    with pytest.raises(Exception):
        _u1 = Mul((Exp(METER, 1), Exp(METER.dimension, 1)))


MPERS = Mul((Exp(METER, 1), Exp(SECOND, -1)))


def test_simplify_basic() -> None:
    tg = Mul(
        (Exp(METER, 1), Exp(SECOND, -1), Exp(METER, 2), Exp(SECOND, -2))
    ).simplify()  # all root nodes
    assert not isinstance(tg, (Dimensionless, Scaled))
    assert len(tg.terms) == 2
    assert Exp(METER, 3) in tg.terms
    assert Exp(SECOND, -3) in tg.terms


def test_simplify_nested() -> None:
    expr0 = Mul((Exp(Exp(METER, 2), Fraction(1, 2)),)).simplify()
    assert isinstance(expr0, Mul)
    assert expr0.terms == Mul((Exp(METER, 1),)).terms
    assert isinstance(
        Mul((Exp(MPERS, 1), Exp(MPERS, -1))).simplify(), Dimensionless
    )


def test_simplify_eq() -> None:
    PERSM = Mul((Exp(SECOND, -1), Exp(METER, 1))).simplify()
    assert isinstance(PERSM, Mul)
    assert PERSM.terms == MPERS.terms


def test_simplify_scaled() -> None:
    from isq import FEET, MIN

    FPERM = Mul((Exp(FEET, 1), Exp(MIN, -1))).simplify()
    assert isinstance(FPERM, Scaled)
    assert FPERM.reference == MPERS

    assert FPERM.to_reference(100) == 0.508  # m per s
    assert FPERM.from_reference(0.508) == 100  # feet per minute


def test_simplify_scaled_dimensionless() -> None:
    HOURS_PER_DAY = Mul((Exp(HOUR, 1), Exp(DAY, -1))).simplify()
    assert isinstance(HOURS_PER_DAY, Scaled)
    assert HOURS_PER_DAY.to_reference(24) == 1  # day
    assert HOURS_PER_DAY.from_reference(1) == 24  # hours per day


def test_simplify_scaled2() -> None:
    # https://what-if.xkcd.com/11/
    from math import pi

    from isq import BaseDimension, BaseUnit

    BIRD = BaseUnit("bird", BaseDimension("bird"))
    POOP = BaseUnit("poop", BaseDimension("poop"))
    MOUTH = BaseUnit("mouth", BaseDimension("mouth"))
    CM = Scaled("centimeter", METER, factor=0.01)
    KM = Scaled("kilometer", METER, factor=1000)

    BIRD_PERKM2 = Mul((Exp(BIRD, 1), Exp(KM, -2)))
    POOP_PERBIRD_PERHOUR = Mul((Exp(POOP, 1), Exp(BIRD, -1), Exp(HOUR, -1)))
    HOURS_PERDAY = Mul((Exp(HOUR, 1), Exp(DAY, -1)))
    MOUTHS_PERPOOP = Mul((Exp(MOUTH, 1), Exp(POOP, -1)))
    CM2_PERMOUTH = Mul((Exp(CM, 2), Exp(MOUTH, -1)))

    PERIOD_S = Mul(
        (
            Exp(
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
            ),
        )
    ).simplify()  # = (km^2 * day) / cm^2
    assert isinstance(PERIOD_S, Scaled)
    assert PERIOD_S.factor == 100_000**2 * 86400
    assert PERIOD_S.reference == Mul((Exp(SECOND, 1),))

    num_birds = 300e9
    earth_surface_area = 4 * pi * 6378**2
    period_s = PERIOD_S.to_reference(
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
