"""
presizing.py
Pré-dimensionamento da seção transversal — Capítulo 6 do manual Torii (2020).
NBR 6118:2014.

Critério geral:  Eqs. 6.9 e 6.10 — módulos mínimos eliminando P e e das
                 4 condições de tensão (ato e serviço).

Derivação das fórmulas (seção simétrica zt = zb = z):
  C1+C3 → zt_req = (Mse − η·Msw) / (η·ftt + |fsc|)   [fibra superior]
  C2+C4 → zb_req = (Mse − η·Msw) / (fst + η·|ftc|)   [fibra inferior]

Critério simpl.: Eq. 6.13 — z_req = Ms / |ftc|
  Usa o limite de compressão no ato de transferência (|ftc| = 0,7·fckj),
  mais restritivo que |fsc| quando fckj < fck.
"""
import math


def presize_general(Mse: float, Msw: float, eta: float, limits) -> tuple:
    """
    Critério geral — Eqs. 6.9 e 6.10 do manual.

    Combina as condições de serviço (C1, C2) e do ato de transferência (C3, C4)
    para determinar os módulos seccionais mínimos sem conhecer P nem e.

    Derivação:
      zt_req: combina C1 (σ_top_serv ≥ fsc) + C3 (σ_top_ato ≤ ftt)
              zt ≥ delta_M / (η·ftt + |fsc|)
      zb_req: combina C2 (σ_bot_serv ≤ fst) + C4 (σ_bot_ato ≥ ftc)
              zb ≥ delta_M / (fst + η·|ftc|)

    Args:
        Mse:    momento total de serviço na seção crítica (kN·m, positivo)
        Msw:    momento do peso próprio na seção crítica (kN·m, positivo)
        eta:    Ps/Pt — razão de perdas (≈ 0,83)
        limits: instância de StressLimits (tensões em MPa)

    Returns:
        (zt_req, zb_req) em m³ — módulos seccionais mínimos necessários.
    """
    ftt_kPa = limits.ftt * 1000.0          # tracção no ato (> 0)
    fst_kPa = limits.fst * 1000.0          # tracção em serviço (≥ 0)
    ftc_abs_kPa = abs(limits.ftc) * 1000.0  # compressão no ato  (> 0)
    fsc_abs_kPa = abs(limits.fsc) * 1000.0  # compressão em serviço (> 0)

    delta_M = max(Mse - eta * Msw, 0.0)

    # Eq. 6.10 — fibra superior: C1 (serv. topo) + C3 (ato topo)
    den_t = eta * ftt_kPa + fsc_abs_kPa    # η·ftt + |fsc|
    zt_req = delta_M / den_t if den_t > 1e-12 else 0.0

    # Eq. 6.9 — fibra inferior: C2 (serv. fundo) + C4 (ato fundo)
    den_b = fst_kPa + eta * ftc_abs_kPa    # fst + η·|ftc|
    zb_req = delta_M / den_b if den_b > 1e-12 else 0.0

    return zt_req, zb_req


def presize_simplified(Ms: float, eta: float, limits) -> tuple:
    """
    Critério simplificado — Eq. 6.13 do manual.

    Estimativa conservadora baseada no momento de cargas variáveis + permanentes
    adicionais (Ms = Mse − Msw) e no limite de compressão no ato de transferência.

    Usa |ftc| = 0,7·fckj (limite no ato) e não |fsc| = 0,7·fck (serviço),
    pois fckj ≤ fck → |ftc| ≤ |fsc|, tornando |ftc| o denominador limitante.

    Args:
        Ms:     momento de cargas sem peso próprio (kN·m) = Mse − Msw
        eta:    Ps/Pt (não utilizado, mantido por compatibilidade)
        limits: instância de StressLimits

    Returns:
        (zt_req, zb_req) em m³ — iguais para seção simétrica.
    """
    ftc_abs_kPa = abs(limits.ftc) * 1000.0  # |ftc| = 0,7·fckj (kPa)
    z_req = Ms / ftc_abs_kPa if ftc_abs_kPa > 1e-12 else 0.0
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
