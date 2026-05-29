"""
Página 7 — Verificaciones ELU y ELS

Tres pestañas:
  · ELU — Flexión:     MRd vs Msd en secciones críticas
  · ELS — Tensiones:   verificación de tensiones en fibras (ELS-D, ELS-DP)
  · ELS — Flechas:     flecha total con fluencia (ELS-DEF)
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.components.state import guardar_estado, mostrar_barra_lateral, obtener_estado
from app.components.plots import graficar_tensiones_fibras, COLORES
from app.components.tables import (
    tabla_verificacion_elu,
    tabla_verificacion_tensiones,
)

st.set_page_config(
    page_title="Verificaciones ELU/ELS — Viga Pretensada",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

mostrar_barra_lateral(etapa_actual="verificaciones")
estado = obtener_estado()

st.title("✅ Verificaciones ELU y ELS")
st.markdown("Verificaciones de seguridad y servicio según NBR 6118:2014.")

for etapa, nombre in [
    ("geometria_materiales", "1 — Geometría y Materiales"),
    ("cargas_apoyos",        "2 — Cargas y Apoyos"),
    ("magnel",               "4 — Diagrama de Magnel"),
]:
    if not estado.etapa_completada(etapa):
        st.warning(f"⚠️ Completa primero la etapa **{nombre}**.")

if estado.Pj is None:
    st.error("Pj no determinado. Completa el Diagrama de Magnel.")
    st.stop()

st.divider()

try:
    from src.uls_flexure import MRd_simplified, Mlim_rectangular
    from src.stress_check import stresses_at_section, check_stresses
    from src.stress_limits import stress_limits
    from src.loads import combine_actions, Md_ULS
    from src.sls import check_deflection

    conc    = estado.get_concrete()
    sec     = estado.get_section()
    loads   = estado.get_loads()
    support = estado.get_support()
    steel   = estado.get_steel()
    lim     = stress_limits(conc)

    Pj = estado.Pj
    Ps = Pj * estado.beta
    Pt = Pj * estado.alpha
    e  = estado.e_real or estado.e

    n_strands = estado.n_strands or 1
    Aps = n_strands * steel.Aps_unit   # m²
    dp  = sec.h - (sec.yb - e)         # distancia del topo al centroide de la armadura

    pp = sec.A * conc.gamma_concrete
    secciones_criticas = support.critical_sections()

    tab_elu, tab_els_t, tab_els_def = st.tabs([
        "⚡ ELU — Flexión",
        "🔍 ELS — Tensiones",
        "↔️ ELS — Flechas",
    ])

    # ════════════════════════════════════════════════════════════════════
    # PESTAÑA 1 — ELU FLEXIÓN
    # ════════════════════════════════════════════════════════════════════
    with tab_elu:
        st.subheader("Estado Límite Último — Flexión")
        st.markdown("Verificación MRd ≥ Msd según NBR 6118:2014 §17.3.2 y Eq. 9.1 del manual.")

        # Momento resistente
        MRd = MRd_simplified(dp, Aps, steel.fpd)
        Mlim = Mlim_rectangular(sec.b, dp, conc.fcd)

        col_r, col_l = st.columns(2)
        col_r.metric("MRd (simplificado, Eq. 9.1)",
                     f"{MRd:.2f} kN·m",
                     help="MRd = 0,82·dp·Aps·fpd")
        col_l.metric("Mlim (ductilidad, Eq. 9.3)",
                     f"{Mlim:.2f} kN·m",
                     help="Mlim = 0,25·b·dp²·fcd. Si MRd > Mlim, seción sobrearmada.")

        if MRd > Mlim:
            st.warning(
                f"⚠️ MRd ({MRd:.1f}) > Mlim ({Mlim:.1f}). "
                "La sección puede estar sobrearmada. Comprueba la ductilidad."
            )

        st.divider()
        st.subheader("Verificación por sección crítica")

        nomes_sec, MRd_vals, Msd_vals = [], [], []
        for x_c, tipo_c in secciones_criticas:
            Msw_c = abs(support.M_uniform(x_c, pp))
            Mgk_c = abs(support.M_uniform(x_c, loads.gk))
            Mqk_c = abs(support.M_uniform(x_c, loads.qk))
            Msd_c = Md_ULS(Msw_c + Mgk_c, Mqk_c)
            nomes_sec.append(f"x={x_c:.2f} m ({tipo_c})")
            MRd_vals.append(MRd)
            Msd_vals.append(Msd_c)

        df_elu = tabla_verificacion_elu(nomes_sec, MRd_vals, Msd_vals)
        st.dataframe(df_elu, use_container_width=True, hide_index=True)

        # Resumen visual
        if all(r >= 1.0 for r in [m / s if s > 0 else 999 for m, s in zip(MRd_vals, Msd_vals)]):
            st.success("✅ ELU a flexión **verificado** en todas las secciones críticas.")
        else:
            st.error("❌ ELU a flexión **no verificado** en al menos una sección. "
                     "Considera aumentar Pj, el número de cordones o la altura.")

        # dp y Aps
        st.caption(
            f"dp = h − (yb − e) = {sec.h:.3f} − ({sec.yb:.3f} − {e:.4f}) = **{dp:.4f} m**  |  "
            f"Aps = {n_strands} × {steel.Aps_unit_mm2:.1f} = **{Aps*1e6:.1f} mm²**"
        )

    # ════════════════════════════════════════════════════════════════════
    # PESTAÑA 2 — ELS TENSIONES
    # ════════════════════════════════════════════════════════════════════
    with tab_els_t:
        st.subheader("Estado Límite de Servicio — Tensiones en las fibras")
        st.markdown(
            "Verificación de σ_top y σ_bot en el hormigón para las combinaciones "
            "de carga de servicio (NBR 6118:2014 §17.2.4.3.2)."
        )

        # Calcular tensiones en la sección crítica para cada combinación
        x_c, _ = secciones_criticas[0]
        Msw_c = abs(support.M_uniform(x_c, pp))
        Mgk_c = abs(support.M_uniform(x_c, loads.gk))
        Mqk_c = abs(support.M_uniform(x_c, loads.qk))
        Mse_c = Msw_c + Mgk_c + Mqk_c

        combos = combine_actions(
            estado.prestress_level,
            Mgk_c + Msw_c, Mqk_c,
            loads.psi1, loads.psi2,
        )

        lim_transfer = stress_limits(conc, situation='transfer')
        lim_service  = stress_limits(conc, situation='service')
        if estado.prestress_level == 'completa':
            lim_ELS_D = stress_limits(conc, situation='service_ELS_D')
        else:
            lim_ELS_D = lim_service

        # Acto de transferencia (M = Msw)
        st_top, st_bot = stresses_at_section(Pt, e, Msw_c, sec)
        res_transfer = check_stresses(st_top, st_bot, lim_transfer, 'transfer')

        # Servicio (M = Mse rara)
        ss_top, ss_bot = stresses_at_section(Ps, e, Mse_c, sec)
        res_service = check_stresses(ss_top, ss_bot, lim_service, 'service')

        situaciones = [
            {"sigma_top": st_top, "sigma_bottom": st_bot},
            {"sigma_top": ss_top, "sigma_bottom": ss_bot},
        ]
        etiquetas_tension = ["Transferencia (Pt, Msw)", "Servicio (Ps, Mse)"]

        # Si hay combinaciones ELS adicionales
        for clave, Mels in combos.items():
            s_top, s_bot = stresses_at_section(Ps, e, abs(Mels), sec)
            if estado.prestress_level in ("completa", "limitada"):
                res_els = check_stresses(s_top, s_bot, lim_ELS_D, 'service')
            else:
                res_els = check_stresses(s_top, s_bot, lim_service, 'service')
            situaciones.append({"sigma_top": s_top, "sigma_bottom": s_bot})
            etiquetas_tension.append(f"ELS — {clave} (kN·m={Mels:.1f})")

        resultados_check = [
            check_stresses(s["sigma_top"], s["sigma_bottom"],
                           lim_transfer if "Transf" in et else lim_service,
                           'transfer' if "Transf" in et else 'service')
            for s, et in zip(situaciones, etiquetas_tension)
        ]
        # Fix check for transfer
        resultados_check[0] = res_transfer
        resultados_check[1] = res_service

        df_tens = tabla_verificacion_tensiones(resultados_check, etiquetas_tension)
        st.dataframe(df_tens, use_container_width=True, hide_index=True)

        fig_tensiones = graficar_tensiones_fibras(situaciones, etiquetas_tension)
        st.plotly_chart(fig_tensiones, use_container_width=True)

        # Límites mostrados
        st.markdown("**Límites admisibles:**")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"**Acto de transferencia:**  \n"
                f"Compresión: ≥ {lim_transfer.ftc:.2f} MPa  \n"
                f"Tracción: ≤ {lim_transfer.ftt:.2f} MPa"
            )
        with c2:
            st.markdown(
                f"**En servicio:**  \n"
                f"Compresión: ≥ {lim_service.fsc:.2f} MPa  \n"
                f"Tracción: ≤ {lim_service.fst:.2f} MPa"
            )

        todos_ok = all(r.ok for r in resultados_check)
        if todos_ok:
            st.success("✅ Verificaciones de tensiones **aprobadas** en todas las combinaciones.")
        else:
            st.error("❌ Al menos una verificación de tensión **no aprobada**. "
                     "Revisa Pj, e o el nivel de pretensado.")

    # ════════════════════════════════════════════════════════════════════
    # PESTAÑA 3 — ELS FLECHAS
    # ════════════════════════════════════════════════════════════════════
    with tab_els_def:
        st.subheader("Estado Límite de Servicio — Flechas (ELS-DEF)")
        st.markdown(
            "Verificación de flechas a largo plazo incluyendo fluencia. "
            "Límites: L/250 (criterio general) y L/350 (con elementos frágiles)."
        )

        phi = estado.phi_creep
        col_p, col_res = st.columns([1, 1.5])
        with col_p:
            phi_usr = st.number_input(
                "Coeficiente de fluencia φ", 0.5, 4.0, float(phi), 0.1,
                format="%.2f", key="_ni_phi_def",
                help="φ(t∞, t0) según NBR 6118:2014 §8.2.11.",
            )

        try:
            res_def = check_deflection(
                section=sec,
                concrete=conc,
                loads=loads,
                Ps=Ps,
                e_max=e,
                L=estado.L,
                phi=phi_usr,
                profile_type=estado.profile_type,
                alpha_E=estado.alpha_E,
            )

            with col_res:
                c1, c2, c3 = st.columns(3)
                c1.metric("Flecha inmediata δ_i",
                           f"{res_def.delta_immediate*100:.2f} cm",
                           help="Flecha bajo cargas pp + gk + ψ2·qk (m).")
                c2.metric("Contraflecha δ_p",
                           f"{res_def.delta_prestress*100:.2f} cm",
                           help="Levantamiento por pretensado.")
                c3.metric("Flecha total δ_total",
                           f"{res_def.delta_long_term*100:.2f} cm",
                           help="Flecha a largo plazo con fluencia.")

            st.divider()
            import pandas as pd
            df_def = pd.DataFrame([
                ("Flecha inmediata δ_i",       f"{res_def.delta_immediate*100:.3f}",  "cm", "—"),
                ("Contraflecha pretensado δ_p", f"{res_def.delta_prestress*100:.3f}", "cm", "—"),
                ("Flecha total a largo plazo",  f"{res_def.delta_long_term*100:.3f}",  "cm",
                 "✅ OK" if res_def.ok_L250 else "❌ FALLO"),
                ("Límite L/250",                f"{res_def.limit_L250*100:.3f}",       "cm",
                 "—"),
                ("Límite L/350 (elem. frágiles)", f"{res_def.limit_L350*100:.3f}",    "cm",
                 "—"),
            ], columns=["Descripción", "Valor", "Unidad", "Estado"])
            st.dataframe(df_def, use_container_width=True, hide_index=True)

            if res_def.ok_L250:
                st.success(
                    f"✅ ELS-DEF **verificado** (δ={res_def.delta_long_term*100:.2f} cm "
                    f"≤ L/250 = {res_def.limit_L250*100:.2f} cm)."
                )
            else:
                st.error(
                    f"❌ ELS-DEF **no verificado** (δ={res_def.delta_long_term*100:.2f} cm "
                    f"> L/250 = {res_def.limit_L250*100:.2f} cm). "
                    "Aumenta Ps, e o la rigidez de la sección."
                )
            if not res_def.ok_L350:
                st.warning(
                    f"⚠️ Para elementos con revestimientos frágiles: δ > L/350 = "
                    f"{res_def.limit_L350*100:.2f} cm."
                )

        except NotImplementedError:
            st.warning("Cálculo de flechas no disponible para este tipo de apoyo.")

    st.divider()
    if st.button("💾 Marcar verificaciones como completadas →",
                 type="primary", use_container_width=False):
        estado.marcar_completada("verificaciones")
        guardar_estado(estado)
        st.success("Verificaciones guardadas. Continúa en Página 8 — Informe Final.")

except NotImplementedError:
    st.warning("El tipo de apoyo seleccionado no soporta este cálculo.")
except Exception as err:
    st.error(f"Error en las verificaciones: {err}")

guardar_estado(estado)
