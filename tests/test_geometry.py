"""
Testes unitários para o módulo geometry.
"""

import pytest
from src.geometry import RectangularSection


def test_rectangular_section_basic():
    s = RectangularSection(b=0.30, h=0.80)
    assert s.A == pytest.approx(0.24)
    assert s.I == pytest.approx(0.30 * 0.80**3 / 12)
    assert s.yt == 0.40
    assert s.yb == 0.40
    assert s.zt == s.zb


def test_rectangular_section_modulus():
    s = RectangularSection(b=0.30, h=0.80)
    expected_z = 0.30 * 0.80**2 / 6
    assert s.zt == pytest.approx(expected_z)
    assert s.zb == pytest.approx(expected_z)


def test_invalid_dimensions():
    with pytest.raises(ValueError):
        RectangularSection(b=0, h=0.5)
    with pytest.raises(ValueError):
        RectangularSection(b=0.3, h=-0.5)
