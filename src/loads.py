"""
loads.py
Cargas e combinações de ações conforme NBR 6118:2014 §11.7 e §11.8 (Tab. 11.4 e 13.4).
"""

from dataclasses import dataclass
from typing import Dict


# Tabela 11.4 NBR 6118 — Coeficientes ψ por uso da edificação
PSI_TABLE = {
    'residencial':       {'psi0': 0.5, 'psi1': 0.4, 'psi2': 0.3},
    'comercial':         {'psi0': 0.7, 'psi1': 0.6, 'psi2': 0.4},
    'biblioteca_arquivo':{'psi0': 0.8, 'psi1': 0.7, 'psi2': 0.6},
    'oficina_garagem':   {'psi0': 0.7, 'psi1': 0.6, 'psi2': 0.4},
    'vento':             {'psi0': 0.6, 'psi1': 0.3, 'psi2': 0.0},
    'temperatura':       {'psi0': 0.6, 'psi1': 0.5, 'psi2': 0.3},
}


@dataclass
class Loads:
    """
    Cargas características.

    Args:
        gk:    cargas permanentes características, sem peso próprio (kN/m)
        qk:    sobrecarga característica (kN/m)
        usage: uso da edificação (ver PSI_TABLE)
    """
    gk: float
    qk: float
    usage: str = 'residencial'

    def __post_init__(self):
        if self.usage not in PSI_TABLE:
            raise ValueError(f"Uso '{self.usage}' não previsto. Opções: {list(PSI_TABLE.keys())}")

    @property
    def psi1(self) -> float:
        return PSI_TABLE[self.usage]['psi1']

    @property
    def psi2(self) -> float:
        return PSI_TABLE[self.usage]['psi2']

    def self_weight(self, section, gamma_concrete: float = 25.0) -> float:
        """Peso próprio da viga (kN/m)."""
        return section.A * gamma_concrete


def combine_actions(level: str, Mgk: float, Mqk: float, psi1: float, psi2: float) -> Dict[str, float]:
    """
    Combinações de ações para verificação dos ELS conforme nível de protensão.

    Tabela 13.4 NBR 6118:2014:
        - Completa:  ELS-F = Rara (γq=1), ELS-D = Frequente (ψ1)
        - Limitada:  ELS-F = Frequente (ψ1), ELS-D = Quase Permanente (ψ2)
        - Parcial:   ELS-W = Frequente (ψ1)

    Args:
        level: 'completa' | 'limitada' | 'parcial'
        Mgk:   momento devido às cargas permanentes (incluindo PP), valor característico
        Mqk:   momento devido à sobrecarga, valor característico
        psi1, psi2: coeficientes de redução

    Returns:
        dict com 'Mse_F' (para ELS-F) e 'Mse_D' (para ELS-D), em kN·m.
    """
    if level == 'completa':
        return {
            'Mse_F': Mgk + Mqk,            # Rara
            'Mse_D': Mgk + psi1 * Mqk,     # Frequente
        }
    elif level == 'limitada':
        return {
            'Mse_F': Mgk + psi1 * Mqk,     # Frequente
            'Mse_D': Mgk + psi2 * Mqk,     # Quase Permanente
        }
    elif level == 'parcial':
        return {
            'Mse_W': Mgk + psi1 * Mqk,     # Frequente (ELS-W)
        }
    else:
        raise ValueError(f"Nível '{level}' inválido. Use 'completa', 'limitada' ou 'parcial'.")


def Md_ULS(Mgk: float, Mqk: float, gamma_g: float = 1.4, gamma_q: float = 1.4) -> float:
    """
    Momento de cálculo no ELU — combinação última normal §11.7.
    Md = γg·Mgk + γq·Mqk
    """
    return gamma_g * Mgk + gamma_q * Mqk
