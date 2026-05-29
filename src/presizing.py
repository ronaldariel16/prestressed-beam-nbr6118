"""
presizing.py
Pré-dimensionamento da seção transversal — Capítulo 6 do manual Torii (2020).
NBR 6118:2014.

Critério geral:  Eqs. 6.9 e 6.10 → módulos seccionais mínimos considerando
                 diferença de momentos (serviço − η·peso próprio).
Critério simpl.: Eq. 6.13      → módulo mínimo baseado somente no momento
                 de serviço e no limite de compressão em serviço.
"""
import math


def presize_general(Mse: float, Msw: float, eta: float, limits) -> tuple:
    """
    Critério geral — Eqs. 6.9 e 6.10 do manual.

    Combina as condições de serviço e do ato para determinar os módulos
    seccionais mínimos independentemente de P e e.

    Args:
        Mse:    momento total de serviço na seção crítica (kN·m, positivo)
        Msw:    momento do peso próprio na seção crítica (kN·m, positivo)
        eta:    Ps/Pt — razão de perdas (≈ 0,83)
        limits: instância de StressLimits (tensões em MPa)

    Returns:
        (zt_req, zb_req) em m³ — módulos seccionais mínimos necessários.
    """
    # Tensões limites em kPa (1 MPa = 1000 kPa = 1000 kN/m²)
    ftt_kPa = limits.ftt * 1000.0   # > 0
    ftc_kPa = limits.ftc * 1000.0   # < 0
    fst_kPa = limits.fst * 1000.0   # ≥ 0
    fsc_kPa = limits.fsc * 1000.0   # < 0

    delta_M = max(Mse - eta * Msw, 0.0)

    # Eq. 6.9 — fibra inferior (determinante para viga simplesmente apoiada)
    # De: σ_bot_service ≥ fsc e σ_top_transfer ≤ ftt  → eliminando P e e
    den_b = eta * ftt_kPa - fsc_kPa  # = η·ftt + |fsc| > 0
    zb_req = delta_M / den_b if den_b > 1e-12 else 0.0

    # Eq. 6.10 — fibra superior
    # De: σ_top_service ≤ fst e σ_bot_transfer ≥ ftc → eliminando P e e
    den_t = eta * abs(ftc_kPa) - fst_kPa  # = η·|ftc| - fst
    zt_req = delta_M / den_t if den_t > 1e-12 else 0.0

    return zt_req, zb_req


def presize_simplified(Ms: float, eta: float, limits) -> tuple:
    """
    Critério simplificado — Eq. 6.13 do manual.

    Calcula o módulo seccional mínimo considerando somente o momento de
    serviço total Ms e o limite de compressão em serviço fsc.

    Args:
        Ms:     momento total de serviço na seção crítica (kN·m)
        eta:    Ps/Pt (não utilizado, mantido por compatibilidade)
        limits: instância de StressLimits

    Returns:
        (zt_req, zb_req) em m³ — iguais para seção simétrica.
    """
    fsc_kPa = abs(limits.fsc) * 1000.0  # kPa
    z_req = Ms / fsc_kPa if fsc_kPa > 1e-12 else 0.0
    return z_req, z_req  # seção simétrica: zt = zb


def min_height_rectangular(b: float, zt_req: float, zb_req: float) -> float:
    """
    Altura mínima de uma seção retangular b×h dado os módulos seccionais
    mínimos requeridos.

    Para seção retangular: z = b·h²/6  →  h = √(6·z_req/b).
    A seção retangular é simétrica, portanto zt = zb = b·h²/6.

    Args:
        b:      largura da seção (m)
        zt_req: módulo seccional superior mínimo (m³)
        zb_req: módulo seccional inferior mínimo (m³)

    Returns:
        h_min em metros.
    """
    z_req = max(zt_req, zb_req)
    if z_req <= 0.0 or b <= 0.0:
        return 0.0
    return math.sqrt(6.0 * z_req / b)


def round_up_to_step(h: float, step: float = 0.05) -> float:
    """
    Arredonda h para cima ao múltiplo de step (em metros).
    Por padrão arredonda a cada 5 cm.
    """
    return math.ceil(h / step) * step
