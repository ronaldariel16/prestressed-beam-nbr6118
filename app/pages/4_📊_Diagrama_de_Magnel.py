"""
Página 4 — Diagrama de Magnel

Construye el diagrama de Magnel con las 4 restricciones lineales en el plano
(e, 1/Ps). Identifica la región factible y permite seleccionar el punto de
diseño de forma automática o manual.
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
from app.components.plots import _hex_a_rgba, COLORES

st.set_page_config(
    page_title="Diagrama de Magnel — Viga Pretensada",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

mostrar_barra_lateral(etapa_actual="magnel")
estado = obtener_estado()

st.title("📊 Diagrama de Magnel")
st.markdown(
    "Región factible en el plano **(e, 1/Ps)** a partir de las 4 condiciones "
    "de tensión en las fibras extremas — Eq. 7.1 del manual."
)

for etapa, nombre in [
    ("geometria_materiales", "1 — Geometría y Materiales"),
    ("cargas_apoyos",        "2 — Cargas y Apoyos"),
]:
    if not estado.etapa_completada(etapa):
        st.warning(f"⚠️ Completa primero la etapa **{nombre}**.")

st.divider()

try:
    from src.magnel import feasible_region, magnel_lines, select_design_point
    from src.stress_limits import stress_limits

    conc    = estado.get_concrete()
    sec     = estado.get_section()
    loads   = estado.get_loads()
    support = estado.get_support()

    pp = sec.A * conc.gamma_concrete
    x_crit, _ = support.critical_sections()[0]
    Msw = abs(support.M_uniform(x_crit, pp))
    Mgk = abs(support.M_uniform(x_crit, loads.gk))
    Mqk = abs(support.M_uniform(x_crit, loads.qk))
    Mse = Msw + Mgk + Mqk
    eta = estado.beta / estado.alpha if estado.alpha > 0 else 0.83
    lim = stress_limits(conc)

    col_param, col_diag = st.columns([1, 2], gap="medium")

    with col_param:
        st.subheader("Parámetros del diagrama")
        cover = st.number_input(
            "Cobertura nominal c (m)", 0.02, 0.15, 0.05, 0.01,
            format="%.3f", key="_ni_cover_magnel",
            help="Distancia del eje del cable a la fibra inferior (m). "
                 "Define el límite geométrico superior de e.",
        )
        e_max_geo = sec.yb - cover
        e_min_val = st.number_input(
            "Excentricidad mínima e_min (m)",
            0.0, float(e_max_geo * 0.5), 0.0, 0.01,
            format="%.3f", key="_ni_emin_magnel",
        )
        Ps_min_kN = st.number_input(
            "Ps mínimo a graficar (kN)", 50.0, 2000.0, 100.0, 50.0,
            format="%.0f", key="_ni_Psmin_magnel",
            help="Define el eje vertical: se grafica hasta 1/Ps_min.",
        )
        invP_max = 1.0 / Ps_min_kN

        st.info(f"Límite geométrico: **e_max = yb − c = {e_max_geo:.4f} m**")

        st.divider()
        st.subheader("Momentos en la sección crítica")
        st.markdown(
            f"- **Msw** = {Msw:.2f} kN·m  \n"
            f"- **Mse** = {Mse:.2f} kN·m  \n"
            f"- **η** = {eta:.3f}"
        )

        st.divider()
        st.subheader("Punto de diseño")
        estrategia = st.radio(
            "Selección automática",
            ["max_e", "min_P", "centroid", "manual"],
            format_func=lambda s: {
                "max_e":    "Máxima excentricidad (mínimo Ps)",
                "min_P":    "Mínima fuerza (mayor 1/Ps)",
                "centroid": "Centroide de la región",
                "manual":   "Manual",
            }[s],
            key="_radio_estrategia",
        )

        e_manual = Ps_manual = None
        if estrategia == "manual":
            e_manual  = st.number_input("e (m)", e_min_val, e_max_geo,
                                         float(estado.e or e_max_geo * 0.7),
                                         0.001, format="%.4f", key="_ni_e_man")
            Ps_manual = st.number_input("Ps (kN)", 50.0, 10000.0,
                                         float(estado.Pj * estado.beta if estado.Pj else 500),
                                         10.0, format="%.1f", key="_ni_Ps_man")

    # ── Región factible ──────────────────────────────────────────────
    e_arr, lower, upper, valid = feasible_region(
        sec, Msw, Mse, eta, lim,
        e_range=(e_min_val, e_max_geo),
        invP_range=(0.0, invP_max),
        n_points=1000,
    )
    factible = bool(np.any(valid))

    # ── Punto de diseño ──────────────────────────────────────────────
    resultado = None
    if estrategia != "manual":
        resultado = select_design_point(e_arr, lower, upper, valid, strategy=estrategia)
    elif e_manual is not None and Ps_manual is not None:
        resultado = (e_manual, 1.0 / Ps_manual, Ps_manual)

    with col_param:
        st.divider()
        if not factible:
            st.error(
                "❌ **No existe región factible.** "
                "Aumenta la altura h (Página 3) o revisa los parámetros de pérdidas."
            )
        elif resultado:
            e_d, invPs_d, Ps_d = resultado
            Pj_d = Ps_d / estado.beta if estado.beta > 0 and Ps_d else None

            st.success("✅ Región factible encontrada")
            c1, c2 = st.columns(2)
            c1.metric("Excentricidad e", f"{e_d:.4f} m")
            c2.metric("Ps diseño", f"{Ps_d:.1f} kN" if Ps_d else "—")
            if Pj_d:
                st.metric("Pj = Ps/β", f"{Pj_d:.1f} kN")

            if st.button("💾 Guardar punto de diseño", type="primary",
                         use_container_width=True):
                estado.e  = e_d
                estado.Pj = Pj_d
                estado.marcar_completada("magnel")
                guardar_estado(estado)
                st.success("Punto de diseño guardado. Continúa en Página 5.")

    # ── Gráfico ──────────────────────────────────────────────────────
    with col_diag:
        st.subheader("Diagrama de Magnel — plano (e, 1/Ps)")

        lineas = magnel_lines(sec, Msw, Mse, eta, lim, e_arr)
        colores_lineas = {
            "C1_serv_top":  COLORES["primario"],
            "C2_serv_bot":  COLORES["secundario"],
            "C3_trans_top": COLORES["acento"],
            "C4_trans_bot": COLORES["peligro"],
        }

        fig = go.Figure()

        # Región factible
        if factible:
            e_v = e_arr[valid]
            fig.add_trace(go.Scatter(
                x=np.concatenate([e_v, e_v[::-1]]),
                y=np.concatenate([upper[valid], lower[valid][::-1]]),
                fill="toself",
                fillcolor=_hex_a_rgba(COLORES["acento"], 0.18),
                line=dict(width=0),
                name="Región factible",
                hoverinfo="skip",
            ))

        # Líneas de restricción
        for key, (vals, bound_type, label) in lineas.items():
            color = colores_lineas.get(key, "#888888")
            y_clipped = np.clip(vals, 0, invP_max * 1.1)
            fig.add_trace(go.Scatter(
                x=e_arr, y=y_clipped,
                mode="lines",
                name=f"{'— ' if bound_type == 'upper' else '… '}{label}",
                line=dict(color=color, width=2.0,
                           dash="solid" if bound_type == "upper" else "dash"),
                hovertemplate=f"<b>{label}</b><br>e=%{{x:.4f}} m<br>1/Ps=%{{y:.6f}} 1/kN<extra></extra>",
            ))

        # Punto de diseño
        if resultado:
            e_d, invPs_d, Ps_d = resultado
            fig.add_trace(go.Scatter(
                x=[e_d], y=[invPs_d],
                mode="markers+text",
                marker=dict(color="red", size=14, symbol="star"),
                text=[f"  e={e_d:.3f} m<br>  Ps={Ps_d:.0f} kN"],
                textposition="top right",
                name="Punto de diseño",
            ))

        # Límite geométrico e_max
        fig.add_vline(x=e_max_geo, line=dict(color="#999", dash="dot", width=1.5),
                      annotation_text=f"e_max={e_max_geo:.3f} m",
                      annotation_position="top left")

        fig.update_layout(
            xaxis=dict(title="Excentricidad e (m)", gridcolor="#EEEEEE"),
            yaxis=dict(title="1/Ps (1/kN)", gridcolor="#EEEEEE",
                       tickformat=".5f"),
            plot_bgcolor="white", paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.25, font=dict(size=11)),
            hovermode="x unified",
            margin=dict(t=30, b=100, l=80, r=20),
            height=490,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "**Lectura:** La región verde es el conjunto de (e, 1/Ps) que satisfacen "
            "las 4 condiciones de tensión. Líneas sólidas = cotas superiores de 1/Ps; "
            "líneas discontinuas = cotas inferiores. "
            "Mayor 1/Ps → menor Ps (más económico)."
        )

except NotImplementedError:
    st.warning("El tipo de apoyo aún no implementa cálculo de momentos. "
               "Usa 'Simplemente apoyada'.")
except Exception as err:
    if not estado.etapa_completada("cargas_apoyos"):
        st.info("Completa las etapas 1 y 2 primero.")
    else:
        st.error(f"Error en el diagrama de Magnel: {err}")
        import traceback
        st.code(traceback.format_exc())

guardar_estado(estado)
