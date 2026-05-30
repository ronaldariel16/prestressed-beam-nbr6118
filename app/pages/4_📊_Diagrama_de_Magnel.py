"""
Página 4 — Diagrama de Magnel

Construye el diagrama de Magnel con las 4 restricciones lineales en el plano
(e, 1/Ps). Identifica la región factible y permite seleccionar el punto de
diseño de forma automática o manual.

Estrategias automáticas:
  · max_e    — mayor e factible; en ese e, 1/Ps = límite superior (Ps mínimo).
  · min_P    — menor Ps global (máximo 1/Ps sobre toda la región).
  · centroid — centroide ponderado del polígono factible.
  · manual   — el usuario ingresa e y Ps; se valida si está dentro de la región.
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
    from src.magnel import (
        feasible_region, magnel_lines,
        select_design_point, is_in_feasible_region,
    )
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
            help=(
                "Distancia del eje del cable a la fibra inferior (m). "
                "Define el límite geométrico máximo de e: e_max = yb − c."
            ),
        )
        e_max_geo = sec.yb - cover
        e_min_val = st.number_input(
            "Excentricidad mínima e_min (m)",
            0.0, float(e_max_geo * 0.5), 0.0, 0.01,
            format="%.3f", key="_ni_emin_magnel",
            help="Excentricidad mínima a graficar (m). Para viga simplemente apoyada, suele ser 0.",
        )
        Ps_min_kN = st.number_input(
            "Ps mínimo a graficar (kN)", 50.0, 2000.0, 100.0, 50.0,
            format="%.0f", key="_ni_Psmin_magnel",
            help="Define el límite superior del eje 1/Ps: 1/Ps_min.",
        )
        invP_max = 1.0 / Ps_min_kN

        st.info(
            f"**Límite geométrico:** e_max = yb − c = "
            f"{sec.yb:.4f} − {cover:.3f} = **{e_max_geo:.4f} m**"
        )

        st.divider()
        st.subheader("Momentos en la sección crítica")
        st.markdown(
            f"- **Msw** = {Msw:.2f} kN·m (peso propio)  \n"
            f"- **Mse** = {Mse:.2f} kN·m (servicio total)  \n"
            f"- **η** = {eta:.3f}"
        )

        st.divider()
        st.subheader("Punto de diseño")
        estrategia = st.radio(
            "Selección del punto de diseño",
            ["max_e", "min_P", "centroid", "manual"],
            format_func=lambda s: {
                "max_e":    "Máxima excentricidad (mínimo Ps)",
                "min_P":    "Mínima fuerza (mayor 1/Ps)",
                "centroid": "Centroide de la región factible",
                "manual":   "Manual (ingresar e y Ps)",
            }[s],
            key="_radio_estrategia",
            help=(
                "Máxima excentricidad: mayor e factible → Ps mínimo en ese e. "
                "Mínima fuerza: menor Ps en toda la región. "
                "Centroide: punto central del polígono factible. "
                "Manual: el usuario elige e y Ps; se verifica si está dentro de la región."
            ),
        )

        e_manual = Ps_manual = None
        if estrategia == "manual":
            e_manual = st.number_input(
                "Excentricidad e (m)",
                float(e_min_val), float(e_max_geo),
                float(estado.e or e_max_geo * 0.7),
                0.001, format="%.4f", key="_ni_e_man",
                help="Excentricidad del punto de diseño a verificar (m).",
            )
            Ps_manual = st.number_input(
                "Fuerza Ps (kN)",
                50.0, 10000.0,
                float(estado.Pj * estado.beta if estado.Pj else 500),
                10.0, format="%.1f", key="_ni_Ps_man",
                help="Fuerza de pretensado en servicio a verificar (kN).",
            )

    # ── Región factible (para visualización) ─────────────────────────
    e_arr, lower, upper, valid = feasible_region(
        sec, Msw, Mse, eta, lim,
        e_range=(e_min_val, e_max_geo),
        invP_range=(0.0, invP_max),
        n_points=1000,
    )
    factible = bool(np.any(valid))

    # ── Selección del punto de diseño ─────────────────────────────────
    # select_design_point trabaja sobre cotas crudas (sin clipping)
    # y garantiza que el punto esté DENTRO de la región (lo < up estricto).
    resultado = None
    punto_en_region = False

    if estrategia == "manual":
        if e_manual is not None and Ps_manual is not None and Ps_manual > 0:
            invPs_man = 1.0 / Ps_manual
            resultado = (e_manual, invPs_man, Ps_manual)
            punto_en_region = is_in_feasible_region(
                e_manual, invPs_man, sec, Msw, Mse, eta, lim
            )
    else:
        resultado = select_design_point(
            sec, Msw, Mse, eta, lim,
            e_min=float(e_min_val), e_max=float(e_max_geo),
            strategy=estrategia, n_pts=1000,
        )
        # select_design_point solo devuelve puntos con lo < up (interior)
        if resultado is not None:
            e_d, invPs_d, _ = resultado
            punto_en_region = is_in_feasible_region(
                e_d, invPs_d, sec, Msw, Mse, eta, lim
            )

    # ── Panel de resultado (columna izquierda) ────────────────────────
    with col_param:
        st.divider()

        if not factible:
            st.error(
                "❌ **No existe región factible** con los parámetros actuales.  \n"
                "→ Aumenta la altura h (Página 3) o ajusta α y β (Página 2)."
            )

        elif resultado is not None:
            e_d, invPs_d, Ps_d = resultado
            Pj_d = Ps_d / estado.beta if estado.beta > 0 and Ps_d else None

            if estrategia == "manual":
                if punto_en_region:
                    st.success(
                        f"✅ El punto manual **(e={e_d:.4f} m, Ps={Ps_d:.1f} kN)** "
                        f"está **dentro** de la región factible."
                    )
                else:
                    st.error(
                        f"❌ El punto manual **(e={e_d:.4f} m, Ps={Ps_d:.1f} kN)** "
                        f"está **fuera** de la región factible.  \n"
                        f"Ajusta e o Ps hasta que el punto quede dentro del polígono verde."
                    )
                    # Mostrar el rango válido de Ps para el e elegido
                    if e_min_val <= e_d <= e_max_geo:
                        lo_e = float(np.interp(e_d, e_arr, lower))
                        up_e = float(np.interp(e_d, e_arr, upper))
                        if lo_e < up_e and up_e > 1e-12:
                            Ps_lo = 1.0 / up_e  # Ps mínimo (1/Ps máximo)
                            Ps_hi = 1.0 / lo_e if lo_e > 1e-12 else float("inf")
                            st.info(
                                f"Para e = {e_d:.4f} m, el rango válido de Ps es:  \n"
                                f"**{Ps_lo:.1f} kN ≤ Ps ≤ {Ps_hi:.1f} kN**"
                            )
            else:
                etiquetas_estrategia = {
                    "max_e":    "Mayor excentricidad factible → Ps mínimo",
                    "min_P":    "Menor fuerza de pretensado (Ps mínimo global)",
                    "centroid": "Centroide ponderado del polígono factible",
                }
                st.success(
                    f"✅ **{etiquetas_estrategia.get(estrategia, estrategia)}**  \n"
                    f"Punto dentro de la región factible."
                )

            # Métricas del punto seleccionado (solo si válido en modo manual, o si automático)
            if punto_en_region or estrategia != "manual":
                c1, c2 = st.columns(2)
                c1.metric("Excentricidad e", f"{e_d:.4f} m")
                c2.metric("Ps diseño", f"{Ps_d:.1f} kN" if Ps_d else "—")
                if Pj_d:
                    st.metric(
                        "Pj = Ps / β",
                        f"{Pj_d:.1f} kN",
                        help=f"Pj = Ps / β = {Ps_d:.1f} / {estado.beta:.3f}",
                    )

                if st.button(
                    "💾 Guardar punto de diseño",
                    type="primary",
                    use_container_width=True,
                    disabled=not punto_en_region and estrategia == "manual",
                ):
                    estado.e  = e_d
                    estado.Pj = Pj_d
                    estado.marcar_completada("magnel")
                    guardar_estado(estado)
                    st.success("Punto de diseño guardado. Continúa en Página 5.")
            else:
                st.caption(
                    "El punto está fuera de la región factible. "
                    "Ajústalo para poder guardarlo."
                )

    # ── Gráfico del diagrama de Magnel ────────────────────────────────
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

        # Región factible (relleno verde)
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
                line=dict(
                    color=color, width=2.0,
                    dash="solid" if bound_type == "upper" else "dash",
                ),
                hovertemplate=(
                    f"<b>{label}</b><br>"
                    "e=%{x:.4f} m<br>"
                    "1/Ps=%{y:.6f} 1/kN<extra></extra>"
                ),
            ))

        # Punto de diseño — color según validez
        if resultado is not None:
            e_d, invPs_d, Ps_d = resultado
            color_punto  = "limegreen" if punto_en_region else "red"
            simbolo_pto  = "star" if punto_en_region else "x"
            nombre_pto   = (
                f"{'✅' if punto_en_region else '❌'} Punto de diseño "
                f"({'dentro' if punto_en_region else 'FUERA'} de la región)"
            )
            fig.add_trace(go.Scatter(
                x=[e_d], y=[invPs_d],
                mode="markers+text",
                marker=dict(color=color_punto, size=14, symbol=simbolo_pto),
                text=[
                    f"  e={e_d:.3f} m<br>"
                    f"  Ps={Ps_d:.0f} kN"
                ],
                textposition="top right",
                name=nombre_pto,
            ))

        # Límite geométrico e_max
        fig.add_vline(
            x=e_max_geo,
            line=dict(color="#888888", dash="dot", width=1.5),
            annotation_text=f"e_max = {e_max_geo:.3f} m",
            annotation_position="top left",
        )

        fig.update_layout(
            xaxis=dict(title="Excentricidad e (m)", gridcolor="#EEEEEE"),
            yaxis=dict(
                title="1/Ps (1/kN)",
                gridcolor="#EEEEEE",
                tickformat=".5f",
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(orientation="h", y=-0.25, font=dict(size=11)),
            hovermode="x unified",
            margin=dict(t=30, b=100, l=80, r=20),
            height=490,
        )
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "**Lectura:** La región verde satisface las 4 condiciones de tensión.  \n"
            "**Mayor 1/Ps** → menor Ps (más económico).  \n"
            "Líneas sólidas = cotas superiores de 1/Ps; "
            "líneas discontinuas = cotas inferiores."
        )

except NotImplementedError:
    st.warning(
        "El tipo de apoyo seleccionado no implementa cálculo de momentos. "
        "Selecciona 'Simplemente apoyada', 'Biempotrada' o 'Voladizo'."
    )
except Exception as err:
    if not estado.etapa_completada("cargas_apoyos"):
        st.info("Completa las etapas 1 y 2 primero.")
    else:
        st.error(f"Error en el diagrama de Magnel: {err}")
        import traceback
        st.code(traceback.format_exc())

guardar_estado(estado)
