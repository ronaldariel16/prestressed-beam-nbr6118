"""
Página 8 — Informe Final

Resumen ejecutivo completo del proyecto con descarga en:
  · JSON  (estado completo del proyecto)
  · Markdown (.md)
  · Excel (.xlsx) con varias hojas
"""
import io
import json
import sys
from datetime import datetime
from pathlib import Path

_ROOT = Path(__file__).parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from app.components.state import (
    ETAPAS, NOMBRES_ETAPAS,
    guardar_estado, mostrar_barra_lateral, obtener_estado,
)

st.set_page_config(
    page_title="Informe Final — Viga Pretensada",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

_CSS = Path(__file__).parent.parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

mostrar_barra_lateral(etapa_actual="informe")
estado = obtener_estado()

st.title("📑 Informe Final")
st.markdown("Resumen ejecutivo del proyecto y archivos para descarga.")

st.divider()

# ── Barra de progreso del proyecto ────────────────────────────────────────
pct = estado.progreso()
st.progress(pct, text=f"Progreso total del proyecto: {pct*100:.0f}%")

etapas_pendientes = [e for e in ETAPAS if not estado.etapa_completada(e)]
if etapas_pendientes:
    pendientes_str = ", ".join(NOMBRES_ETAPAS[e] for e in etapas_pendientes)
    st.warning(f"⚠️ Etapas pendientes: {pendientes_str}")

st.divider()

# ════════════════════════════════════════════════════════════════════════
# Resumen ejecutivo
# ════════════════════════════════════════════════════════════════════════
st.subheader("Resumen ejecutivo")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    st.markdown("#### Geometría")
    st.markdown(
        f"| Parámetro | Valor |\n"
        f"|-----------|-------|\n"
        f"| b | {estado.b*100:.0f} cm |\n"
        f"| h | {estado.h*100:.0f} cm |\n"
        f"| A | {estado.b*estado.h*1e4:.1f} cm² |"
    )

with col_b:
    st.markdown("#### Materiales")
    st.markdown(
        f"| Parámetro | Valor |\n"
        f"|-----------|-------|\n"
        f"| Hormigón | C{int(estado.fck)} |\n"
        f"| fckj | {estado.fckj:.0f} MPa |\n"
        f"| Acero | CP-190 RB |\n"
        f"| Ø | {estado.steel_diameter:.1f} mm |"
    )

with col_c:
    st.markdown("#### Pretensado")
    pj_str = f"{estado.Pj:.1f} kN" if estado.Pj else "—"
    e_str  = f"{estado.e:.4f} m"  if estado.e  else "—"
    n_str  = str(estado.n_strands) if estado.n_strands else "—"
    st.markdown(
        f"| Parámetro | Valor |\n"
        f"|-----------|-------|\n"
        f"| Nivel | {estado.prestress_level} |\n"
        f"| Tipo | {estado.prestress_type} |\n"
        f"| Pj | {pj_str} |\n"
        f"| e diseño | {e_str} |\n"
        f"| Cordones | {n_str} |"
    )

with col_d:
    st.markdown("#### Apoyos y cargas")
    tipo_apoyo_es = {
        "simplemente_apoyada": "Simp. apoyada",
        "biempotrada": "Biempotrada",
        "empotrada_apoyada": "Emp.-apoyada",
        "voladizo": "Voladizo",
        "continua_dos_vanos": "Continua",
    }.get(estado.support_type, estado.support_type)
    st.markdown(
        f"| Parámetro | Valor |\n"
        f"|-----------|-------|\n"
        f"| Apoyo | {tipo_apoyo_es} |\n"
        f"| L | {estado.L:.1f} m |\n"
        f"| gk | {estado.gk:.1f} kN/m |\n"
        f"| qk | {estado.qk:.1f} kN/m |"
    )

st.divider()

# ── Verificaciones OK/FALLO ───────────────────────────────────────────────
st.subheader("Estado de las verificaciones")

try:
    from src.uls_flexure import MRd_simplified, Mlim_rectangular
    from src.stress_check import stresses_at_section, check_stresses
    from src.stress_limits import stress_limits
    from src.loads import Md_ULS

    if estado.Pj and estado.etapa_completada("magnel"):
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
        Aps = n_strands * steel.Aps_unit
        dp  = sec.h - (sec.yb - e)

        pp = sec.A * conc.gamma_concrete
        x_c, _ = support.critical_sections()[0]
        Msw_c = abs(support.M_uniform(x_c, pp))
        Mgk_c = abs(support.M_uniform(x_c, loads.gk))
        Mqk_c = abs(support.M_uniform(x_c, loads.qk))
        Mse_c = Msw_c + Mgk_c + Mqk_c
        Msd_c = Md_ULS(Msw_c + Mgk_c, Mqk_c)

        MRd = MRd_simplified(dp, Aps, steel.fpd)
        elu_ok = MRd >= Msd_c

        st_top, st_bot = stresses_at_section(Pt, e, Msw_c, sec)
        res_tr = check_stresses(st_top, st_bot, lim, 'transfer')

        ss_top, ss_bot = stresses_at_section(Ps, e, Mse_c, sec)
        res_sv = check_stresses(ss_top, ss_bot, lim, 'service')

        verif_cols = st.columns(4)
        verif_cols[0].metric("ELU Flexión",
                              "✅ OK" if elu_ok else "❌ FALLO",
                              f"MRd/Msd = {MRd/Msd_c:.2f}" if Msd_c > 0 else "—")
        verif_cols[1].metric("ELS Transferencia",
                              "✅ OK" if res_tr.ok else "❌ FALLO")
        verif_cols[2].metric("ELS Servicio",
                              "✅ OK" if res_sv.ok else "❌ FALLO")
        verif_cols[3].metric("Cordones / Pj",
                              f"{n_strands} × Ø{steel.diameter:.1f}mm",
                              f"Pj = {n_strands * steel.Pj_lim_unit():.0f} kN")

except NotImplementedError:
    st.info("El tipo de apoyo no permite calcular verificaciones automáticamente.")
except Exception as err:
    st.info(f"Verificaciones no disponibles: {err}")

st.divider()

# ════════════════════════════════════════════════════════════════════════
# Generación de documentos
# ════════════════════════════════════════════════════════════════════════
st.subheader("Descargas")

fecha = datetime.now().strftime("%Y-%m-%d %H:%M")


def _generar_markdown() -> str:
    """Genera el informe en formato Markdown."""
    pj_str = f"{estado.Pj:.2f} kN" if estado.Pj else "No calculado"
    e_str  = f"{estado.e:.4f} m"   if estado.e  else "No calculado"
    n_str  = str(estado.n_strands)  if estado.n_strands else "No calculado"
    Ps_str = f"{estado.Pj * estado.beta:.2f} kN" if estado.Pj else "No calculado"

    lineas = [
        "# Informe de Dimensionamiento — Viga de Hormigón Pretensado",
        f"**Fecha:** {fecha}",
        f"**Norma de referencia:** NBR 6118:2014",
        "",
        "---",
        "",
        "## 1. Geometría de la sección transversal",
        f"- Ancho b = {estado.b*100:.1f} cm = {estado.b:.3f} m",
        f"- Altura h = {estado.h*100:.1f} cm = {estado.h:.3f} m",
        f"- Área A = {estado.b*estado.h:.4f} m²",
        f"- Inercia I = {estado.b*estado.h**3/12:.6e} m⁴",
        f"- Módulo seccional zt = zb = {estado.b*estado.h**2/6:.6e} m³",
        "",
        "## 2. Materiales",
        f"- Hormigón: C{int(estado.fck)} (fck = {estado.fck:.1f} MPa, fckj = {estado.fckj:.1f} MPa)",
        f"- Acero de pretensado: CP-190 RB Ø {estado.steel_diameter:.1f} mm",
        "",
        "## 3. Condición de apoyo y cargas",
        f"- Tipo de apoyo: {estado.support_type}",
        f"- Luz L = {estado.L:.2f} m",
        f"- Carga permanente gk = {estado.gk:.2f} kN/m",
        f"- Sobrecarga qk = {estado.qk:.2f} kN/m",
        f"- Uso: {estado.usage}",
        "",
        "## 4. Pretensado",
        f"- Nivel de pretensado: {estado.prestress_level}",
        f"- Tipo: {estado.prestress_type}",
        f"- Coef. de pérdidas estimados: α = {estado.alpha:.3f}, β = {estado.beta:.3f}",
        f"- Fuerza de pretensado Pj = {pj_str}",
        f"- Fuerza en servicio Ps = {Ps_str}",
        f"- Excentricidad de diseño e = {e_str}",
        f"- Número de cordones: {n_str}",
        f"- Tipo de perfil: {estado.profile_type}",
        "",
        "## 5. Estado de las etapas",
    ]
    for etapa in ETAPAS:
        estado_str = "✅ Completada" if estado.etapa_completada(etapa) else "⬜ Pendiente"
        lineas.append(f"- {NOMBRES_ETAPAS[etapa]}: {estado_str}")

    lineas += [
        "",
        "---",
        "",
        "*Informe generado automáticamente. Verificar con ingeniero responsable.*",
        "*Herramienta desarrollada con Streamlit — NBR 6118:2014 | Torii (2020)*",
    ]
    return "\n".join(lineas)


def _generar_excel() -> bytes:
    """Genera el archivo Excel con varias hojas."""
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        # Hoja 1 — Resumen
        df_res = pd.DataFrame([
            ("b (m)", estado.b),
            ("h (m)", estado.h),
            ("fck (MPa)", estado.fck),
            ("fckj (MPa)", estado.fckj),
            ("Diámetro cordón (mm)", estado.steel_diameter),
            ("L (m)", estado.L),
            ("gk (kN/m)", estado.gk),
            ("qk (kN/m)", estado.qk),
            ("Nivel pretensado", estado.prestress_level),
            ("Tipo pretensado", estado.prestress_type),
            ("α = Pt/Pj", estado.alpha),
            ("β = Ps/Pj", estado.beta),
            ("Pj (kN)", estado.Pj or "—"),
            ("e diseño (m)", estado.e or "—"),
            ("Nº cordones", estado.n_strands or "—"),
            ("Perfil tendón", estado.profile_type),
        ], columns=["Parámetro", "Valor"])
        df_res.to_excel(writer, sheet_name="Resumen", index=False)

        # Hoja 2 — Propiedades de la sección
        try:
            from app.components.tables import tabla_propiedades_seccion
            sec = estado.get_section()
            df_geom = tabla_propiedades_seccion(sec)
            df_geom.to_excel(writer, sheet_name="Geometría", index=False)
        except Exception:
            pass

        # Hoja 3 — Propiedades de materiales
        try:
            from app.components.tables import tabla_propiedades_hormigon, tabla_propiedades_acero
            conc  = estado.get_concrete()
            steel = estado.get_steel()
            df_conc  = tabla_propiedades_hormigon(conc, estado.alpha_E)
            df_steel = tabla_propiedades_acero(steel)
            df_conc.to_excel(writer,  sheet_name="Hormigón", index=False)
            df_steel.to_excel(writer, sheet_name="Acero",    index=False)
        except Exception:
            pass

        # Hoja 4 — Estado del proyecto
        df_etapas = pd.DataFrame([
            (NOMBRES_ETAPAS[e], "Completada" if estado.etapa_completada(e) else "Pendiente")
            for e in ETAPAS
        ], columns=["Etapa", "Estado"])
        df_etapas.to_excel(writer, sheet_name="Progreso", index=False)

    buf.seek(0)
    return buf.getvalue()


# ── Botones de descarga ────────────────────────────────────────────────────
col_dl1, col_dl2, col_dl3 = st.columns(3)

with col_dl1:
    st.download_button(
        label="💾 Proyecto JSON",
        data=json.dumps(estado.to_dict(), ensure_ascii=False, indent=2),
        file_name=f"viga_pretensada_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json",
        use_container_width=True,
        help="Exporta el estado completo del proyecto en formato JSON.",
    )

with col_dl2:
    md_content = _generar_markdown()
    st.download_button(
        label="📄 Informe Markdown",
        data=md_content.encode("utf-8"),
        file_name=f"informe_viga_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
        use_container_width=True,
        help="Descarga el informe técnico en formato Markdown.",
    )

with col_dl3:
    try:
        xlsx_data = _generar_excel()
        st.download_button(
            label="📊 Planilla Excel",
            data=xlsx_data,
            file_name=f"viga_pretensada_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            help="Descarga la planilla Excel con resumen, geometría, materiales y progreso.",
        )
    except Exception as e_xl:
        st.warning(f"Excel no disponible: {e_xl}")

st.divider()

# ── Vista previa del informe Markdown ─────────────────────────────────────
with st.expander("👁️ Vista previa del informe", expanded=False):
    st.markdown(md_content)

st.divider()
if st.button("✅ Marcar proyecto como completo", type="primary",
             use_container_width=False):
    estado.marcar_completada("informe")
    guardar_estado(estado)
    st.success("🎉 ¡Proyecto completado! Todas las etapas han sido marcadas.")
    st.balloons()

guardar_estado(estado)
