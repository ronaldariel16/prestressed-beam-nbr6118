"""
stress_check.py
Verificação de tensões nas fibras superior e inferior (Eqs. 5.4-5.9 do manual).

Convenção:
  - Tração positiva, compressão negativa
  - e positiva quando abaixo do centroide
  - σ_top = -P/A + P·e/zt - M/zt
  - σ_bottom = -P/A - P·e/zb + M/zb
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class StressResult:
    sigma_top: float     # MPa
    sigma_bottom: float  # MPa
    passes_top: bool
    passes_bottom: bool

    @property
    def ok(self) -> bool:
        return self.passes_top and self.passes_bottom


def stresses_at_section(P: float, e: float, M: float, section) -> Tuple[float, float]:
    """
    Tensões nas fibras superior e inferior.

    Args:
        P: força de protensão (kN, sempre positiva)
        e: excentricidade (m, positiva abaixo do centroide)
        M: momento fletor (kN·m, positivo traciona fibra inferior)
        section: instância de RectangularSection

    Returns:
        (σ_top, σ_bottom) em MPa
    """
    # Conversão de unidades: kN, m, m² → MPa = MN/m²
    # σ [MPa] = (P [kN] / A [m²]) / 1000
    A = section.A
    zt = section.zt
    zb = section.zb

    sigma_top = (-P / A + P * e / zt - M / zt) / 1000.0
    sigma_bottom = (-P / A - P * e / zb + M / zb) / 1000.0
    return sigma_top, sigma_bottom


def check_stresses(sigma_top: float, sigma_bottom: float,
                   limits, situation: str) -> StressResult:
    """
    Verifica tensões contra limites.

    Args:
        sigma_top, sigma_bottom: tensões calculadas (MPa)
        limits: instância de StressLimits
        situation: 'transfer' ou 'service'

    Returns:
        StressResult com flags de aprovação
    """
    if situation == 'transfer':
        f_min, f_max = limits.ftc, limits.ftt
    elif situation in ('service', 'service_ELS_D'):
        f_min, f_max = limits.fsc, limits.fst
    else:
        raise ValueError(f"situation inválida: {situation}")

    passes_top = f_min <= sigma_top <= f_max
    passes_bottom = f_min <= sigma_bottom <= f_max

    return StressResult(
        sigma_top=sigma_top,
        sigma_bottom=sigma_bottom,
        passes_top=passes_top,
        passes_bottom=passes_bottom,
    )
