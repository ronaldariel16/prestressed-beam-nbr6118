"""
streamlit_app.py
Punto de entrada principal de la aplicación.

Ejecución:
    streamlit run app/streamlit_app.py
"""
import json
import sys
from pathlib import Path

# Añadir la raíz del proyecto al path para importar src/ y app/
_ROOT = Path(__file__).parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.components.state import (
    EstadoProyecto,
    ETAPAS,
    ICONOS_ETAPAS,
    NOMBRES_ETAPAS,
    guardar_estado,
    obtener_estado,
    reiniciar_estado,
)

# ── Configuración de la página ────────────────────────────────────────────
st.set_page_config(
    page_title="Vigas Pretensadas — NBR 6118:2014",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": (
            "**Dimensionamiento de Vigas de Hormigón Pretensado**\n\n"
            "Basado en NBR 6118:2014 y el manual de Torii (2020).\n"
            "Sección rectangular • Cualquier condición de apoyo • C15–C50."
        ),
    },
)

# ── Cargar CSS personalizado ──────────────────────────────────────────────
_CSS = Path(__file__).parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True)

# ── Estado del proyecto ───────────────────────────────────────────────────
estado = obtener_estado()

# ── Barra lateral ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ Proyecto actual")

    pct = estado.progreso()
    st.markdown(f"**Progreso:** {pct*100:.0f}%")
    st.progress(pct)

    st.markdown("**Etapas:**")
    for etapa in ETAPAS:
        icono   = ICONOS_ETAPAS.get(etapa, "")
        nombre  = NOMBRES_ETAPAS.get(etapa, etapa)
        hecho   = estado.etapa_completada(etapa)
        st.markdown(
            f"{'✅' if hecho else '⬜'} {icono} {nombre}"
        )

    st.divider()

    col_n, col_r = st.columns(2)
    with col_n:
        if st.button("🆕 Nuevo", use_container_width=True,
                     help="Crea un proyecto nuevo, borrando todos los datos actuales."):
            reiniciar_estado()
            st.rerun()
    with col_r:
        if st.button("🔄 Reiniciar", use_container_width=True,
                     help="Vuelve a los valores por defecto del proyecto actual."):
            reiniciar_estado()
            st.rerun()

    st.download_button(
        label="💾 Descargar proyecto (.json)",
        data=json.dumps(estado.to_dict(), ensure_ascii=False, indent=2),
        file_name="proyecto_viga.json",
        mime="application/json",
        use_container_width=True,
        help="Descarga el proyecto en formato JSON para continuar después.",
    )

    archivo_carga = st.file_uploader(
        "📂 Cargar proyecto (.json)",
        type=["json"],
        help="Sube un archivo JSON guardado previamente para reanudar el diseño.",
    )
    if archivo_carga is not None:
        try:
            datos = json.load(archivo_carga)
            guardar_estado(EstadoProyecto.from_dict(datos))
            st.success("Proyecto cargado correctamente.")
            st.rerun()
        except Exception as exc:
            st.error(f"Error al cargar el proyecto: {exc}")

# ── Contenido principal ───────────────────────────────────────────────────
st.title("🏗️ Dimensionamiento de Vigas de Hormigón Pretensado")
st.markdown(
    "**Sección rectangular** &nbsp;|&nbsp; "
    "Cualquier condición de apoyo &nbsp;|&nbsp; "
    "Hormigones hasta **C50** &nbsp;|&nbsp; "
    "Basado en **NBR 6118:2014**"
)

st.divider()

# ── Descripción del flujo de trabajo ─────────────────────────────────────
st.subheader("Flujo de trabajo")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    #### Etapas del dimensionamiento

    Esta aplicación guía el proceso completo de dimensionamiento de una
    viga de hormigón pretensado con sección rectangular, siguiendo la
    secuencia del manual de Torii (2020) y la norma **NBR 6118:2014**:

    | Etapa | Descripción |
    |-------|-------------|
    | **1** | Definir geometría de la sección y materiales |
    | **2** | Establecer condición de apoyo y cargas |
    | **3** | Predimensionamiento (altura mínima) |
    | **4** | Diagrama de Magnel — determinar Pj y excentricidad |
    | **5** | Disposición de cordones y perfil del tendón |
    | **6** | Cálculo de pérdidas de pretensado |
    | **7** | Verificaciones ELU (flexión) y ELS (tensiones, flechas) |
    | **8** | Generación del informe final |

    Navega entre páginas usando el menú de la izquierda.
    Los datos se conservan automáticamente entre páginas.
    """)

with col_b:
    st.markdown("""
    #### Alcance y limitaciones

    - **Tipo de sección:** Rectangular (b × h)
    - **Norma:** NBR 6118:2014
    - **Hormigones:** C15 a C50
    - **Acero:** CP-190 RB (catálogo ArcelorMittal)
    - **Apoyos:** Simplemente apoyado, biempotrado, empotrado-apoyado,
      voladizo, continua de dos vanos
    - **Pretensado:** Pre-tracción y postracción

    #### Cómo empezar

    1. Usa el botón **🆕 Nuevo** en la barra lateral para iniciar un proyecto limpio.
    2. Ve a la página **📐 Geometría y Materiales** para definir la sección.
    3. Continúa secuencialmente hasta obtener el **📑 Informe Final**.

    También puedes cargar un proyecto existente en formato JSON con el
    botón **📂 Cargar proyecto** de la barra lateral.
    """)

st.divider()

# ── Estado actual del proyecto (resumen) ──────────────────────────────────
st.subheader("Estado actual del proyecto")

cols = st.columns(4)

with cols[0]:
    if estado.etapa_completada("geometria_materiales"):
        st.metric(
            label="Sección",
            value=f"{estado.b*100:.0f}×{estado.h*100:.0f} cm",
            help="Ancho × altura de la sección transversal.",
        )
        st.metric(
            label="Hormigón",
            value=f"C{int(estado.fck)}",
            help="Clase de resistencia del hormigón.",
        )
    else:
        st.info("Geometría no definida aún.")

with cols[1]:
    if estado.etapa_completada("cargas_apoyos"):
        tipo_label = {
            "simplemente_apoyada": "Simp. apoyada",
            "biempotrada": "Biempotrada",
            "empotrada_apoyada": "Emp.-apoyada",
            "voladizo": "Voladizo",
            "continua_dos_vanos": "Continua",
        }.get(estado.support_type, estado.support_type)
        st.metric(label="Apoyo", value=tipo_label)
        st.metric(label="Luz", value=f"{estado.L:.1f} m")
    else:
        st.info("Apoyo y cargas no definidos.")

with cols[2]:
    if estado.Pj is not None:
        st.metric(label="Fuerza Pj", value=f"{estado.Pj:.1f} kN")
        st.metric(label="Excentricidad e", value=f"{estado.e:.3f} m")
    else:
        st.info("Pretensado no determinado aún.")

with cols[3]:
    if estado.n_strands is not None:
        st.metric(label="Nº cordones", value=str(estado.n_strands))
    else:
        st.info("Armadura no dimensionada.")

st.divider()
st.caption(
    "Desarrollado como herramienta de apoyo al dimensionamiento. "
    "Siempre verifique los resultados con un ingeniero responsable. "
    "Referencia: **Torii, A. J. (2020)** — *Concreto Protendido*; **NBR 6118:2014**."
)
