"""
Página 5 — Armadura y Perfil del Tendón

Calcula el número de cordones y su disposición en la sección transversal.
Grafica la zona admisible a lo largo de la viga y el perfil propuesto.
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
from app.components.plots import dibujar_seccion_transversal, COLORES, _hex_a_rgba

st.set_page_config(
    page_title="Armadura y Perfil — Viga Pretensada",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

mostrar_barra_lateral(etapa_actual="armadura_perfil")
estado = obtener_estado()

st.title("🔗 Armadura y Perfil del Tendón")

for etapa, nombre in [
    ("geometria_materiales", "1 — Geometría y Materiales"),
    ("cargas_apoyos",        "2 — Cargas y Apoyos"),
    ("magnel",               "4 — Diagrama de Magnel"),
]:
    if not estado.etapa_completada(etapa):
        st.warning(f"⚠️ Completa primero la etapa **{nombre}**.")

if estado.Pj is None:
    st.error("Pj no determinado. Completa el Diagrama de Magnel (Página 4).")
    st.stop()

st.divider()

try:
    from src.reinforcement import number_of_strands, arrange_strands
    from src.tendon_profile import parabolic_profile, straight_profile, admissible_zone
    from src.stress_limits import stress_limits

    conc    = estado.get_concrete()
    sec     = estado.get_section()
    loads   = estado.get_loads()
    support = estado.get_support()
    steel   = estado.get_steel()

    lim = stress_limits(conc)
    Pj  = estado.Pj
    Ps  = Pj * estado.beta

    col_izq, col_der = st.columns([1, 1.6], gap="medium")

    with col_izq:
        st.subheader("1. Número de cordones")

        n_calc = number_of_strands(Pj, steel)
        n = st.number_input(
            "Número de cordones",
            min_value=1, max_value=200,
            value=int(n_calc),
            step=1,
            key="_ni_n_strands",
            help=(
                f"Número mínimo calculado: n = ⌈Pj / Pj,lim⌉ = "
                f"⌈{Pj:.1f} / {steel.Pj_lim_unit():.2f}⌉ = {n_calc}. "
                "Puede aumentarse para reducir la excentricidad real."
            ),
        )
        estado.n_strands = n

        # Verificación de fuerza
        Pj_real = n * steel.Pj_lim_unit()
        Aps_total = n * steel.Aps_unit_mm2
        st.metric("Pj real (n cordones)", f"{Pj_real:.1f} kN",
                  delta=f"{(Pj_real - Pj):.1f} kN sobre el requerido")

        st.divider()
        st.subheader("2. Disposición en la sección")

        cover = st.number_input(
            "Recubrimiento c (m)", 0.02, 0.10, 0.04, 0.005,
            format="%.3f", key="_ni_cover_arm",
            help="Distancia del eje del cordón al borde de la sección (m).",
        )
        spacing = st.number_input(
            "Espaciado entre ejes (m)", 0.03, 0.15, 0.05, 0.005,
            format="%.3f", key="_ni_spacing_arm",
            help="Espaciado mínimo entre ejes de cordones en la misma camada (m). "
                 "NBR 6118:2014 §18.6.2.3: mínimo 3·Ø o 20 mm.",
        )

        positions, e_real = arrange_strands(n, sec, cover=cover, spacing=spacing)
        estado.e_real = e_real

        n_camadas = len(set(round(y, 4) for y in positions))
        st.markdown(
            f"- **Camadas:** {n_camadas}  \n"
            f"- **Baricentro** (desde base): {(sec.yb - e_real)*100:.1f} cm  \n"
            f"- **Excentricidad real** e_real: **{e_real:.4f} m**  \n"
            f"- **Aps total** = {n} × {steel.Aps_unit_mm2:.1f} = **{Aps_total:.1f} mm²**"
        )

        if abs(e_real - (estado.e or 0)) > 0.01:
            st.warning(
                f"⚠️ La excentricidad real ({e_real:.4f} m) difiere "
                f"de la de diseño ({estado.e:.4f} m). "
                "Esto puede afectar la verificación de tensiones."
            )

        st.divider()
        st.subheader("3. Tipo de perfil")
        perfil_tipo = st.selectbox(
            "Tipo de perfil del tendón",
            options=["parabolico", "recto"],
            index=0 if estado.profile_type == "parabolico" else 1,
            format_func=lambda x: {
                "parabolico": "Parabólico (máx e en el centro)",
                "recto":      "Recto (e constante)",
            }[x],
            key="_sel_perfil",
            help="Perfil parabólico: óptimo para viga simplemente apoyada con carga uniforme. "
                 "Perfil recto: más simple, usado en pretracción.",
        )
        estado.profile_type = perfil_tipo

        st.divider()
        if st.button("💾 Guardar armadura y perfil →", type="primary",
                     use_container_width=True):
            estado.marcar_completada("armadura_perfil")
            guardar_estado(estado)
            st.success("Armadura y perfil guardados.")

        guardar_estado(estado)

    with col_der:
        tab_sec, tab_perfil = st.tabs(["📐 Sección con cordones", "📈 Perfil a lo largo de la viga"])

        with tab_sec:
            st.markdown("#### Sección transversal con cordones posicionados")
            # Convertir posiciones (y desde base, x centrado) → (y_desde_base, x)
            cordones_plot = []
            for y in positions:
                cordones_plot.append((y, sec.b / 2))  # simplificación: centrados

            fig_sec = dibujar_seccion_transversal(
                b=sec.b, h=sec.h,
                cordones=cordones_plot,
                cobertura=cover,
            )
            st.pyplot(fig_sec, use_container_width=True)
            st.caption(
                f"Los {n} cordones están distribuidos en {n_camadas} camada(s). "
                f"Recubrimiento nominal c = {cover*100:.0f} cm."
            )

        with tab_perfil:
            st.markdown("#### Zona admisible y perfil del tendón")

            try:
                x_z, e_min_z, e_max_z = admissible_zone(
                    sec, conc, loads, support, Ps, lim,
                    cover_bottom=cover, cover_top=cover,
                )

                # Perfil propuesto
                if perfil_tipo == "parabolico":
                    x_p, e_p = parabolic_profile(e_real, support.L, e_end=0.0)
                else:
                    x_p, e_p = straight_profile(e_real, support.L)

                fig_perf = go.Figure()

                # Zona admisible (banda verde)
                fig_perf.add_trace(go.Scatter(
                    x=np.concatenate([x_z, x_z[::-1]]),
                    y=np.concatenate([e_max_z, e_min_z[::-1]]),
                    fill="toself",
                    fillcolor=_hex_a_rgba(COLORES["acento"], 0.15),
                    line=dict(width=0),
                    name="Zona admisible",
                    hoverinfo="skip",
                ))
                fig_perf.add_trace(go.Scatter(
                    x=x_z, y=e_max_z, mode="lines",
                    line=dict(color=COLORES["acento"], width=1.5, dash="dash"),
                    name="e_max (zona admit.)",
                    hovertemplate="x=%{x:.2f} m<br>e_max=%{y:.4f} m<extra></extra>",
                ))
                fig_perf.add_trace(go.Scatter(
                    x=x_z, y=e_min_z, mode="lines",
                    line=dict(color=COLORES["acento"], width=1.5, dash="dot"),
                    name="e_min (zona admit.)",
                    hovertemplate="x=%{x:.2f} m<br>e_min=%{y:.4f} m<extra></extra>",
                ))

                # Perfil propuesto
                fig_perf.add_trace(go.Scatter(
                    x=x_p, y=e_p, mode="lines",
                    line=dict(color=COLORES["primario"], width=2.5),
                    name=f"Perfil {perfil_tipo}",
                    hovertemplate="x=%{x:.2f} m<br>e=%{y:.4f} m<extra></extra>",
                ))

                # Verificación
                from src.tendon_profile import verify_profile
                e_p_interp = np.interp(x_z, x_p, e_p)
                ok_arr = verify_profile(e_p_interp, e_min_z, e_max_z)
                n_fuera = np.sum(~ok_arr)
                if n_fuera == 0:
                    st.success("✅ El perfil propuesto está **dentro** de la zona admisible.")
                else:
                    st.error(f"❌ El perfil sale de la zona admisible en {n_fuera} punto(s).")

                fig_perf.update_layout(
                    xaxis=dict(title="Posición a lo largo de la viga x (m)", gridcolor="#EEEEEE"),
                    yaxis=dict(title="Excentricidad e (m)", gridcolor="#EEEEEE"),
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    legend=dict(orientation="h", y=-0.22),
                    hovermode="x unified",
                    margin=dict(t=20, b=80, l=60, r=20),
                    height=420,
                )
                st.plotly_chart(fig_perf, use_container_width=True)

            except NotImplementedError:
                st.warning("La zona admisible no está disponible para este tipo de apoyo.")
            except Exception as err2:
                st.error(f"Error al calcular la zona admisible: {err2}")

except NotImplementedError:
    st.warning("El tipo de apoyo no implementa cálculo de momentos.")
except Exception as err:
    st.error(f"Error en armadura y perfil: {err}")
