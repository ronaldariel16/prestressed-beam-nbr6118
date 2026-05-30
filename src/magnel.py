"""
magnel.py
Diagrama de Magnel — Capítulo 7 do manual Torii (2020).

Plano (e, 1/Ps): cada condição de tensão define uma linha reta.
A classificação como cota superior/inferior depende do sinal do denominador.

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


# ── Helper: bounds crudos en un único punto e ─────────────────────────────

def _cotas_en_e(
    e: float,
    A: float, zt: float, zb: float,
    D1: float, D2: float, D3: float, D4: float,
) -> Tuple[float, float]:
    """
    Calcula las cotas inferior y superior RAW (sin clipping) de 1/Ps
    para un valor de e dado.

    La cota inferior lo se fuerza a ≥ 0 (1/Ps no puede ser negativo).

    Returns:
        (lo, up) — el intervalo válido de 1/Ps; infactible si lo >= up.
    """
    n_top = e / zt - 1 / A
    n_bot = 1 / A + e / zb    # siempre > 0

    lo: float = 0.0            # invPs ≥ 0 (Ps finito, positivo)
    up: float = float("inf")

    # C1: n_top ≥ D1·u
    if abs(D1) > 1e-12:
        v1 = n_top / D1
        if D1 > 0:
            up = min(up, v1)    # cota superior
        else:
            lo = max(lo, v1)    # cota inferior (puede ser negativa → queda en 0)

    # C2: n_bot ≥ D2·u  (D2 > 0 siempre → cota superior)
    if D2 > 1e-12:
        up = min(up, n_bot / D2)

    # C3: n_top/η ≤ D3·u  (D3 > 0 siempre → cota inferior)
    if D3 > 1e-12:
        lo = max(lo, n_top / D3)

    # C4: n_bot/η ≤ D4·u  (D4 > 0 siempre → cota inferior)
    if D4 > 1e-12:
        lo = max(lo, n_bot / D4)

    return lo, up


def _denominadores(
    A: float, zt: float, zb: float,
    Msw: float, Mse: float, eta: float,
    fsc: float, fst: float, ftt: float, ftc: float,
) -> Tuple[float, float, float, float]:
    """Calcula los 4 denominadores constantes de las restricciones de Magnel."""
    D1 = fsc + Mse / zt          # C1: puede ser + o −
    D2 = Mse / zb - fst          # C2: siempre > 0
    D3 = eta * (ftt + Msw / zt)  # C3: siempre > 0
    D4 = eta * (Msw / zb - ftc)  # C4: siempre > 0 (ftc < 0)
    return D1, D2, D3, D4


# ── Región factible (arrays para visualización) ───────────────────────────

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
    Calcula la región factible [lower(e), upper(e)] para visualización.

    La condición de validez usa cotas CRUDAS (sin clipping) con
    desigualdad estricta (lo < up) para garantizar que los puntos
    seleccionados queden claramente en el interior del polígono.

    Returns:
        (e_arr, lower_display, upper_display, valid)
        lower/upper están recortados a invP_range para la visualización.
        valid se calcula sobre los valores crudos.
    """
    A  = section.A
    zt = section.zt
    zb = section.zb

    fsc = limits.fsc * 1000.0
    fst = limits.fst * 1000.0
    ftt = limits.ftt * 1000.0
    ftc = limits.ftc * 1000.0

    D1, D2, D3, D4 = _denominadores(A, zt, zb, Msw, Mse, eta, fsc, fst, ftt, ftc)

    e_arr  = np.linspace(e_range[0], e_range[1], n_points)
    lo_raw = np.empty(n_points)
    up_raw = np.empty(n_points)

    for i, e in enumerate(e_arr):
        lo_raw[i], up_raw[i] = _cotas_en_e(e, A, zt, zb, D1, D2, D3, D4)

    # valid: condición estricta sobre valores crudos
    # up_raw > 0 y lo_raw < up_raw con tolerancia pequeña
    TOL = 1e-7
    valid = (up_raw > TOL) & (lo_raw < up_raw - TOL)

    # Recortar para visualización
    lower = np.clip(lo_raw, invP_range[0], invP_range[1])
    upper = np.clip(up_raw, invP_range[0], invP_range[1])

    return e_arr, lower, upper, valid


# ── Selección del punto de diseño ─────────────────────────────────────────

def select_design_point(
    section,
    Msw: float,
    Mse: float,
    eta: float,
    limits,
    e_min: float,
    e_max: float,
    strategy: str = "max_e",
    n_pts: int = 1000,
) -> Optional[Tuple[float, float, float]]:
    """
    Selecciona el punto de diseño (e, 1/Ps) dentro de la región factible.

    Trabaja sobre cotas CRUDAS (sin clipping) para evitar artefactos.
    La condición de factibilidad es: lo >= 0  AND  lo < up  AND  up > 0.

    Estrategias:
        'max_e'    — mayor e factible; en ese e, 1/Ps = up (Ps mínimo).
        'min_P'    — menor Ps global (mayor 1/Ps = mayor up sobre todos los e válidos).
        'centroid' — centroide ponderado por el ancho del intervalo [lo, up].

    Returns:
        (e_design, invPs_design, Ps_design) o None si no hay región factible.
    """
    A  = section.A
    zt = section.zt
    zb = section.zb

    fsc = limits.fsc * 1000.0
    fst = limits.fst * 1000.0
    ftt = limits.ftt * 1000.0
    ftc = limits.ftc * 1000.0

    D1, D2, D3, D4 = _denominadores(A, zt, zb, Msw, Mse, eta, fsc, fst, ftt, ftc)
    e_vals = np.linspace(e_min, e_max, n_pts)

    # --- Primera pasada: recopilar todos los e válidos y sus cotas ----
    validos: list = []   # (e, lo, up, ancho)
    for e in e_vals:
        lo, up = _cotas_en_e(e, A, zt, zb, D1, D2, D3, D4)
        if lo >= 0.0 and up > 0.0 and lo < up:
            validos.append((e, lo, up, up - lo))

    if not validos:
        return None

    # Ancho mínimo para que el punto quede visualmente dentro del polígono.
    # Se exige ≥ 50 % del ancho máximo de la región factible, garantizando
    # que el punto de diseño quede en la zona ancha del polígono y no en su
    # vértice extremo donde el intervalo se hace cero.
    ancho_max = max(v[3] for v in validos)
    umbral    = ancho_max * 0.50   # 50 % del ancho máximo

    # ── max_e: mayor e con ancho ≥ umbral ────────────────────────────
    if strategy == "max_e":
        for e, lo, up, ancho in reversed(validos):
            if ancho >= umbral:
                return float(e), float(up), 1.0 / up
        # Si ninguno supera el umbral, devolver el mayor e con ancho > 0
        e, lo, up, _ = validos[-1]
        return float(e), float(up), 1.0 / up

    # ── min_P: mayor up (= menor Ps) con ancho ≥ umbral ─────────────
    elif strategy == "min_P":
        candidatos = [(e, lo, up, ancho) for e, lo, up, ancho in validos
                      if ancho >= umbral]
        if not candidatos:
            candidatos = validos
        mejor = max(candidatos, key=lambda v: v[2])   # mayor up
        e, lo, up, _ = mejor
        return float(e), float(up), 1.0 / up

    # ── centroid: centroide ponderado por ancho [lo, up] ─────────────
    else:
        puntos_e:     list = []
        puntos_mid:   list = []
        puntos_ancho: list = []

        for e in e_vals:
            lo, up = _cotas_en_e(e, A, zt, zb, D1, D2, D3, D4)
            if lo >= 0.0 and lo <= up and up > 0.0:
                ancho = up - lo
                puntos_e.append(e)
                puntos_mid.append((lo + up) / 2.0)
                puntos_ancho.append(ancho)

        if not puntos_e:
            return None

        W    = sum(puntos_ancho)
        e_c  = sum(e * w for e, w in zip(puntos_e, puntos_ancho)) / W
        m_c  = sum(m * w for m, w in zip(puntos_mid, puntos_ancho)) / W

        return float(e_c), float(m_c), 1.0 / m_c if m_c > 0 else None


# ── Verificación de un punto ──────────────────────────────────────────────

def is_in_feasible_region(
    e: float,
    invPs: float,
    section,
    Msw: float,
    Mse: float,
    eta: float,
    limits,
) -> bool:
    """
    Verifica si el punto (e, 1/Ps) está dentro de la región factible.
    Usa cotas crudas (sin clipping) para máxima precisión.

    Returns:
        True si lo(e) ≤ invPs ≤ up(e) con up > 0.
    """
    A  = section.A
    zt = section.zt
    zb = section.zb

    fsc = limits.fsc * 1000.0
    fst = limits.fst * 1000.0
    ftt = limits.ftt * 1000.0
    ftc = limits.ftc * 1000.0

    D1, D2, D3, D4 = _denominadores(A, zt, zb, Msw, Mse, eta, fsc, fst, ftt, ftc)
    lo, up = _cotas_en_e(e, A, zt, zb, D1, D2, D3, D4)

    return up > 0.0 and lo <= invPs <= up


# ── Líneas de frontera para visualización ────────────────────────────────

def magnel_lines(
    section,
    Msw: float,
    Mse: float,
    eta: float,
    limits,
    e_arr: np.ndarray,
) -> dict:
    """
    Calcula las 4 líneas de frontera del diagrama de Magnel para plotear.

    Returns:
        dict {nombre: (invPs_array, tipo_frontera, etiqueta)}
        tipo_frontera: 'upper' | 'lower'
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

    def _div(num: np.ndarray, den: float) -> np.ndarray:
        if abs(den) < 1e-12:
            return np.full_like(num, np.inf)
        return num / den

    n_top = e_arr / zt - 1 / A
    n_bot = 1 / A + e_arr / zb
    tipo_C1 = "upper" if D1 > 0 else "lower"

    return {
        "C1_serv_top":  (_div(n_top, D1), tipo_C1, "ELS — Compresión, fibra sup."),
        "C2_serv_bot":  (_div(n_bot, D2), "upper", "ELS — Tracción, fibra inf."),
        "C3_trans_top": (_div(n_top, D3), "lower", "Ato — Tracción, fibra sup."),
        "C4_trans_bot": (_div(n_bot, D4), "lower", "Ato — Compresión, fibra inf."),
    }


# ── Compatibilidad retroactiva ────────────────────────────────────────────

def magnel_constraints(section, Msw, Mse, eta, limits):
    """Alias de magnel_lines con interfaz de funciones (retrocompatibilidad)."""
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

    def _sf(num_fn, den):
        return lambda e_a: np.where(abs(den) > 1e-12, num_fn(e_a) / den, np.inf)

    return {
        "C1_serv_top":  (_sf(lambda e: e/zt - 1/A, D1), tipo_C1, "ELS — Compresión, fibra sup."),
        "C2_serv_bot":  (_sf(lambda e: 1/A + e/zb, D2), "upper", "ELS — Tracción, fibra inf."),
        "C3_trans_top": (_sf(lambda e: e/zt - 1/A, D3), "lower", "Ato — Tracción, fibra sup."),
        "C4_trans_bot": (_sf(lambda e: 1/A + e/zb, D4), "lower", "Ato — Compresión, fibra inf."),
    }
