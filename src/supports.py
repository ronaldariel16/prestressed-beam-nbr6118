"""
supports.py
Biblioteca de casos de apoio para cálculo de momentos fletores.
Cada classe expõe M(x) para diferentes carregamentos.
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Tuple
import numpy as np


class BeamSupport(ABC):
    """Classe base abstrata para condições de apoio."""

    def __init__(self, L: float):
        if L <= 0:
            raise ValueError("L deve ser positivo")
        self.L = L

    @abstractmethod
    def M_uniform(self, x: float, q: float) -> float:
        """Momento fletor (kN·m) em x devido à carga uniforme q (kN/m)."""
        ...

    @abstractmethod
    def critical_sections(self) -> List[Tuple[float, str]]:
        """Lista de seções críticas: [(x, 'tipo'), ...] onde tipo ∈ {'M+', 'M-'}."""
        ...

    def M_array(self, q: float, n_points: int = 21) -> Tuple[np.ndarray, np.ndarray]:
        """Retorna arrays (x, M) para plotagem."""
        x = np.linspace(0, self.L, n_points)
        M = np.array([self.M_uniform(xi, q) for xi in x])
        return x, M


class SimplySupported(BeamSupport):
    """Viga simplesmente apoiada."""

    def M_uniform(self, x: float, q: float) -> float:
        return q * x * (self.L - x) / 2

    def critical_sections(self) -> List[Tuple[float, str]]:
        return [(self.L / 2, 'M+')]


class FixedFixed(BeamSupport):
    """Viga biengastada."""

    def M_uniform(self, x: float, q: float) -> float:
        # M(x) = q·(6Lx - 6x² - L²)/12
        return q * (6 * self.L * x - 6 * x**2 - self.L**2) / 12

    def critical_sections(self) -> List[Tuple[float, str]]:
        # Negativo nos apoios, positivo no meio
        return [(0, 'M-'), (self.L, 'M-'), (self.L / 2, 'M+')]


class FixedPinned(BeamSupport):
    """Viga engastada-apoiada (engaste em x=0, apoio em x=L)."""

    def M_uniform(self, x: float, q: float) -> float:
        # Reações: V0 = 5qL/8, ML = 0, M0 = -qL²/8
        # Implementar conforme T2.4
        raise NotImplementedError("Implementar T2.4")

    def critical_sections(self) -> List[Tuple[float, str]]:
        # Negativo no engaste (x=0), positivo em x = 5L/8
        return [(0, 'M-'), (5 * self.L / 8, 'M+')]


class Cantilever(BeamSupport):
    """Viga em balanço (engaste em x=0, livre em x=L)."""

    def M_uniform(self, x: float, q: float) -> float:
        return -q * (self.L - x)**2 / 2

    def critical_sections(self) -> List[Tuple[float, str]]:
        return [(0, 'M-')]


class TwoSpanContinuous(BeamSupport):
    """Viga contínua de dois vãos L1 e L2."""

    def __init__(self, L1: float, L2: float):
        if L1 <= 0 or L2 <= 0:
            raise ValueError("L1 e L2 devem ser positivos")
        self.L1 = L1
        self.L2 = L2
        super().__init__(L=L1 + L2)

    def M_uniform(self, x: float, q: float) -> float:
        # Implementar via método dos três momentos — T2.6
        raise NotImplementedError("Implementar T2.6")

    def critical_sections(self) -> List[Tuple[float, str]]:
        # Apoio central (M-) e meios dos vãos (M+)
        # Implementar T2.6 para calcular posições exatas
        raise NotImplementedError("Implementar T2.6")


class CustomSupport(BeamSupport):
    """
    Apoio customizado: usuário fornece função M(x) ou array (x, M).
    Útil para casos não tabelados ou resultados de software externo.
    """

    def __init__(self, L: float, M_function: Callable[[float], float],
                 critical: List[Tuple[float, str]]):
        super().__init__(L)
        self._M = M_function
        self._critical = critical

    def M_uniform(self, x: float, q: float) -> float:
        # Para CustomSupport, q é usado apenas como escalar.
        # O usuário define M(x) por unidade de carga ou direto.
        return self._M(x) * q

    def critical_sections(self) -> List[Tuple[float, str]]:
        return self._critical
