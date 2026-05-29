"""
tendon_profile.py
Perfil do tendão ao longo da viga — Capítulo 7/8 do manual Torii (2020).

Perfis implementados:
  · reto:       e(x) = e_max  (constante em todo o vão)
  · parabólico: e(x) = e_end + (e_max − e_end) · 4(x/L)(1 − x/L)

Zona admissível: bounds [e_min(x), e_max(x)] para cada posição ao longo da viga,
derivados das 4 condições de tensão com a força Ps conhecida.

Convenção: e positivo → cabo abaixo do centroide.
"""
from __future__ import annotations

import numpy as np


def straight_profile(
    e: float,
    L: float,
    n_points: int = 101,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perfil reto: excentricidade constante ao longo do vão.

    Args:
        e:        excentricidade constante (m)
        L:        comprimento do vão (m)
        n_points: pontos de discretização

    Returns:
        (x_arr, e_arr)
    """
    x = np.linspace(0.0, L, n_points)
    return x, np.full_like(x, float(e))


def parabolic_profile(
    e_max: float,
    L: float,
    e_end: float = 0.0,
    n_points: int = 101,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Perfil parabólico — clássico para viga simplesmente apoiada.

    e(x) = e_end + (e_max − e_end) · 4(x/L)(1 − x/L)

    e_max é atingido em x = L/2; nos apoios e = e_end (default 0).

    Args:
        e_max:    excentricidade máxima no meio do vão (m)
        L:        comprimento do vão (m)
        e_end:    excentricidade nos apoios (m, default 0)
        n_points: pontos de discretização

    Returns:
        (x_arr, e_arr)
    """
    x = np.linspace(0.0, L, n_points)
    e = e_end + (e_max - e_end) * 4.0 * (x / L) * (1.0 - x / L)
    return x, e


def admissible_zone(
    section,
    concrete,
    loads,
    support,
    Ps: float,
    limits,
    cover_bottom: float = 0.05,
    cover_top: float = 0.05,
    n_points: int = 101,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula a zona admissível [e_min(x), e_max(x)] a cada posição x.

    Para cada seção, as 4 condições de tensão determinam os limites da
    excentricidade do cabo dado que Ps é conhecido.

    Condições (em kPa, Ps em kN):
      C1 (serviço topo  σ ≥ fsc): e ≥  zt·(fsc·A/Ps + 1) − zt·Ms/(Ps·zt)
      C2 (serviço fundo σ ≤ fst): e ≤ −zb·(fst·A/Ps + 1) + zb·Ms/(Ps·zb)
      C3 (ato topo      σ ≤ ftt): e ≤  zt·(ftt·A/Pt + 1) + zt·Msw/(Pt·zt)
      C4 (ato fundo     σ ≥ ftc): e ≥ −zb·(ftc·A/Pt + 1) − zb·Msw/(Pt·zb)

    Args:
        section:      RectangularSection
        concrete:     Concrete
        loads:        Loads
        support:      BeamSupport
        Ps:           força de serviço (kN)
        limits:       StressLimits (MPa)
        cover_bottom: cobertura inferior mínima (m)
        cover_top:    cobertura superior mínima (m)
        n_points:     pontos de discretização

    Returns:
        (x_arr, e_min_arr, e_max_arr) em metros.
    """
    A  = section.A
    zt = section.zt
    zb = section.zb

    # Conversão MPa → kPa
    fsc = limits.fsc * 1000.0   # < 0
    fst = limits.fst * 1000.0   # ≥ 0
    ftt = limits.ftt * 1000.0   # > 0
    ftc = limits.ftc * 1000.0   # < 0

    # Estimativa de Pt (perdas imediatas ≈ 10%)
    Pt = Ps / 0.9

    x_arr = np.linspace(0.0, support.L, n_points)

    # Momentos ao longo da viga
    pp   = A * concrete.gamma_concrete
    M_sw = np.array([support.M_uniform(xi, pp)       for xi in x_arr])
    M_gk = np.array([support.M_uniform(xi, loads.gk) for xi in x_arr])
    M_qk = np.array([support.M_uniform(xi, loads.qk) for xi in x_arr])
    Mse  = M_sw + M_gk + M_qk

    # Limites geométricos
    e_min_geo = -(zt - cover_top)    # cabo não pode ir acima da fibra superior − cobertura
    e_max_geo =  zb - cover_bottom   # cabo não pode ir abaixo da fibra inferior − cobertura

    e_min_arr = np.full(n_points, e_min_geo)
    e_max_arr = np.full(n_points, e_max_geo)

    for i in range(n_points):
        Ms_i  = Mse[i]
        Msw_i = M_sw[i]

        # C1 (serviço topo): e ≥ zt·(1 + fsc/·(A/Ps)) + Ms/Ps
        c1 = zt * (1.0 + fsc * A / Ps) + Ms_i / Ps
        # C4 (ato fundo): e ≥ -zb·(1 + ftc·A/Pt) - Msw/Pt
        c4 = -zb * (1.0 + ftc * A / Pt) - Msw_i / Pt

        # C2 (serviço fundo): e ≤ -zb·(1 + fst·A/Ps) + Ms/Ps
        c2 = -zb * (1.0 + fst * A / Ps) + Ms_i / Ps
        # C3 (ato topo): e ≤ zt·(1 + ftt·A/Pt) + Msw/Pt
        c3 = zt * (1.0 + ftt * A / Pt) + Msw_i / Pt

        e_min_arr[i] = max(e_min_arr[i], c1, c4)
        e_max_arr[i] = min(e_max_arr[i], c2, c3)

    return x_arr, e_min_arr, e_max_arr


def verify_profile(
    e_profile: np.ndarray,
    e_min: np.ndarray,
    e_max: np.ndarray,
) -> np.ndarray:
    """
    Verifica se o perfil proposto está dentro da zona admissível.

    Returns:
        Array booleano: True onde o perfil é admissível.
    """
    return (e_profile >= e_min - 1e-6) & (e_profile <= e_max + 1e-6)
