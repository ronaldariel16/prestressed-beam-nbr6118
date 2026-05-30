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
    from src.magnel import is_in_feasible_region

    conc    = estado.get_concrete()
    sec     = estado.get_section()
    loads   = estado.get_loads()
    support = estado.get_support()
    steel   = estado.get_steel()

    lim = stress_limits(conc)
    Pj  = estado.Pj
    Ps  = Pj * estado.beta

    # Momentos en la sección crítica (para verificación de Magnel)
    pp = sec.A * conc.gamma_concrete
    x_crit, _ = support.critical_sections()[0]
    Msw = abs(support.M_uniform(x_crit, pp))
    Mgk = abs(support.M_uniform(x_crit, loads.gk))
    Mqk = abs(support.M_uniform(x_crit, loads.qk))
    Mse = Msw + Mgk + Mqk
    eta = estado.beta / estado.alpha if estado.alpha > 0 else 0.83

    # Diámetro real del cordón en metros
    diam_m = steel.diameter / 1000.0

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
                f"⌈{Pj:.1f} / {steel.Pj_lim_unit():.2f}⌉ = {n_calc}.  \n"
                "Puede ajustarse para modificar la excentricidad real."
            ),
        )
        estado.n_strands = n

        Pj_real = n * steel.Pj_lim_unit()
        Ps_real = Pj_real * estado.beta
        Aps_total = n * steel.Aps_unit_mm2

        st.metric(
            "Pj real (n cordones)",
            f"{Pj_real:.1f} kN",
            delta=f"{(Pj_real - Pj):.1f} kN sobre Pj requerido",
            help=f"Pj_real = n × Pj,lim = {n} × {steel.Pj_lim_unit():.2f} kN",
        )

        st.divider()
        st.subheader("2. Disposición en la sección")

        cover = st.number_input(
            "Recubrimiento nominal c (m)", 0.02, 0.10, 0.04, 0.005,
            format="%.3f", key="_ni_cover_arm",
            help=(
                "Distancia del borde de la sección al eje del cordón (m).  \n"
                "NBR 6118:2014 §7.4.7: mínimo según clase de agressividad (CAA)."
            ),
        )
        spacing = st.number_input(
            "Espaciado libre entre cordones s (m)", 0.02, 0.15, 0.05, 0.005,
            format="%.3f", key="_ni_spacing_arm",
            help=(
                "Distancia libre (clear) entre las superficies de cordones adyacentes (m).  \n"
                "NBR 6118:2014 §18.6.2.3: mínimo 3·Ø o 20 mm.  \n"
                f"Para Ø {steel.diameter:.1f} mm: mín = max(3×{steel.diameter:.1f}={3*steel.diameter:.0f} mm, 20 mm) "
                f"= {max(3*steel.diameter, 20):.0f} mm = {max(3*steel.diameter/1000, 0.02):.3f} m."
            ),
        )

        # Llamar con el diámetro real del cordón
        positions, e_real = arrange_strands(
            n, sec,
            cover=cover,
            spacing=spacing,
            diameter_strand=diam_m,
        )
        estado.e_real = e_real

        n_camadas = len(set(round(y, 4) for y in positions))
        y_baricentro = sec.yb - e_real

        st.markdown(
            f"- **Camadas:** {n_camadas}  \n"
            f"- **Baricentro** (desde base): **{y_baricentro*100:.2f} cm**  \n"
            f"- **Excentricidad real** e_real: **{e_real:.4f} m**  \n"
            f"- **Aps total** = {n} × {steel.Aps_unit_mm2:.1f} = **{Aps_total:.1f} mm²**  \n"
            f"- **Ps real** = {Pj_real:.1f} × {estado.beta:.3f} = **{Ps_real:.1f} kN**"
        )

        # ── Verificación de consistencia e_real vs diseño ────────────────
        st.divider()
        e_diseno = estado.e or 0.0
        e_max_geo = sec.yb - cover   # límite geométrico inferior

        if e_real > e_max_geo:
            st.error(
                f"❌ **e_real ({e_real:.4f} m) excede el límite geométrico "
                f"({e_max_geo:.4f} m).**  \n"
                "El cable saldría de la sección. Aumenta n para distribuir en más "
                "camadas, reduce el diámetro o aumenta la cobertura."
            )

        else:
            # Verificar si el punto real está en la región factible de Magnel
            invPs_real = 1.0 / Ps_real if Ps_real > 0 else 0.0
            en_region = is_in_feasible_region(
                e_real, invPs_real, sec, Msw, Mse, eta, lim
            )

            if en_region:
                st.success(
                    f"✅ El punto real **(e = {e_real:.4f} m, Ps = {Ps_real:.0f} kN)** "
                    f"está **dentro** de la región factible de Magnel.  \n"
                    "Puede guardar este diseño o actualizar el punto de diseño en Página 4 "
                    f"con e ≈ {e_real:.3f} m."
                )
            elif abs(e_real - e_diseno) > 0.005:
                st.warning(
                    f"⚠️ La excentricidad real **({e_real:.4f} m)** difiere del punto "
                    f"de Magnel **({e_diseno:.4f} m)** y el punto real está **fuera** "
                    f"de la región factible (Ps_real = {Ps_real:.0f} kN).  \n\n"
                    f"**Opción A:** Reducir a **{max(1, n-1)} cordones** → menor e_real "
                    f"y menor Pj_real → puede que el punto entre en la región.  \n"
                    f"**Opción B:** Ir a **Página 4** y seleccionar un nuevo punto de "
                    f"diseño con e ≈ {e_real:.3f} m."
                )
            else:
                st.success(
                    f"✅ e_real ({e_real:.4f} m) ≈ e_diseño ({e_diseno:.4f} m). "
                    "Disposición coherente con el punto de Magnel."
                )

        st.divider()
        st.subheader("3. Tipo de perfil del tendón")
        perfil_tipo = st.selectbox(
            "Tipo de perfil",
            options=["parabolico", "recto"],
            index=0 if estado.profile_type == "parabolico" else 1,
            format_func=lambda x: {
                "parabolico": "Parabólico (e_max en el centro del vano)",
                "recto":      "Recto (e constante a lo largo del vano)",
            }[x],
            key="_sel_perfil",
            help=(
                "Perfil parabólico: óptimo para viga simplemente apoyada bajo carga uniforme; "
                "minimiza las pérdidas por fricción y maximiza la contraflecha.  \n"
                "Perfil recto: más simple, habitual en pretracción."
            ),
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
        tab_sec, tab_perfil = st.tabs([
            "📐 Sección con cordones",
            "📈 Perfil a lo largo de la viga",
        ])

        with tab_sec:
            st.markdown("#### Sección transversal con cordones posicionados")
            cordones_plot = [(y, sec.b / 2) for y in positions]

            fig_sec = dibujar_seccion_transversal(
                b=sec.b, h=sec.h,
                cordones=cordones_plot,
                cobertura=cover,
            )
            st.pyplot(fig_sec, use_container_width=True)
            st.caption(
                f"{n} cordones Ø {steel.diameter:.1f} mm distribuidos en "
                f"{n_camadas} camada(s). "
                f"Recubrimiento c = {cover*100:.0f} cm. "
                f"Espaciado libre s = {spacing*100:.0f} mm."
            )

        with tab_perfil:
            st.markdown("#### Zona admisible y perfil del tendón")

            try:
                x_z, e_min_z, e_max_z = admissible_zone(
                    sec, conc, loads, support, Ps_real, lim,
                    cover_bottom=cover, cover_top=cover,
                )

                if perfil_tipo == "parabolico":
                    x_p, e_p = parabolic_profile(e_real, support.L, e_end=0.0)
                else:
                    x_p, e_p = straight_profile(e_real, support.L)

                fig_perf = go.Figure()

                # Zona admisible
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

                # Verificación tramo a tramo
                from src.tendon_profile import verify_profile
                e_p_interp = np.interp(x_z, x_p, e_p)
                ok_arr = verify_profile(e_p_interp, e_min_z, e_max_z)
                n_fuera = int(np.sum(~ok_arr))
                if n_fuera == 0:
                    st.success("✅ El perfil propuesto está **dentro** de la zona admisible.")
                else:
                    st.error(
                        f"❌ El perfil sale de la zona admisible en {n_fuera} punto(s).  \n"
                        "Considera cambiar el tipo de perfil o ajustar e_real."
                    )

                fig_perf.update_layout(
                    xaxis=dict(title="Posición x (m)", gridcolor="#EEEEEE"),
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
