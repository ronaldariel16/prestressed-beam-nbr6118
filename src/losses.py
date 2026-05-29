"""
losses.py
Perdas de protensão — Capítulo 11 do manual.
Referência: NBR 6118:2014 §9.6.3.

Convenções:
  - Pj: força aplicada no macaco (kN)
  - Pt: força após perdas imediatas (kN)
  - Ps: força em serviço, após todas as perdas (kN)

Estimativas iniciais (Cap. 5 do manual):
  - Pt ≈ 0,90·Pj
  - Ps ≈ 0,75·Pj
  - η = Ps/Pt ≈ 0,83

Implementar conforme T10.x do tasks.md.
"""

import math


# =============================================================================
# PERDAS IMEDIATAS — §9.6.3.3
# =============================================================================

def friction_loss(Pj: float, x: float, alpha_total: float,
                  mu: float = 0.2, k: float = 0.002) -> float:
    """
    Perda por atrito — Eq. 11.2 do manual; §9.6.3.3.2.2 NBR 6118.
    ΔP(x) = Pj·[1 - exp(-(μ·α + k·x))]

    Args:
        Pj:          força aplicada (kN)
        x:           posição ao longo do cabo (m)
        alpha_total: soma dos desvios angulares até x (rad)
        mu:          coef. de atrito (0.2 para bainhas metálicas)
        k:           coef. de perdas parasitas (0.002 /m)

    Returns:
        Perda ΔP(x) em kN.
    """
    return Pj * (1 - math.exp(-(mu * alpha_total + k * x)))


def anchor_slip_loss(Aps: float, Eps: float, dA: float, L: float,
                     n_anchors: int = 2) -> float:
    """
    Perda por acomodação da ancoragem — Eq. 11.5; §9.6.3.3.2.3.
    ΔPanc = n_anchors · Aps·Eps·ΔA / L

    Args:
        Aps:       área da armadura (m²)
        Eps:       módulo de elasticidade (kN/m² = kPa)
        dA:        deslocamento de acomodação (m)
        L:         comprimento do cabo (m)
        n_anchors: 1 (uma extremidade) ou 2 (ambas)

    Returns:
        ΔPanc em kN (modelo aproximado, perda constante ao longo do cabo).
    """
    return n_anchors * Aps * Eps * dA / L


def elastic_shortening_loss(Aps: float, alpha_p: float,
                            sigma_c: float, n_cables: int) -> float:
    """
    Perda por encurtamento elástico do concreto — Eq. 11.7; §9.6.3.3.2.1.
    ΔPenc = αp·Aps·σc·(n-1)/(2n)

    Args:
        Aps:      área total da armadura (m²)
        alpha_p:  Eps / Eci
        sigma_c:  tensão no concreto na fibra do cabo (kN/m² = kPa)
        n_cables: número de cabos protendidos sequencialmente

    Returns:
        ΔPenc em kN.
    """
    if n_cables < 2:
        return 0.0
    return alpha_p * Aps * sigma_c * (n_cables - 1) / (2 * n_cables)


def immediate_losses(beam, profile, Pj, x):
    """Combina T10.1, T10.2, T10.3. Retorna Pt(x). Implementar T10.4."""
    raise NotImplementedError("Implementar T10.4")


# =============================================================================
# PERDAS PROGRESSIVAS — §9.6.3.4 (modelo simplificado §9.6.3.4.3)
# =============================================================================

def progressive_losses_simplified(Pt: float, sigma_c_p0g: float,
                                   alpha_p: float, phi: float) -> float:
    """
    Perdas progressivas — modelo simplificado para aço RB — Eq. 11.9.

    Δσp/σp0 = (1/100) · {7,4 + (αp/18,7) · φ^1,07 · (3 + σc,p0g)}

    Args:
        Pt:          força após perdas imediatas (kN)
        sigma_c_p0g: tensão no concreto adjacente ao cabo (MPa, positiva se compressão)
        alpha_p:     Eps / Eci
        phi:         coef. de fluência φ(t∞, t0)

    Returns:
        Perda ΔP em kN.
    """
    delta_pct = (1/100) * (7.4 + (alpha_p/18.7) * phi**1.07 * (3 + sigma_c_p0g))
    return Pt * delta_pct


def total_losses(beam, profile, Pj, **kwargs):
    """Encadeamento completo. Retorna arrays Pt(x), Ps(x). Implementar T10.6."""
    raise NotImplementedError("Implementar T10.6")


def iterate_losses(beam, profile, Pj, tol=0.01, max_iter=10):
    """Iteração até convergência. Implementar T10.7."""
    raise NotImplementedError("Implementar T10.7")
