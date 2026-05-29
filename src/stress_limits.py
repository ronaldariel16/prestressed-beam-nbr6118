"""
stress_limits.py
Tensões limites no concreto conforme NBR 6118:2014 §8.2.5 e §17.2.4.3.2.
Escopo: concretos até C50.
"""

from dataclasses import dataclass


@dataclass
class StressLimits:
    """Tensões limites para uma situação."""
    ftt: float  # tração no ato (MPa, positivo)
    ftc: float  # compressão no ato (MPa, negativo)
    fst: float  # tração em serviço (MPa, positivo)
    fsc: float  # compressão em serviço (MPa, negativo)


def stress_limits(concrete, situation: str = 'all') -> StressLimits:
    """
    Calcula tensões limites.

    Args:
        concrete:  instância de Concrete
        situation: 'all' | 'transfer' | 'service' | 'service_ELS_D'

    Returns:
        StressLimits

    Notas:
        - No ato (transfer):  ftt = +0,3·fckj^(2/3) ; ftc = -0,7·fckj
        - Em serviço:         fst = +0,3·fck^(2/3)  ; fsc = -0,7·fck
        - Para ELS-D:         fst = 0
    """
    ftt = 0.3 * concrete.fckj ** (2/3)
    ftc = -0.7 * concrete.fckj
    fst = 0.3 * concrete.fck ** (2/3)
    fsc = -0.7 * concrete.fck

    if situation == 'service_ELS_D':
        fst = 0.0

    return StressLimits(ftt=ftt, ftc=ftc, fst=fst, fsc=fsc)
