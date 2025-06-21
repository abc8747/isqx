def test_fmt_basic() -> None:
    from isq import BTU, FT, HOUR, IN, R
    from isq.fmt import BasicFormatter

    K_VALUE = BTU * IN / (HOUR * FT**2 * R)
    fmt = BasicFormatter(verbose=True)
    assert (
        fmt.format(K_VALUE)
        == """btu_it · inch · (hour · foot² · rankine)⁻¹, where:
- btu_it = 1055.05585262 · joule
  - joule = newton · meter
    - newton = kilogram · meter · second⁻²
- inch = 1/12 · foot
  - foot = 0.3048 · meter
- hour = 60 · minute
  - minute = 60 · second
- rankine = 5/9 · kelvin"""
    )
    assert (
        fmt.format(K_VALUE.simplify())
        == "1055.05585262 · 1/12 · 0.3048 · 60⁻¹ · 60⁻¹ · 0.3048⁻² · 5/9⁻¹ · (meter · kilogram · second⁻³ · kelvin⁻¹)"
    )
