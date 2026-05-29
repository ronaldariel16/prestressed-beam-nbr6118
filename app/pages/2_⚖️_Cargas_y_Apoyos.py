"""
Página 2 — Cargas y Apoyos

Define la condición de apoyo, las cargas y los parámetros de pretensado.
Muestra el diagrama de momentos flectores interactivo (plotly).
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import streamlit as st

from app.components.state import guardar_estado, mostrar_barra_lateral, obtener_estado
from app.components.inputs import (
    selector_nivel_pretensado,
    selector_tipo_apoyo,
    selector_tipo_pretensado,
    selector_uso_edificacion,
)
from app.components.plots import graficar_diagrama_momentos
from app.components.tables import tabla_combinaciones_carga

st.set_page_config(
    page_title="Cargas y Apoyos — Viga Pretensada",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

mostrar_barra_lateral(etapa_actual="cargas_apoyos")
estado = obtener_estado()

st.title("⚖️ Cargas y Apoyos")
if not estado.etapa_completada("geometria_materiales"):
    st.warning("⚠️ Completa primero la etapa **1 — Geometría y Materiales**.")

st.divider()

col_izq, col_der = st.columns([1.1, 1.8], gap="medium")

# ─────────────────────────────────────────────────────────────────────────
# COLUMNA IZQUIERDA — Entradas
# ─────────────────────────────────────────────────────────────────────────
with col_izq:

    st.subheader("1. Condición de apoyo")
    tipo_apoyo = selector_tipo_apoyo(tipo_actual=estado.support_type)
    estado.support_type = tipo_apoyo

    es_continua = tipo_apoyo == "continua_dos_vanos"
    es_stub = tipo_apoyo in ("empotrada_apoyada", "continua_dos_vanos")

    L = st.number_input(
        "Luz del vano L (m)" if not es_continua else "Luz del primer vano L₁ (m)",
        min_value=1.0, max_value=60.0,
        value=float(estado.L), step=0.5,
        format="%.1f",
        key="_ni_L",
        help=(
            "Luz libre entre apoyos (m). "
            "Para viga continua, es la luz del primer vano."
        ),
    )
    estado.L = L

    if es_continua:
        L2 = st.number_input(
            "Luz del segundo vano L₂ (m)",
            min_value=1.0, max_value=60.0,
            value=float(estado.L2), step=0.5,
            format="%.1f",
            key="_ni_L2",
            help="Luz del segundo vano de la viga continua (m).",
        )
        estado.L2 = L2

    if es_stub:
        st.warning(
            "⚠️ Este tipo de apoyo aún no está completamente implementado en el backend. "
            "Los cálculos de momentos no estarán disponibles."
        )

    st.divider()

    st.subheader("2. Cargas características")
    gk = st.number_input(
        "Carga permanente gk (kN/m)",
        min_value=0.0, max_value=500.0,
        value=float(estado.gk), step=1.0,
        format="%.1f",
        key="_ni_gk",
        help=(
            "Carga permanente adicional distribuida sin incluir el peso propio (kN/m). "
            "Incluye revestimientos, tabiques fijos, instalaciones, etc."
        ),
    )
    qk = st.number_input(
        "Sobrecarga variable qk (kN/m)",
        min_value=0.0, max_value=500.0,
        value=float(estado.qk), step=1.0,
        format="%.1f",
        key="_ni_qk",
        help=(
            "Sobrecarga variable distribuida característica (kN/m). "
            "Valor según NBR 6120 para el uso previsto."
        ),
    )
    estado.gk = gk
    estado.qk = qk
    estado.usage = selector_uso_edificacion(uso_actual=estado.usage)

    st.divider()

    st.subheader("3. Parámetros de pretensado")
    estado.prestress_level = selector_nivel_pretensado(nivel_actual=estado.prestress_level)
    estado.prestress_type  = selector_tipo_pretensado(tipo_actual=estado.prestress_type)

    CAA_OPCIONES = {"I": "I — Fuertemente agresivo", "II": "II — Mod. agresivo",
                    "III": "III — Poco agresivo", "IV": "IV — Muy poco agresivo"}
    idx_caa = list(CAA_OPCIONES.keys()).index(estado.CAA) if estado.CAA in CAA_OPCIONES else 2
    estado.CAA = st.selectbox(
        "Clase de Agresividad Ambiental (CAA)",
        options=list(CAA_OPCIONES.keys()),
        index=idx_caa,
        format_func=lambda k: CAA_OPCIONES[k],
        key="_sel_CAA",
        help=(
            "Define las exigencias de recubrimiento mínimo y los límites de fisuración "
            "según NBR 6118:2014 Tabla 6.1."
        ),
    )

    st.divider()
    st.subheader("4. Estimación de pérdidas")
    c1, c2 = st.columns(2)
    with c1:
        estado.alpha = st.number_input(
            "α = Pt/Pj",
            0.70, 1.00, float(estado.alpha), 0.01, format="%.2f",
            key="_ni_alpha",
            help="Fracción de Pj que permanece tras las pérdidas inmediatas. Típico: 0,85–0,95.",
        )
    with c2:
        estado.beta = st.number_input(
            "β = Ps/Pj",
            0.50, float(estado.alpha), float(min(estado.beta, estado.alpha)),
            0.01, format="%.2f",
            key="_ni_beta",
            help="Fracción de Pj que permanece en servicio. Típico: 0,70–0,85.",
        )
    eta = estado.beta / estado.alpha if estado.alpha > 0 else 0.83
    st.caption(f"η = Ps/Pt = β/α = {eta:.3f}")

    st.divider()
    if st.button("✅ Guardar y continuar →", type="primary", use_container_width=True):
        estado.marcar_completada("cargas_apoyos")
        guardar_estado(estado)
        st.success("Cargas y apoyos guardados.")

    guardar_estado(estado)

# ─────────────────────────────────────────────────────────────────────────
# COLUMNA DERECHA — Resultados y diagrama
# ─────────────────────────────────────────────────────────────────────────
with col_der:

    # ── Métricas de momentos ──────────────────────────────────────────────
    st.subheader("Momentos en la sección crítica")

    try:
        conc    = estado.get_concrete()
        sec     = estado.get_section()
        loads   = estado.get_loads()
        support = estado.get_support()

        pp = sec.A * conc.gamma_concrete
        x_crit, tipo_crit = support.critical_sections()[0]

        Msw = abs(support.M_uniform(x_crit, pp))
        Mgk = abs(support.M_uniform(x_crit, gk))
        Mqk = abs(support.M_uniform(x_crit, qk))
        Mse_total = Msw + Mgk + Mqk

        from src.loads import combine_actions, Md_ULS
        combos = combine_actions(estado.prestress_level, Mgk + Msw, Mqk,
                                 loads.psi1, loads.psi2)
        Md = Md_ULS(Mgk + Msw, Mqk)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Msw (PP)", f"{Msw:.1f} kN·m",
                  help="Momento del peso propio en la sección crítica.")
        m2.metric("Mgk (perm.)", f"{Mgk:.1f} kN·m",
                  help="Momento de la carga permanente adicional.")
        m3.metric("Mqk (variable)", f"{Mqk:.1f} kN·m",
                  help="Momento de la sobrecarga variable.")
        m4.metric("Msd (ELU)", f"{Md:.1f} kN·m",
                  help="Momento de cálculo ELU = γg·Mgk + γq·Mqk.")

        # ── Tabla de combinaciones ────────────────────────────────────────
        st.markdown("#### Combinaciones de carga (sección crítica)")
        df_combo = tabla_combinaciones_carga(Msw, Mgk, Mqk, combos, Md)
        st.dataframe(df_combo, use_container_width=True, hide_index=True)

        # ── Diagrama de momentos ──────────────────────────────────────────
        st.markdown("#### Diagrama de momentos flectores")

        n_pts = 61
        x_arr, M_sw_arr = support.M_array(pp, n_pts)
        _, M_gk_arr     = support.M_array(gk, n_pts)
        _, M_qk_arr     = support.M_array(qk, n_pts)
        M_se_arr = M_sw_arr + M_gk_arr + M_qk_arr
        M_d_arr  = 1.4 * (M_sw_arr + M_gk_arr) + 1.4 * M_qk_arr

        fig_M = graficar_diagrama_momentos(
            x_arr,
            {
                "Msw — Peso propio":       M_sw_arr,
                "Mgk — Carga permanente":  M_gk_arr,
                "Mqk — Sobrecarga":        M_qk_arr,
                "Mse — Servicio total":    M_se_arr,
                "Msd — Cálculo (ELU)":    M_d_arr,
            },
            titulo="Diagrama de momentos flectores (kN·m)",
        )
        st.plotly_chart(fig_M, use_container_width=True)

        # ── Peso propio ───────────────────────────────────────────────────
        st.info(
            f"**Peso propio de la viga:** {pp:.2f} kN/m  "
            f"(A = {sec.A*1e4:.1f} cm² × γc = {conc.gamma_concrete:.0f} kN/m³)"
        )

    except NotImplementedError:
        st.warning(
            "⚠️ El tipo de apoyo seleccionado aún no tiene implementado "
            "el cálculo de momentos en el backend. "
            "Selecciona 'Simplemente apoyada', 'Biempotrada' o 'Voladizo'."
        )
    except Exception as err:
        if estado.etapa_completada("geometria_materiales"):
            st.error(f"Error en el cálculo: {err}")
        else:
            st.info("Define primero la geometría y los materiales (Página 1).")
