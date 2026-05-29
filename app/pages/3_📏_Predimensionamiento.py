"""
Página 3 — Predimensionamiento

Calcula la altura mínima requerida mediante dos criterios:
  · General    (Eqs. 6.9/6.10 del manual) — considera η, Msw y Mse
  · Simplificado (Eq. 6.13) — solo Mse y fsc
Sugiere h ajustada al múltiplo de 5 cm superior.
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.components.state import guardar_estado, mostrar_barra_lateral, obtener_estado

st.set_page_config(
    page_title="Predimensionamiento — Viga Pretensada",
    page_icon="📏",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

mostrar_barra_lateral(etapa_actual="predimensionamiento")
estado = obtener_estado()

st.title("📏 Predimensionamiento")

for etapa, nombre in [
    ("geometria_materiales", "1 — Geometría y Materiales"),
    ("cargas_apoyos",        "2 — Cargas y Apoyos"),
]:
    if not estado.etapa_completada(etapa):
        st.warning(f"⚠️ Completa primero la etapa **{nombre}**.")

st.divider()

try:
    from src.presizing import presize_general, presize_simplified, min_height_rectangular, round_up_to_step
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
    b   = estado.b

    # ── Cálculo de los dos criterios ─────────────────────────────────────
    zt_gen, zb_gen  = presize_general(Mse, Msw, eta, lim)
    zt_sim, zb_sim  = presize_simplified(Mse, eta, lim)

    h_gen = min_height_rectangular(b, zt_gen, zb_gen)
    h_sim = min_height_rectangular(b, zt_sim, zb_sim)
    h_adop_gen = round_up_to_step(h_gen,  0.05)
    h_adop_sim = round_up_to_step(h_sim,  0.05)
    h_actual   = estado.h

    # ── Layout ───────────────────────────────────────────────────────────
    col_izq, col_der = st.columns([1.2, 1.5], gap="medium")

    with col_izq:
        st.subheader("Datos de entrada")
        st.markdown(
            f"| Parámetro | Valor |\n"
            f"|-----------|-------|\n"
            f"| Ancho b | **{b*100:.1f} cm** |\n"
            f"| Msw (peso propio) | **{Msw:.2f} kN·m** |\n"
            f"| Mgk (carga perm.) | **{Mgk:.2f} kN·m** |\n"
            f"| Mqk (sobrecarga) | **{Mqk:.2f} kN·m** |\n"
            f"| Mse (total serv.) | **{Mse:.2f} kN·m** |\n"
            f"| η = Ps/Pt | **{eta:.3f}** |\n"
            f"| fsc | **{lim.fsc:.2f} MPa** |\n"
            f"| ftt | **{lim.ftt:.2f} MPa** |\n"
            f"| ftc | **{lim.ftc:.2f} MPa** |"
        )

        st.divider()
        st.subheader("Tabla comparativa de criterios")
        import pandas as pd
        df = pd.DataFrame({
            "Criterio":         ["General (Eq. 6.9/6.10)", "Simplificado (Eq. 6.13)"],
            "zb_req (m³)":      [f"{zb_gen:.6f}", f"{zb_sim:.6f}"],
            "zt_req (m³)":      [f"{zt_gen:.6f}", f"{zt_sim:.6f}"],
            "h_min (m)":        [f"{h_gen:.4f}", f"{h_sim:.4f}"],
            "h_min (cm)":       [f"{h_gen*100:.1f}", f"{h_sim*100:.1f}"],
            "h adoptada (cm)":  [f"{h_adop_gen*100:.0f}", f"{h_adop_sim*100:.0f}"],
        })
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Indicadores respecto a h actual
        st.divider()
        c1, c2 = st.columns(2)
        c1.metric("h actual", f"{h_actual*100:.0f} cm")
        c2.metric("h mín. general", f"{h_gen*100:.1f} cm",
                  delta=f"{(h_actual - h_gen)*100:.1f} cm",
                  delta_color="normal")

        if h_actual >= h_gen:
            st.success(f"✅ La altura actual h = {h_actual*100:.0f} cm es **suficiente** "
                       f"(≥ {h_gen*100:.1f} cm requerido por criterio general).")
        else:
            st.error(f"❌ La altura actual h = {h_actual*100:.0f} cm es **insuficiente**. "
                     f"Se requiere ≥ {h_gen*100:.1f} cm (criterio general).")

    with col_der:
        st.subheader("Sugerencia de altura")

        h_suger = max(h_adop_gen, h_adop_sim)
        st.metric(
            "h sugerida (múltiplo 5 cm más próximo por encima)",
            f"{h_suger*100:.0f} cm = {h_suger:.2f} m",
            help="Altura recomendada redondeada al múltiplo de 5 cm inmediatamente superior.",
        )

        # Verificación con h sugerida
        from src.geometry import RectangularSection
        sec_nueva = RectangularSection(b=b, h=h_suger)
        st.markdown(
            f"""
            **Con h = {h_suger*100:.0f} cm:**
            - A = {sec_nueva.A*1e4:.1f} cm²
            - I = {sec_nueva.I*1e8:.2f} cm⁴
            - z = zt = zb = {sec_nueva.zt*1e6:.1f} cm³
            - z/zb_req (general) = {sec_nueva.zb/zb_gen:.3f} {"✅" if sec_nueva.zb >= zb_gen else "❌"}
            - z/zb_req (simplif) = {sec_nueva.zb/zb_sim:.3f} {"✅" if sec_nueva.zb >= zb_sim else "❌"}
            """
        )

        st.divider()
        st.markdown(
            """
            **Notas sobre los criterios:**

            - **General (Eqs. 6.9/6.10):** Combina las condiciones de servicio
              y del acto de transferencia para determinar el módulo seccional
              mínimo sin conocer P ni e. Es más preciso al incluir η y Msw.

            - **Simplificado (Eq. 6.13):** Usa solo Mse y el límite de compresión
              de servicio |fsc|. Es conservador pero rápido para una estimación inicial.

            - En vigas simplemente apoyadas el criterio **determinante** suele ser
              la fibra inferior (zb), que controla la compresión de servicio.
            """
        )

        if st.button(
            f"📐 Actualizar geometría → h = {h_suger*100:.0f} cm",
            type="primary",
            use_container_width=True,
            help="Aplica la altura sugerida como nueva altura en la Página 1.",
        ):
            estado.h = h_suger
            estado.marcar_completada("predimensionamiento")
            guardar_estado(estado)
            st.success(
                f"Altura actualizada a h = {h_suger*100:.0f} cm. "
                "El cambio se refleja en la Página 1 (Geometría y Materiales)."
            )

except NotImplementedError:
    st.warning("El tipo de apoyo seleccionado aún no tiene cálculo de momentos. "
               "Usa 'Simplemente apoyada', 'Biempotrada' o 'Voladizo'.")
except Exception as err:
    if not estado.etapa_completada("geometria_materiales"):
        st.info("Completa las etapas 1 y 2 para ver los resultados de predimensionamiento.")
    else:
        st.error(f"Error en el cálculo de predimensionamiento: {err}")

guardar_estado(estado)
