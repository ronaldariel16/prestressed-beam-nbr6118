"""
Página 1 — Geometría y Materiales

Permite al usuario definir:
  · Dimensiones de la sección transversal rectangular (b × h)
  · Clase de hormigón (fck, fckj, tipo de árido)
  · Acero de pretensado (cordón CP-190 RB)

Los datos se almacenan en st.session_state a través de EstadoProyecto.
"""
import sys
from pathlib import Path

# Raíz del proyecto → permite importar src/ y app/
_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.components.state import (
    guardar_estado,
    mostrar_barra_lateral,
    obtener_estado,
)
from app.components.inputs import (
    entrada_con_slider,
    selector_acero_pretensado,
    selector_factor_agregado,
    selector_hormigon,
)
from app.components.plots import dibujar_seccion_transversal
from app.components.tables import (
    tabla_propiedades_acero,
    tabla_propiedades_hormigon,
    tabla_propiedades_seccion,
)

# ── Configuración ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Geometría y Materiales — Viga Pretensada",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado
_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

# ── Barra lateral ─────────────────────────────────────────────────────────
mostrar_barra_lateral(etapa_actual="geometria_materiales")

# ── Estado del proyecto ───────────────────────────────────────────────────
estado = obtener_estado()

# ── Encabezado ────────────────────────────────────────────────────────────
st.title("📐 Geometría y Materiales")
st.markdown(
    "Define las dimensiones de la sección rectangular y los materiales. "
    "Todos los cambios se guardan automáticamente en el proyecto."
)

st.divider()

# ══════════════════════════════════════════════════════════════════════════
# Layout: INPUTS (izq) | SECCIÓN (centro) | TABLAS (der)
# ══════════════════════════════════════════════════════════════════════════
col_izq, col_centro, col_der = st.columns([1.1, 1.1, 1.6], gap="medium")

# ──────────────────────────────────────────────────────────────────────────
# COLUMNA IZQUIERDA — Entradas del usuario
# ──────────────────────────────────────────────────────────────────────────
with col_izq:

    # ── 1. Dimensiones ────────────────────────────────────────────────────
    st.subheader("1. Dimensiones de la sección")

    b = entrada_con_slider(
        etiqueta="Ancho b",
        clave_estado="b",
        valor=estado.b,
        minimo=0.10,
        maximo=1.00,
        paso=0.01,
        unidad="m",
        ayuda=(
            "Ancho de la sección transversal rectangular (m). "
            "Valores habituales para vigas: 0,15 m a 0,60 m. "
            "El ancho influye directamente en el módulo seccional y en la "
            "cantidad de cordones que caben en la sección."
        ),
        formato="%.2f",
    )

    h = entrada_con_slider(
        etiqueta="Altura h",
        clave_estado="h",
        valor=estado.h,
        minimo=0.20,
        maximo=2.50,
        paso=0.01,
        unidad="m",
        ayuda=(
            "Altura total de la sección transversal rectangular (m). "
            "La altura es el parámetro más influyente en la rigidez a flexión. "
            "Regla empírica para vigas simplemente apoyadas: h ≈ L/10 a L/15."
        ),
        formato="%.2f",
    )

    # Actualizar estado con los nuevos valores
    estado.b = b
    estado.h = h

    # Métricas rápidas
    try:
        sec_tmp = estado.get_section()
        c1, c2 = st.columns(2)
        c1.metric("A", f"{sec_tmp.A*1e4:.1f} cm²",
                  help="Área transversal de la sección (cm²).")
        c2.metric("I", f"{sec_tmp.I*1e8:.2f} cm⁴",
                  help="Momento de inercia respecto al eje neutro central (cm⁴).")
    except ValueError as err:
        st.error(f"Dimensiones inválidas: {err}")

    st.divider()

    # ── 2. Hormigón ───────────────────────────────────────────────────────
    st.subheader("2. Hormigón estructural")

    fck, fckj = selector_hormigon(
        fck_actual=estado.fck,
        fckj_actual=estado.fckj,
    )
    alpha_E = selector_factor_agregado(alpha_E_actual=estado.alpha_E)

    estado.fck    = fck
    estado.fckj   = fckj
    estado.alpha_E = alpha_E

    try:
        conc_tmp = estado.get_concrete()
        c1, c2, c3 = st.columns(3)
        c1.metric("fcd", f"{conc_tmp.fcd:.1f} MPa",
                  help="Resistencia de cálculo a compresión = fck / γc (γc = 1,4).")
        c2.metric("Ecs", f"{conc_tmp.Ecs(alpha_E)/1000:.1f} GPa",
                  help="Módulo de elasticidad secante del hormigón (GPa).")
        c3.metric("fct,m", f"{conc_tmp.fct_m:.2f} MPa",
                  help="Resistencia media a tracción = 0,3 · fck^(2/3).")
    except ValueError as err:
        st.error(f"Parámetros de hormigón inválidos: {err}")

    st.divider()

    # ── 3. Acero de pretensado ─────────────────────────────────────────────
    st.subheader("3. Acero de pretensado")

    steel_diameter = selector_acero_pretensado(
        diametro_actual=estado.steel_diameter,
    )
    estado.steel_diameter = steel_diameter

    try:
        steel_tmp = estado.get_steel()
        c1, c2 = st.columns(2)
        c1.metric("fpd", f"{steel_tmp.fpd:.0f} MPa",
                  help="Tensión de cálculo del acero de pretensado = fpyk / γs (γs = 1,15).")
        c2.metric("Pj,lim", f"{steel_tmp.Pj_lim_unit():.1f} kN",
                  help=(
                      "Fuerza máxima de pretensado por cordón según NBR 6118:2014 §9.6.1.2: "
                      "min(0,74·Pptk ; 0,85·Ppyk)."
                  ))
    except (ValueError, KeyError) as err:
        st.error(f"Parámetros de acero inválidos: {err}")

    st.divider()

    # ── Botón de confirmación ─────────────────────────────────────────────
    if st.button(
        "✅ Guardar y continuar →",
        type="primary",
        use_container_width=True,
        help="Guarda la geometría y los materiales; marca esta etapa como completada.",
    ):
        estado.marcar_completada("geometria_materiales")
        guardar_estado(estado)
        st.success(
            "Geometría y materiales guardados. Continúa en "
            "**2 — Cargas y Apoyos** usando el menú de la izquierda."
        )
        st.balloons()

    guardar_estado(estado)


# ──────────────────────────────────────────────────────────────────────────
# COLUMNA CENTRAL — Vista previa de la sección
# ──────────────────────────────────────────────────────────────────────────
with col_centro:
    st.subheader("Vista de la sección transversal")
    st.caption("Sección rectangular b × h con línea de centroide (CG).")

    try:
        fig_sec = dibujar_seccion_transversal(b=estado.b, h=estado.h)
        st.pyplot(fig_sec, use_container_width=True)
    except Exception as err:
        st.error(f"No se pudo generar la vista de la sección: {err}")

    # Indicador de relación de aspecto
    if estado.b > 0 and estado.h > 0:
        ratio = estado.h / estado.b
        nivel = (
            "⚠️ Muy esbelta (h/b > 5)" if ratio > 5 else
            "⚠️ Muy compacta (h/b < 1,5)" if ratio < 1.5 else
            "✅ Esbeltez razonable"
        )
        st.info(f"**Relación h/b = {ratio:.2f}** — {nivel}")

        # Relación de slenderness en contexto
        if estado.etapa_completada("cargas_apoyos"):
            rel_L_h = estado.L / estado.h
            if rel_L_h > 20:
                st.warning(
                    f"Relación L/h = {rel_L_h:.1f}. "
                    "Viga muy esbelta; considere aumentar la altura."
                )
            elif rel_L_h < 8:
                st.warning(
                    f"Relación L/h = {rel_L_h:.1f}. "
                    "Viga muy rígida; posiblemente sobredimensionada."
                )


# ──────────────────────────────────────────────────────────────────────────
# COLUMNA DERECHA — Tablas de propiedades
# ──────────────────────────────────────────────────────────────────────────
with col_der:
    tab_geom, tab_conc, tab_acero = st.tabs([
        "📐 Geometría",
        "🧱 Hormigón",
        "🔩 Acero",
    ])

    # ── Pestaña geometría ─────────────────────────────────────────────────
    with tab_geom:
        st.markdown("#### Propiedades geométricas de la sección")
        try:
            seccion = estado.get_section()
            df_geom = tabla_propiedades_seccion(seccion)
            st.dataframe(
                df_geom,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Propiedad": st.column_config.TextColumn("Propiedad", width="medium"),
                    "Símbolo":   st.column_config.TextColumn("Símbolo",   width="small"),
                    "Valor":     st.column_config.TextColumn("Valor",     width="small"),
                    "Unidad":    st.column_config.TextColumn("Unidad",    width="small"),
                },
            )

            # Fórmula resumida
            st.markdown(
                f"""
                **Fórmulas aplicadas (sección b×h):**
                - A = b·h = {estado.b:.3f}·{estado.h:.3f} = **{seccion.A:.5f} m²**
                - I = b·h³/12 = **{seccion.I:.8f} m⁴**
                - yt = yb = h/2 = **{seccion.yt:.4f} m**
                - zt = zb = I/yt = **{seccion.zt:.6f} m³**
                """
            )
        except ValueError as err:
            st.error(f"Error en propiedades geométricas: {err}")

    # ── Pestaña hormigón ──────────────────────────────────────────────────
    with tab_conc:
        st.markdown("#### Propiedades del hormigón")
        try:
            concreto = estado.get_concrete()
            df_conc = tabla_propiedades_hormigon(concreto, alpha_E=estado.alpha_E)
            st.dataframe(
                df_conc,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Propiedad":  st.column_config.TextColumn("Propiedad",  width="large"),
                    "Símbolo":    st.column_config.TextColumn("Símbolo",    width="small"),
                    "Valor":      st.column_config.TextColumn("Valor",      width="small"),
                    "Unidad":     st.column_config.TextColumn("Unidad",     width="small"),
                    "Ref. NBR":   st.column_config.TextColumn("Ref. NBR",   width="small"),
                },
            )

            st.divider()
            st.markdown("##### Límites de tensión admisibles")
            from src.stress_limits import stress_limits
            lim = stress_limits(concreto)
            col_t, col_s = st.columns(2)
            with col_t:
                st.markdown("**Acto de transferencia:**")
                st.markdown(
                    f"- Compresión: **{lim.ftc:.2f} MPa**  \n"
                    f"- Tracción:   **{lim.ftt:.2f} MPa**"
                )
            with col_s:
                st.markdown("**En servicio (ELS):**")
                st.markdown(
                    f"- Compresión: **{lim.fsc:.2f} MPa**  \n"
                    f"- Tracción:   **{lim.fst:.2f} MPa**"
                )

        except ValueError as err:
            st.error(f"Error en propiedades del hormigón: {err}")

    # ── Pestaña acero ─────────────────────────────────────────────────────
    with tab_acero:
        st.markdown("#### Propiedades del acero de pretensado")
        try:
            acero = estado.get_steel()
            df_acero = tabla_propiedades_acero(acero)
            st.dataframe(
                df_acero,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Propiedad": st.column_config.TextColumn("Propiedad", width="medium"),
                    "Símbolo":   st.column_config.TextColumn("Símbolo",   width="small"),
                    "Valor":     st.column_config.TextColumn("Valor",     width="small"),
                    "Unidad":    st.column_config.TextColumn("Unidad",    width="small"),
                },
            )

            st.divider()
            st.markdown(
                f"""
                ##### Capacidad de la armadura activa
                - **Pj,lim / cordón** = min(0,74·Pptk ; 0,85·Ppyk)
                  = min({0.74*acero.Pptk_unit:.1f} ; {0.85*acero.Ppyk_unit:.1f})
                  = **{acero.Pj_lim_unit():.2f} kN/cordón**
                - **Área por cordón** = {acero.Aps_unit_mm2:.1f} mm²
                  = {acero.Aps_unit*1e4:.2f} cm²
                - **Módulo de elasticidad** = {acero.Eps:.0f} MPa
                  = {acero.Eps/1000:.0f} GPa
                """
            )
        except (ValueError, KeyError) as err:
            st.error(f"Error en propiedades del acero: {err}")

# ──────────────────────────────────────────────────────────────────────────
# Nota al pie
# ──────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "**Referencias:** NBR 6118:2014 §8.2 (hormigón), §8.4 (acero de pretensado). "
    "Catálogo de cordones: ArcelorMittal CP-190 RB. "
    "Torii, A. J. (2020) — *Concreto Protendido*, Cap. 3."
)
