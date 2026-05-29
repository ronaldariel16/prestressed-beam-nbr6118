"""
materials.py
Concreto e aço conforme NBR 6118:2014.
Escopo: concretos até C50.
"""

from dataclasses import dataclass
from typing import Optional


# =============================================================================
# CONCRETO — NBR 6118:2014 §8.2
# =============================================================================

@dataclass
class Concrete:
    """
    Concreto estrutural conforme NBR 6118:2014.

    Args:
        fck:   resistência característica à compressão (MPa)
        fckj:  resistência na idade j (MPa). Se None, assume = fck.
        gamma_c: coeficiente de ponderação (default 1.4)
        gamma_concrete: peso específico do concreto armado (kN/m³, default 25)
    """
    fck: float
    fckj: Optional[float] = None
    gamma_c: float = 1.4
    gamma_concrete: float = 25.0

    def __post_init__(self):
        if self.fck > 50:
            raise ValueError(f"Escopo limitado a C50. Recebido fck={self.fck} MPa.")
        if self.fckj is None:
            self.fckj = self.fck

    @property
    def fcd(self) -> float:
        """Tensão de cálculo (MPa)."""
        return self.fck / self.gamma_c

    @property
    def fct_m(self) -> float:
        """Resistência média à tração — §8.2.5 (MPa). Vale para fck ≤ 50."""
        return 0.3 * self.fck ** (2/3)

    @property
    def fct_mj(self) -> float:
        """Resistência média à tração na idade j (MPa)."""
        return 0.3 * self.fckj ** (2/3)

    def Eci(self, alpha_E: float = 1.0) -> float:
        """
        Módulo de elasticidade tangente inicial — §8.2.8 (MPa).
        αE: fator do agregado (1.0 granito, 0.9 basalto, 0.7 calcário, 0.5 arenito).
        """
        return alpha_E * 5600 * self.fck**0.5

    def Ecs(self, alpha_E: float = 1.0) -> float:
        """Módulo de elasticidade secante — §8.2.8 (MPa)."""
        alpha_i = 0.8 + 0.2 * self.fck / 80
        alpha_i = min(alpha_i, 1.0)
        return alpha_i * self.Eci(alpha_E)

    def Eci_j(self, alpha_E: float = 1.0) -> float:
        """Módulo tangente na idade j — §8.2.8."""
        return alpha_E * 5600 * self.fckj**0.5

    def phi(self, t_inf: float, t0: float, h_fic: float, humidity: float) -> float:
        """
        Coeficiente de fluência φ(t∞, t0) — §8.2.11.

        Implementar conforme T9.3 (placeholder).
        Pode usar Tabela 8.2 para valores aproximados.
        """
        raise NotImplementedError("Implementar conforme T9.3")


# =============================================================================
# AÇO DE PROTENSÃO — NBR 6118:2014 §8.4 e Tabela 3.1 do manual
# =============================================================================

# Catálogo de cordoalhas CP-190 RB (ArcelorMittal, conforme manual Tab. 3.1)
# Chave: diâmetro nominal (mm)
# Valores: (área_mm2, P_ruptura_kN, P_escoamento_kN, fios)
CP_190_RB_CATALOG = {
    # 3 fios
    6.5:  {'A_mm2': 21.5, 'Pptk_kN': 40.8, 'Ppyk_kN': 36.7, 'fios': 3},
    7.6:  {'A_mm2': 30.0, 'Pptk_kN': 57.0, 'Ppyk_kN': 51.3, 'fios': 3},
    8.8:  {'A_mm2': 37.6, 'Pptk_kN': 71.4, 'Ppyk_kN': 64.3, 'fios': 3},
    9.6:  {'A_mm2': 46.2, 'Pptk_kN': 87.7, 'Ppyk_kN': 78.9, 'fios': 3},
    11.1: {'A_mm2': 65.7, 'Pptk_kN': 124.8, 'Ppyk_kN': 112.3, 'fios': 3},
    # 7 fios
    9.5:  {'A_mm2': 54.8, 'Pptk_kN': 104.3, 'Ppyk_kN': 93.9, 'fios': 7},
    12.7: {'A_mm2': 98.7, 'Pptk_kN': 187.3, 'Ppyk_kN': 168.6, 'fios': 7},
    15.2: {'A_mm2': 140.0, 'Pptk_kN': 265.8, 'Ppyk_kN': 239.2, 'fios': 7},
}


@dataclass
class PrestressSteel:
    """
    Aço de protensão conforme NBR 6118:2014 §8.4 e Tabela 3.1 do manual.

    Args:
        type_:    tipo do aço (default 'CP-190 RB')
        diameter: diâmetro nominal (mm)
        gamma_s:  coeficiente de ponderação (default 1.15)
    """
    type_: str = 'CP-190 RB'
    diameter: float = 15.2
    gamma_s: float = 1.15
    Eps: float = 200_000.0  # MPa, §8.4

    def __post_init__(self):
        if self.diameter not in CP_190_RB_CATALOG:
            raise ValueError(
                f"Diâmetro {self.diameter} mm não está no catálogo. "
                f"Disponíveis: {list(CP_190_RB_CATALOG.keys())}"
            )
        props = CP_190_RB_CATALOG[self.diameter]
        self.Aps_unit_mm2 = props['A_mm2']
        self.Pptk_unit = props['Pptk_kN']  # kN por cordoalha
        self.Ppyk_unit = props['Ppyk_kN']  # kN por cordoalha
        self.fios = props['fios']

    @property
    def Aps_unit(self) -> float:
        """Área por cordoalha (m²)."""
        return self.Aps_unit_mm2 * 1e-6

    @property
    def fptk(self) -> float:
        """Resistência característica à ruptura (MPa) — para CP-190 = 1900."""
        return 1900.0

    @property
    def fpyk(self) -> float:
        """Tensão característica a 1% de deformação (MPa)."""
        # CP-190: fpyk ≈ 0.9 · fptk = 1710 MPa
        return self.Ppyk_unit / self.Aps_unit_mm2 * 1000

    @property
    def fpd(self) -> float:
        """Tensão de cálculo (MPa)."""
        return self.fpyk / self.gamma_s

    def Pj_lim_unit(self) -> float:
        """
        Força máxima de protensão por cordoalha — NBR 6118 §9.6.1.2.
        Para pós-tração com cordoalha RB: min(0.74·Pptk; 0.85·Ppyk).
        """
        return min(0.74 * self.Pptk_unit, 0.85 * self.Ppyk_unit)


# =============================================================================
# AÇO PASSIVO — CA-50
# =============================================================================

@dataclass
class PassiveSteel:
    """Aço passivo CA-50 (default) conforme NBR 6118:2014."""
    category: str = 'CA-50'
    gamma_s: float = 1.15
    Es: float = 210_000.0  # MPa

    @property
    def fyk(self) -> float:
        return 500.0  # MPa para CA-50

    @property
    def fyd(self) -> float:
        return self.fyk / self.gamma_s
