"""
example_01_simply_supported.py

Adaptação do Exemplo 5.2.1 do manual (Torii, 2020) para seção retangular.

Original (duplo T): A=44e4 mm², I=2.32e10 mm⁴, yb=473mm, yt=252mm
Aqui usamos seção retangular equivalente: b=0.30 m, h=0.80 m

Dados:
- L = 10 m, simplesmente apoiada
- gk = 20 kN/m, qk = 25 kN/m
- fck = 50 MPa, fckj = 30 MPa
- Pj = 1450 kN, e = 0.39 m
- Protensão completa, comercial
"""

from src.geometry import RectangularSection
from src.materials import Concrete, PrestressSteel
from src.supports import SimplySupported
from src.loads import Loads
from src.stress_limits import stress_limits
from src.stress_check import stresses_at_section, check_stresses


def main():
    # 1. Geometria
    section = RectangularSection(b=0.30, h=0.80)
    print(section)
    print()

    # 2. Materiais
    concrete = Concrete(fck=50, fckj=30)
    steel = PrestressSteel(type_='CP-190 RB', diameter=15.2)
    print(f"Concrete: fck={concrete.fck}, fct_m={concrete.fct_m:.2f} MPa, "
          f"Ecs={concrete.Ecs()/1000:.0f} GPa")
    print(f"Steel: {steel.type_} φ{steel.diameter} mm, "
          f"Aps_unit={steel.Aps_unit_mm2} mm², Pj_lim={steel.Pj_lim_unit():.1f} kN")
    print()

    # 3. Apoio e cargas
    support = SimplySupported(L=10.0)
    loads = Loads(gk=20, qk=25, usage='comercial')
    qw = loads.self_weight(section)  # peso próprio
    print(f"Peso próprio: {qw:.2f} kN/m")
    print()

    # 4. Momentos no meio do vão
    x_mid = 5.0
    Msw = support.M_uniform(x_mid, qw)
    Mgk = support.M_uniform(x_mid, qw + loads.gk)
    Mqk = support.M_uniform(x_mid, loads.qk)
    Mse = Mgk + Mqk  # combinação rara (protensão completa)
    print(f"Msw = {Msw:.1f} kN·m")
    print(f"Mse = {Mse:.1f} kN·m (combinação rara)")
    print()

    # 5. Tensões limites
    limits = stress_limits(concrete)
    print(f"Limites: ftt={limits.ftt:.2f}, ftc={limits.ftc:.1f}, "
          f"fst={limits.fst:.2f}, fsc={limits.fsc:.1f} MPa")
    print()

    # 6. Verificação de tensões — protensão simplificada
    Pj = 1450.0
    e = 0.39
    Pt = 0.90 * Pj
    Ps = 0.75 * Pj

    # No ato da protensão (com Msw)
    sigma_t_top, sigma_t_bot = stresses_at_section(Pt, e, Msw, section)
    res_transfer = check_stresses(sigma_t_top, sigma_t_bot, limits, 'transfer')
    print("--- ATO DA PROTENSÃO (meio do vão) ---")
    print(f"σ_top    = {sigma_t_top:7.2f} MPa  {'OK' if res_transfer.passes_top else 'FALHA'}")
    print(f"σ_bottom = {sigma_t_bot:7.2f} MPa  {'OK' if res_transfer.passes_bottom else 'FALHA'}")

    # Em serviço (com Mse)
    sigma_s_top, sigma_s_bot = stresses_at_section(Ps, e, Mse, section)
    res_service = check_stresses(sigma_s_top, sigma_s_bot, limits, 'service')
    print("--- EM SERVIÇO (meio do vão) ---")
    print(f"σ_top    = {sigma_s_top:7.2f} MPa  {'OK' if res_service.passes_top else 'FALHA'}")
    print(f"σ_bottom = {sigma_s_bot:7.2f} MPa  {'OK' if res_service.passes_bottom else 'FALHA'}")


if __name__ == '__main__':
    main()
