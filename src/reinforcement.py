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
    diameter_strand: float = 0.0152,
) -> Tuple[List[float], float]:
    """
    Arranjo das cordoalhas em camadas respeitando espaçamentos mínimos.

    Convenção: `spacing` é o espaçamento LIVRE (clear) entre superfícies de
    cordoalhas adjacentes (horizontal e vertical), conforme NBR 6118:2014 §18.6.2.3.
    O espaçamento entre eixos (c-a-c) é: spacing + diameter_strand.

    Posicionamento:
      Camada 1: y = cover + diameter_strand/2   (desde a base)
      Camada k: y = y_{k-1} + spacing           (spacing = c-a-c vertical entre camadas)

    Número máximo por camada (horizontal):
      n_max: n·d + (n-1)·s ≤ b − 2c
      → n_max = floor((b − 2c + s) / (d + s))

    Args:
        n:               número de cordoalhas
        section:         RectangularSection
        cover:           cobertura nominal (m); default 4 cm
        spacing:         espaçamento livre entre superfícies (m); default 5 cm
        diameter_strand: diâmetro da cordoalha (m); default 15,2 mm = 0,0152 m

    Returns:
        (positions_y, e_real)
          positions_y: ordenadas y_i desde a base da seção (m)
          e_real:      excentricidade = yb − ȳ (m, positivo abaixo do centroide)
    """
    b = section.b
    h = section.h

    # Número máximo de cordoalhas por camada com espaçamento livre s
    # Condição: n·d + (n-1)·s ≤ b - 2c  →  n ≤ (b - 2c + s) / (d + s)
    n_por_camada = max(1, int((b - 2.0 * cover + spacing) / (diameter_strand + spacing)))

    n_camadas = math.ceil(n / n_por_camada)

    positions_y: List[float] = []
    restantes = n
    for camada in range(n_camadas):
        # Posição vertical: camada 1 ao nível do eixo das cordoalhas
        # spacing entre camadas = espaçamento entre eixos (c-a-c vertical)
        y_from_base = cover + diameter_strand / 2.0 + camada * spacing
        if y_from_base >= h - cover:
            break  # não pode ultrapassar a fibra superior
        n_nessa_camada = min(n_por_camada, restantes)
        positions_y.extend([y_from_base] * n_nessa_camada)
        restantes -= n_nessa_camada

    if not positions_y:
        positions_y = [cover + diameter_strand / 2.0]

    y_baricentro = sum(positions_y) / len(positions_y)
    e_real = section.yb - y_baricentro   # positivo abaixo do centroide

    return positions_y, e_real
