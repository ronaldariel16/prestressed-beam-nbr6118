"""
sls.py
Estados Limites de Serviço — Capítulo 9/10 do manual Torii (2020).
NBR 6118:2014 §13.3.

Verificações implementadas:
  · ELS-D  (descompressão): σ_bot ≥ 0 MPa
  · ELS-DP (início de fissuração): σ_bot ≥ -fct,m
  · ELS-DEF (flechas): δ ≤ L/250 (longo prazo) e L/350 (elementos frágeis)
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DeflectionResult:
    """Resultado da verificação de flechas ELS-DEF."""
    delta_immediate: float    # flecha imediata total (m, positivo para baixo)
    delta_prestress: float    # contraflecha da protensão (m, positivo para cima)
    delta_long_term: float    # flecha diferida com fluência (m, positivo para baixo)
    limit_L250: float         # limite L/250 (m)
    limit_L350: float         # limite L/350 (m)
    ok_L250: bool
    ok_L350: bool


def deflection_uniform(q: float, L: float, Ecs_MPa: float, I: float) -> float:
    """
    Flecha máxima — viga simplesmente apoiada, carga uniforme.

    δ = 5qL⁴ / (384·E·I)

    Args:
        q:       carga (kN/m)
        L:       vão (m)
        Ecs_MPa: módulo secante em MPa
        I:       inércia (m⁴)

    Returns:
        Flecha em metros (positivo para baixo).
    """
    Ecs_kPa = Ecs_MPa * 1000.0
    return 5.0 * q * L**4 / (384.0 * Ecs_kPa * I)


def camber_parabolic(Ps: float, e_max: float, L: float, Ecs_MPa: float, I: float) -> float:
    """
    Contraflecha — protensão com perfil parabólico, Eq. 10.4 do manual.

    δ_p = 5·Ps·e_max·L² / (48·E·I)

    Returns:
        Contraflecha em metros (positivo = levantamento).
    """
    Ecs_kPa = Ecs_MPa * 1000.0
    return 5.0 * Ps * e_max * L**2 / (48.0 * Ecs_kPa * I)


def camber_straight(Ps: float, e: float, L: float, Ecs_MPa: float, I: float) -> float:
    """
    Contraflecha — protensão com perfil reto, Eq. 10.3 do manual.

    δ_p = Ps·e·L² / (8·E·I)

    Returns:
        Contraflecha em metros (positivo = levantamento).
    """
    Ecs_kPa = Ecs_MPa * 1000.0
    return Ps * e * L**2 / (8.0 * Ecs_kPa * I)


def check_deflection(
    section,
    concrete,
    loads,
    Ps: float,
    e_max: float,
    L: float,
    phi: float,
    profile_type: str = "parabolico",
    alpha_E: float = 1.0,
) -> DeflectionResult:
    """
    Verificação ELS-DEF para viga simplesmente apoiada.

    Flecha total (longo prazo):
        δ_total = (δ_pp + δ_gk + δ_qk) · (1 + φ) − δ_p · (1 + 0,5φ)

    Nota: δ_qk usa psi2·qk para a parcela quasi-permanente.

    Args:
        section:      RectangularSection
        concrete:     Concrete
        loads:        Loads (gk, qk, psi2 disponível)
        Ps:           força de serviço (kN)
        e_max:        excentricidade máxima (m)
        L:            vão (m)
        phi:          coeficiente de fluência φ(t∞, t0)
        profile_type: 'parabolico' | 'reto'
        alpha_E:      fator do árido para Ecs

    Returns:
        DeflectionResult
    """
    Ecs = concrete.Ecs(alpha_E)
    I   = section.I
    pp  = section.A * concrete.gamma_concrete

    # Flechas imediatas sob cargas características
    d_pp = deflection_uniform(pp,                       L, Ecs, I)
    d_gk = deflection_uniform(loads.gk,                 L, Ecs, I)
    d_qk = deflection_uniform(loads.qk * loads.psi2,    L, Ecs, I)  # quasi-permanente
    d_imm = d_pp + d_gk + d_qk

    # Contraflecha da protensão
    if profile_type == "parabolico":
        d_prest = camber_parabolic(Ps, e_max, L, Ecs, I)
    else:
        d_prest = camber_straight(Ps, e_max, L, Ecs, I)

    # Flecha diferida (NBR §13.3.2.1 simplificado)
    d_long = d_imm * (1.0 + phi) - d_prest * (1.0 + 0.5 * phi)

    lim_250 = L / 250.0
    lim_350 = L / 350.0

    return DeflectionResult(
        delta_immediate=d_imm,
        delta_prestress=d_prest,
        delta_long_term=d_long,
        limit_L250=lim_250,
        limit_L350=lim_350,
        ok_L250=abs(d_long) <= lim_250,
        ok_L350=abs(d_long) <= lim_350,
    )


def final_deflection(u_t0: float, phi: float) -> float:
    """Flecha diferida — Eq. 10.2: u(t∞) = (1+φ)·u(t0)."""
    return (1.0 + phi) * u_t0
