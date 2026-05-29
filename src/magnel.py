"""
magnel.py
Diagrama de Magnel — Capítulo 7 do manual Torii (2020).

Plano (e, 1/Ps): cada condição de tensão define uma linha reta.
A classificação como cota superior/inferior depende do sinal do
denominador de cada equação — ver derivação em cada função.

Convenção: P em kN, M em kN·m, A em m², z em m³, σ em kPa (MPa × 1000).

As 4 restrições (em termos de u = 1/Ps, e):

  C1 serviço topo   (σ ≥ fsc): (e/zt − 1/A) ≥ D1·u  onde D1 = fsc + Mse/zt
  C2 serviço fundo  (σ ≤ fst): (1/A + e/zb) ≥ D2·u  onde D2 = Mse/zb − fst  (D2>0 → upper)
  C3 ato topo       (σ ≤ ftt): (e/zt − 1/A)/η ≤ D3·u onde D3 = ftt + Msw/zt (D3>0 → lower)
  C4 ato fundo      (σ ≥ ftc): (1/A + e/zb)/η ≤ D4·u onde D4 = Msw/zb − ftc  (D4>0 → lower)
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np


def feasible_region(
    section,
    Msw: float,
    Mse: float,
    eta: float,
    limits,
    e_range: Tuple[float, float],
    invP_range: Tuple[float, float] = (0.0, 0.01),
    n_points: int = 800,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula a região viável [lower(e), upper(e)] para 1/Ps em função de e.

    Determina corretamente cotas superiores e inferiores com base no sinal
    de cada denominador (ver análise de cada condição no módulo).

    Args:
        section:    RectangularSection
        Msw:        momento do peso próprio na seção crítica (kN·m)
        Mse:        momento total de serviço na seção crítica (kN·m)
        eta:        Ps/Pt ≈ 0.83
        limits:     StressLimits (em MPa)
        e_range:    (e_min, e_max) em metros
        invP_range: (0, 1/Ps_min) em 1/kN
        n_points:   resolução do eixo e

    Returns:
        (e_arr, lower, upper, valid)  valid = (lower ≤ upper)
    """
    A  = section.A
    zt = section.zt
    zb = section.zb

    # Tensões em kPa (1 MPa = 1000 kPa = 1000 kN/m²)
    fsc = limits.fsc * 1000.0   # < 0
    fst = limits.fst * 1000.0   # ≥ 0
    ftt = limits.ftt * 1000.0   # > 0
    ftc = limits.ftc * 1000.0   # < 0

    e_arr = np.linspace(e_range[0], e_range[1], n_points)
    lower = np.full(n_points, invP_range[0])
    upper = np.full(n_points, invP_range[1])

    # Denominadores constantes (independentes de e)
    D1 = fsc + Mse / zt         # C1: pode ser + ou −
    D2 = Mse / zb - fst         # C2: sempre > 0 (Mse/zb >> fst ≥ 0)
    D3 = eta * (ftt + Msw / zt) # C3: sempre > 0
    D4 = eta * (Msw / zb - ftc) # C4: sempre > 0 (ftc < 0)

    for i, e in enumerate(e_arr):
        n_top = e / zt - 1 / A          # numerador em C1 e C3
        n_bot = 1 / A + e / zb          # numerador em C2 e C4 (sempre > 0)

        # C1: n_top ≥ D1 · u
        if abs(D1) > 1e-9:
            v1 = n_top / D1
            if D1 > 0:
                upper[i] = min(upper[i], v1)   # cota superior
            else:
                lower[i] = max(lower[i], v1)   # cota inferior (D1 < 0 → flip)

        # C2: n_bot ≥ D2 · u  (D2 > 0 → cota superior)
        if D2 > 1e-9:
            upper[i] = min(upper[i], n_bot / D2)

        # C3: n_top/η ≤ D3 · u  (D3 > 0 → cota inferior)
        if D3 > 1e-9:
            lower[i] = max(lower[i], n_top / D3)

        # C4: n_bot/η ≤ D4 · u  (D4 > 0 → cota inferior)
        if D4 > 1e-9:
            lower[i] = max(lower[i], n_bot / D4)

    lower = np.clip(lower, invP_range[0], invP_range[1])
    upper = np.clip(upper, invP_range[0], invP_range[1])
    valid = lower <= upper + 1e-12

    return e_arr, lower, upper, valid


def magnel_lines(
    section,
    Msw: float,
    Mse: float,
    eta: float,
    limits,
    e_arr: np.ndarray,
) -> dict:
    """
    Calcula as 4 linhas de fronteira do diagrama de Magnel para plotagem.

    Returns:
        dict {nome: (invPs_array, tipo_fronteira, label)}
        tipo_fronteira: 'upper' | 'lower'
    """
    A  = section.A
    zt = section.zt
    zb = section.zb

    fsc = limits.fsc * 1000.0
    fst = limits.fst * 1000.0
    ftt = limits.ftt * 1000.0
    ftc = limits.ftc * 1000.0

    D1 = fsc + Mse / zt
    D2 = Mse / zb - fst
    D3 = eta * (ftt + Msw / zt)
    D4 = eta * (Msw / zb - ftc)

    def safe_div(num, den, fallback=np.inf):
        return np.where(np.abs(den) > 1e-9, num / den, fallback)

    n_top = e_arr / zt - 1 / A
    n_bot = 1 / A + e_arr / zb

    tipo_C1 = "upper" if D1 > 0 else "lower"

    return {
        "C1_serv_top":  (safe_div(n_top, D1), tipo_C1,   "ELS — Compresión, fibra sup."),
        "C2_serv_bot":  (safe_div(n_bot, D2), "upper",   "ELS — Tracción, fibra inf."),
        "C3_trans_top": (safe_div(n_top, D3), "lower",   "Ato — Tracción, fibra sup."),
        "C4_trans_bot": (safe_div(n_bot, D4), "lower",   "Ato — Compresión, fibra inf."),
    }


# Mantener compatibilidad con la interfaz anterior
def magnel_constraints(section, Msw, Mse, eta, limits):
    """
    Alias de magnel_lines para compatibilidad retroactiva.
    Devuelve funciones en lugar de arrays.
    """
    A  = section.A
    zt = section.zt
    zb = section.zb
    fsc = limits.fsc * 1000.0
    fst = limits.fst * 1000.0
    ftt = limits.ftt * 1000.0
    ftc = limits.ftc * 1000.0

    D1 = fsc + Mse / zt
    D2 = Mse / zb - fst
    D3 = eta * (ftt + Msw / zt)
    D4 = eta * (Msw / zb - ftc)

    tipo_C1 = "upper" if D1 > 0 else "lower"

    def _safe(num_fn, den):
        return lambda e: np.where(np.abs(den) > 1e-9, num_fn(e) / den, np.inf)

    return {
        "C1_serv_top":  (_safe(lambda e: e/zt - 1/A, D1), tipo_C1,   "ELS — Compresión, fibra sup."),
        "C2_serv_bot":  (_safe(lambda e: 1/A + e/zb, D2), "upper",   "ELS — Tracción, fibra inf."),
        "C3_trans_top": (_safe(lambda e: e/zt - 1/A, D3), "lower",   "Ato — Tracción, fibra sup."),
        "C4_trans_bot": (_safe(lambda e: 1/A + e/zb, D4), "lower",   "Ato — Compresión, fibra inf."),
    }


def select_design_point(
    e_arr: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    valid: np.ndarray,
    strategy: str = "max_e",
) -> Optional[Tuple[float, float, float]]:
    """
    Seleciona o ponto de projeto (e, 1/Ps) dentro da região viável.

    Convenção dos arrays:
        lower[i] = cota inferior de 1/Ps em e_arr[i] (máximo Ps permitido)
        upper[i] = cota superior de 1/Ps em e_arr[i] (mínimo Ps requerido)
        → maior 1/Ps = menor Ps = mais econômico

    Estratégias:
        'max_e'    — maior excentricidade factível; nesse e, 1/Ps = upper (Ps mínimo).
        'min_P'    — menor Ps globalmente: máximo de upper sobre todos os e válidos.
        'centroid' — centroide ponderado pelo comprimento do intervalo [lower, upper].

    Returns:
        (e_design, invPs_design, Ps_design) ou None se sem região viável.
    """
    if not np.any(valid):
        return None

    ve = e_arr[valid]
    vl = lower[valid]   # cota inferior de 1/Ps (Ps máximo admissível)
    vu = upper[valid]   # cota superior de 1/Ps (Ps mínimo necessário = mais econômico)

    if strategy == "max_e":
        # Maior e na região factível
        idx = np.argmax(ve)
        e_d = ve[idx]
        # Nesse e: maior 1/Ps possível = limite superior = Ps mínimo
        invP_d = vu[idx]

    elif strategy == "min_P":
        # Menor Ps globalmente = maior 1/Ps sobre todos os e válidos
        idx = np.argmax(vu)
        e_d    = ve[idx]
        invP_d = vu[idx]

    else:  # centroid
        # Centroide ponderado pelo comprimento do intervalo [lower, upper]
        larguras = vu - vl
        total = float(np.sum(larguras))
        if total > 1e-12:
            e_d = float(np.sum(ve * larguras) / total)
        else:
            e_d = float(np.mean(ve))
        # Interpolar lower e upper no e do centroide
        lo_c = float(np.interp(e_d, ve, vl))
        up_c = float(np.interp(e_d, ve, vu))
        invP_d = (lo_c + up_c) / 2.0

    Ps = 1.0 / invP_d if invP_d > 1e-12 else None
    return float(e_d), float(invP_d), Ps


def is_in_feasible_region(
    e: float,
    invPs: float,
    e_arr: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
) -> bool:
    """
    Verifica se o ponto (e, 1/Ps) está dentro da região viável.

    Interpola os limites lower e upper no valor de e dado.

    Returns:
        True se lower(e) ≤ invPs ≤ upper(e), False caso contrário.
    """
    if e < e_arr[0] or e > e_arr[-1]:
        return False
    lo = float(np.interp(e, e_arr, lower))
    up = float(np.interp(e, e_arr, upper))
    return lo <= invPs <= up
