"""
geometry.py
Propriedades geométricas de seções retangulares.
Referência: Resistência dos Materiais (clássica).
"""

from dataclasses import dataclass


@dataclass
class RectangularSection:
    """
    Seção retangular b x h.

    Atributos calculados:
        A:  área (m²)
        I:  momento de inércia em relação ao eixo neutro (m⁴)
        yt: distância do centroide à fibra superior (m)
        yb: distância do centroide à fibra inferior (m)
        zt: módulo seccional fibra superior (m³)
        zb: módulo seccional fibra inferior (m³)
    """
    b: float  # largura (m)
    h: float  # altura (m)

    def __post_init__(self):
        if self.b <= 0 or self.h <= 0:
            raise ValueError("b e h devem ser positivos")

    @property
    def A(self) -> float:
        return self.b * self.h

    @property
    def I(self) -> float:
        return self.b * self.h**3 / 12

    @property
    def yt(self) -> float:
        return self.h / 2

    @property
    def yb(self) -> float:
        return self.h / 2

    @property
    def zt(self) -> float:
        return self.I / self.yt

    @property
    def zb(self) -> float:
        return self.I / self.yb

    def __repr__(self) -> str:
        return (
            f"RectangularSection(b={self.b:.3f} m, h={self.h:.3f} m)\n"
            f"  A  = {self.A:.4f} m²\n"
            f"  I  = {self.I:.6e} m⁴\n"
            f"  zt = zb = {self.zt:.6e} m³"
        )
