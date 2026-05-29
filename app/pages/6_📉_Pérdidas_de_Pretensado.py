"""
Página 6 — Pérdidas de Pretensado

Calcula las pérdidas inmediatas (fricción, asentamiento de anclaje,
acortamiento elástico) y las pérdidas progresivas (modelo simplificado
§9.6.3.4.3 de la NBR 6118:2014).
Muestra gráfico de Pj(x), Pt(x), Ps(x) a lo largo de la viga.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import numpy as np
import streamlit as st

from app.components.state import guardar_estado, mostrar_barra_lateral, obtener_estado
from app.components.plots import graficar_perdidas_pretensado
from app.components.tables import tabla_perdidas_pretensado

st.set_page_config(
    page_title="Pérdidas de Pretensado — Viga Pretensada",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

mostrar_barra_lateral(etapa_actual="perdidas")
estado = obtener_estado()

st.title("📉 Pérdidas de Pretensado")
st.markdown("Cálculo de pérdidas inmediatas y progresivas según NBR 6118:2014 §9.6.3.")

for etapa, nombre in [
    ("armadura_perfil", "5 — Armadura y Perfil"),
]:
    if not estado.etapa_completada(etapa):
        st.warning(f"⚠️ Completa primero la etapa **{nombre}**.")

if estado.Pj is None:
    st.error("Pj no determinado. Completa el Diagrama de Magnel (Página 4).")
    st.stop()

st.divider()

try:
    from src.losses import (
        friction_loss, anchor_slip_loss, elastic_shortening_loss,
        progressive_losses_simplified,
    )

    conc  = estado.get_concrete()
    sec   = estado.get_section()
    steel = estado.get_steel()
    support = estado.get_support()

    Pj = estado.Pj
    n_strands = estado.n_strands or 1
    Aps_total_m2 = n_strands * steel.Aps_unit  # m²

    col_izq, col_der = st.columns([1.1, 1.7], gap="medium")

    with col_izq:
        st.subheader("Parámetros de pérdidas inmediatas")

        mu = st.number_input(
            "Coef. de fricción μ",
            0.05, 0.50, float(estado.mu), 0.01, format="%.3f",
            key="_ni_mu",
            help="Coeficiente de fricción entre el tendón y la vaina. "
                 "Vainas metálicas: μ ≈ 0,20 rad⁻¹ (NBR §9.6.3.3.2.2).",
        )
        k_par = st.number_input(
            "Coef. de pérdidas parásitas k (rad/m)",
            0.0, 0.01, float(estado.k_par), 0.0005, format="%.4f",
            key="_ni_k",
            help="Pérdidas parásitas por unidad de longitud. "
                 "Tendones rectos o suavemente curvos: k ≈ 0,002 rad/m.",
        )
        delta_A_mm = st.number_input(
            "Asentamiento de anclaje ΔA (mm)",
            0.0, 20.0, float(estado.delta_A * 1000), 0.5, format="%.1f",
            key="_ni_deltaA",
            help="Deslizamiento en el anclaje al soltar el gato (mm). "
                 "Typical: 4–8 mm según el tipo de anclaje.",
        )
        n_anclajes = st.selectbox(
            "Extremos con anclaje activo",
            [1, 2], index=0,
            key="_sel_n_anc",
            help="1 extremo activo (tesado por un lado) o 2 (tesado por ambos lados).",
        )
        alpha_total = st.number_input(
            "Desviación angular total α_total (rad)",
            0.0, 1.0,
            float(4 * estado.e_real / estado.L) if estado.e_real and estado.L else 0.0,
            0.01, format="%.4f",
            key="_ni_alpha_total",
            help="Suma de cambios de ángulo del perfil desde el anclaje hasta la sección x. "
                 "Para perfil parabólico: α ≈ 4·e_max/L en el extremo.",
        )

        estado.mu      = mu
        estado.k_par   = k_par
        estado.delta_A = delta_A_mm / 1000.0

        st.divider()
        st.subheader("Parámetros de pérdidas progresivas")

        phi_creep = st.number_input(
            "Coef. de fluencia φ(t∞, t0)",
            0.5, 4.0, float(estado.phi_creep), 0.1, format="%.2f",
            key="_ni_phi",
            help="Coeficiente de fluencia del hormigón según NBR 6118:2014 §8.2.11. "
                 "Valores típicos: 1,5–3,0 para hormigones normales.",
        )
        t0 = st.number_input(
            "Edad al tesar t₀ (días)",
            1.0, 90.0, float(estado.t0), 1.0, format="%.0f",
            key="_ni_t0",
            help="Edad del hormigón en el momento del tesado (días). "
                 "Mayor t₀ → menor fluencia posterior.",
        )
        estado.phi_creep = phi_creep
        estado.t0 = t0

    # ── Cálculo de pérdidas ────────────────────────────────────────────
    L = estado.L

    # Pérdida por fricción (en x = L/2, valor representativo)
    x_mid = L / 2
    dP_fricc_mid = friction_loss(Pj, x_mid, alpha_total, mu=mu, k=k_par)

    # Pérdida por asentamiento de anclaje
    Eps_kPa = steel.Eps * 1000.0  # MPa → kPa
    dP_anc = anchor_slip_loss(Aps_total_m2, Eps_kPa, estado.delta_A, L, n_anclajes)

    # Tensión en el hormigón junto al cable (estimación simple)
    e_eff = estado.e_real or estado.e or sec.yb / 2
    A, I = sec.A, sec.I
    sigma_c_kPa = (Pj / A + Pj * e_eff**2 / I)   # compresión en kPa (aprox.)
    alpha_p = steel.Eps / conc.Eci()              # relación modular

    # Pérdida por acortamiento elástico
    dP_elas = elastic_shortening_loss(
        Aps=Aps_total_m2,
        alpha_p=alpha_p,
        sigma_c=sigma_c_kPa,
        n_cables=n_strands,
    )

    # Pt (tras pérdidas inmediatas)
    Pt_mid = Pj - dP_fricc_mid - dP_anc - dP_elas
    Pt_mid = max(0.0, Pt_mid)

    # Tensión en el hormigón adyacente al cable para modelo simplificado (MPa)
    sigma_c_p0g_MPa = sigma_c_kPa / 1000.0 * (Pt_mid / Pj)  # aprox.

    dP_prog = progressive_losses_simplified(
        Pt=Pt_mid,
        sigma_c_p0g=sigma_c_p0g_MPa,
        alpha_p=alpha_p,
        phi=phi_creep,
    )

    Ps_mid = Pt_mid - dP_prog

    # ── Perfil de fuerzas a lo largo de la viga ────────────────────────
    x_arr = np.linspace(0.0, L, 101)
    Pj_arr = np.full_like(x_arr, Pj)

    # Fricción varía con x (simplificación: perfil parabólico → α(x) ≈ 4*e_max/L * (2x/L) para x≤L/2)
    alpha_x = np.where(x_arr <= L / 2,
                        alpha_total * (2 * x_arr / L),
                        alpha_total * (2 * (L - x_arr) / L))
    dP_fricc_x = np.array([friction_loss(Pj, x, ax, mu=mu, k=k_par)
                             for x, ax in zip(x_arr, alpha_x)])
    Pt_arr = np.clip(Pj_arr - dP_fricc_x - dP_anc - dP_elas, 0, None)

    sigma_c_x = sigma_c_kPa * Pt_arr / Pj  # simplificación proporcional
    dP_prog_x = np.array([
        progressive_losses_simplified(Pt, sc / 1000, alpha_p, phi_creep)
        for Pt, sc in zip(Pt_arr, sigma_c_x)
    ])
    Ps_arr = np.clip(Pt_arr - dP_prog_x, 0, None)

    with col_der:
        st.subheader("Resumen de pérdidas en la sección central")

        df_perdidas = tabla_perdidas_pretensado(
            Pj=Pj,
            delta_P_fricc=dP_fricc_mid,
            delta_P_anc=dP_anc,
            delta_P_elas=dP_elas,
            delta_P_prog=dP_prog,
        )
        st.dataframe(df_perdidas, use_container_width=True, hide_index=True)

        # Métricas de α, β reales
        alpha_real = Pt_mid / Pj if Pj > 0 else 0
        beta_real  = Ps_mid / Pj if Pj > 0 else 0
        eta_real   = Ps_mid / Pt_mid if Pt_mid > 0 else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("α real = Pt/Pj", f"{alpha_real:.3f}",
                  delta=f"{alpha_real - estado.alpha:+.3f}",
                  delta_color="inverse" if alpha_real < estado.alpha - 0.05 else "normal")
        c2.metric("β real = Ps/Pj", f"{beta_real:.3f}",
                  delta=f"{beta_real - estado.beta:+.3f}",
                  delta_color="inverse" if beta_real < estado.beta - 0.05 else "normal")
        c3.metric("η real = Ps/Pt", f"{eta_real:.3f}")

        # Alertas
        if abs(alpha_real - estado.alpha) > 0.05:
            st.warning(
                f"⚠️ α real ({alpha_real:.3f}) difiere significativamente "
                f"del estimado ({estado.alpha:.3f}). Considera actualizar α en la Página 2."
            )
        if abs(beta_real - estado.beta) > 0.05:
            st.warning(
                f"⚠️ β real ({beta_real:.3f}) difiere significativamente "
                f"del estimado ({estado.beta:.3f}). Considera actualizar β en la Página 2."
            )

        st.divider()
        st.subheader("Evolución de la fuerza de pretensado")
        fig_perdidas = graficar_perdidas_pretensado(x_arr, Pj_arr, Pt_arr, Ps_arr)
        st.plotly_chart(fig_perdidas, use_container_width=True)

        st.divider()
        if st.button("💾 Guardar pérdidas →", type="primary", use_container_width=False):
            estado.alpha     = round(alpha_real, 3)
            estado.beta      = round(beta_real, 3)
            estado.marcar_completada("perdidas")
            guardar_estado(estado)
            st.success(
                "Pérdidas calculadas y guardadas. "
                "α y β actualizados con valores reales. "
                "Continúa en Página 7 — Verificaciones."
            )

except NotImplementedError:
    st.warning("El tipo de apoyo no soporta este cálculo. Usa 'Simplemente apoyada'.")
except Exception as err:
    st.error(f"Error en el cálculo de pérdidas: {err}")

guardar_estado(estado)
