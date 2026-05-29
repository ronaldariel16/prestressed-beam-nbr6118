"""
reinforcement.py
Escolha e arranjo da armadura ativa.
Referência: NBR 6118:2014 §9.6.1.2, §18.6.2.3, Tabela 7.2.
"""
from __future__ import annotations

import math
from typing import List, Tuple


def number_of_strands(Pj_total: float, steel) -> int:
    """
    Número mínimo de cordoalhas necessárias.

    Args:
        Pj_total: força total de protensão requerida (kN)
        steel:    instância de PrestressSteel

    Returns:
        Número de cordoalhas (inteiro ≥ 1).
    """
    Pj_lim = steel.Pj_lim_unit()
    return math.ceil(Pj_total / Pj_lim)


def arrange_strands(
    n: int,
    section,
    cover: float = 0.04,
    spacing: float = 0.05,
    diameter_strand: float = 0.015,
) -> Tuple[List[float], float]:
    """
    Arranjo das cordoalhas em camadas respeitando espaçamentos mínimos.

    Disposição: cordoalhas em camadas horizontais a partir da fibra inferior,
    com cobertura e espaçamento iguais ao especificado.

    Args:
        n:               número de cordoalhas
        section:         RectangularSection
        cover:           cobertura nominal (m), default 4 cm
        spacing:         espaçamento mínimo entre eixos das cordoalhas (m), default 5 cm
        diameter_strand: diâmetro da cordoalha (m), default 15,2 mm ≈ 0,015 m

    Returns:
        (positions_y, e_real)
          positions_y: lista de ordenadas y_i medidas a partir da base da seção (m)
          e_real:      excentricidade resultante = yb − ȳ (m, positivo abaixo do centroide)
    """
    b = section.b
    h = section.h

    # Máximo de cordoalhas por camada (espaçamento horizontal)
    n_por_camada = max(1, int((b - 2.0 * cover) / spacing) + 1)

    n_camadas = math.ceil(n / n_por_camada)

    positions_y: List[float] = []
    restantes = n
    for camada in range(n_camadas):
        y_from_base = cover + diameter_strand / 2.0 + camada * spacing
        if y_from_base >= h - cover:
            break  # não ultrapassa a fibra superior
        n_nessa_camada = min(n_por_camada, restantes)
        positions_y.extend([y_from_base] * n_nessa_camada)
        restantes -= n_nessa_camada

    if not positions_y:
        positions_y = [cover + diameter_strand / 2.0]

    y_baricentro = sum(positions_y) / len(positions_y)
    e_real = section.yb - y_baricentro   # positivo abaixo do centroide

    return positions_y, e_real
