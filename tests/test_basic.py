from fractions import Fraction

import pytest

from isq import METER, SECOND, Dimensionless, Exp, Mul


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
    assert not isinstance(tg, Dimensionless)
    assert len(tg.terms) == 2
    assert Exp(METER, 3) in tg.terms
    assert Exp(SECOND, -3) in tg.terms


def test_simplify_nested() -> None:
    assert Mul((Exp(Exp(METER, 2), Fraction(1, 2)),)).simplify() == Mul(
        (Exp(METER, 1),)
    )
    assert isinstance(
        Mul((Exp(MPERS, 1), Exp(MPERS, -1))).simplify(), Dimensionless
    )


def test_simplify_eq() -> None:
    PERSM = Mul((Exp(METER, 1), Exp(SECOND, -1)))
    assert MPERS.simplify() == PERSM.simplify()


# TODO: https://what-if.xkcd.com/11/
