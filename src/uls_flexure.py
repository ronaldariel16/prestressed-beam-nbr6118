"""
uls_flexure.py
Verificação do Estado Limite Último à Flexão — Capítulo 9 do manual.
Modelo aproximado conforme Eq. 9.1 (Torii, 2019).
Implementar conforme T8.x do tasks.md.
"""


def MRd_simplified(dp: float, Aps: float, fpd: float) -> float:
    """
    Momento resistente — Eq. 9.1.
    MRd = 0,82·dp·Aps·fpd

    Args:
        dp:  distância do topo ao centroide das armaduras ativas (m)
        Aps: área da armadura ativa (m²)
        fpd: tensão de cálculo (MPa = kN/m² · 1000)

    Returns:
        MRd em kN·m.
    """
    return 0.82 * dp * Aps * (fpd * 1000)  # MPa → kN/m²


def Mlim_rectangular(b: float, dp: float, fcd: float) -> float:
    """
    Momento limite para ductilidade — Eq. 9.3 (caso retangular).
    Mlim = 0,25·b·dp²·fcd
    """
    return 0.25 * b * dp**2 * (fcd * 1000)


def MRd_with_passive(dp, Aps, fpd, d, As, fyd):
    """MRd com armadura passiva adicional — Eq. 9.13. Implementar T8.4."""
    raise NotImplementedError("Implementar T8.4")


def additional_passive_steel(Msd, MRd_p, dp, d, fyd):
    """Calcula As adicional necessária. Implementar T8.4."""
    raise NotImplementedError("Implementar T8.4")


def check_ULS(beam, x):
    """Verificação completa do ELU em x. Implementar T8.5."""
    raise NotImplementedError("Implementar T8.5")
