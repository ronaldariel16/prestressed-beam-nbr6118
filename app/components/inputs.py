"""
inputs.py
Widgets de entrada estandarizados para la aplicación.

Todas las funciones de este módulo devuelven el valor seleccionado
y son independientes del EstadoProyecto (sin side effects en session_state).
"""
from typing import Dict, List, Tuple

import streamlit as st

# Mapeo de la clave interna del backend → etiqueta en español
USOS_EDIFICACION: Dict[str, str] = {
    "residencial":        "Residencial",
    "comercial":          "Comercial",
    "biblioteca_arquivo": "Biblioteca / Archivo",
    "oficina_garagem":    "Oficina / Garaje",
    "vento":              "Viento",
    "temperatura":        "Temperatura",
}

TIPOS_APOYO: Dict[str, str] = {
    "simplemente_apoyada": "Simplemente apoyada",
    "biempotrada":         "Biempotrada",
    "empotrada_apoyada":   "Empotrada-apoyada",
    "voladizo":            "En voladizo",
    "continua_dos_vanos":  "Continua de dos vanos",
}

TIPOS_PRETENSADO: Dict[str, str] = {
    "pre_traccion":  "Pretracción (pre-tesado, armadura adherente)",
    "pos_traccion":  "Postracción (post-tesado)",
}

NIVELES_PRETENSADO: Dict[str, str] = {
    "completa": "Completa — sin tracción en ELS",
    "limitada": "Limitada — tracción ≤ fct,m en ELS",
    "parcial":  "Parcial — fisuración controlada en ELS",
}

CAA_OPCIONES: Dict[str, str] = {
    "I":   "I — Fuertemente agresivo",
    "II":  "II — Moderadamente agresivo",
    "III": "III — Poco agresivo",
    "IV":  "IV — Muy poco agresivo",
}

TIPOS_PERFIL: Dict[str, str] = {
    "recto":          "Recto (horizontal)",
    "parabolico":     "Parabólico",
    "multiparabolico": "Multiparabólico",
}


def entrada_numero(
    etiqueta: str,
    clave_estado: str,
    valor: float,
    minimo: float,
    maximo: float,
    paso: float,
    ayuda: str,
    formato: str = "%.3f",
) -> float:
    """
    Widget de entrada numérica con validación de rango.

    Args:
        etiqueta:    Texto visible del widget.
        clave_estado: Clave única para session_state.
        valor:       Valor actual (proveniente del estado).
        minimo:      Valor mínimo permitido.
        maximo:      Valor máximo permitido.
        paso:        Incremento del widget.
        ayuda:       Texto de ayuda (tooltip).
        formato:     Formato de visualización printf.

    Returns:
        Valor numérico ingresado por el usuario.
    """
    return st.number_input(
        etiqueta,
        min_value=float(minimo),
        max_value=float(maximo),
        value=float(max(minimo, min(maximo, valor))),
        step=float(paso),
        format=formato,
        key=f"_ni_{clave_estado}",
        help=ayuda,
    )


def entrada_con_slider(
    etiqueta: str,
    clave_estado: str,
    valor: float,
    minimo: float,
    maximo: float,
    paso: float,
    unidad: str,
    ayuda: str,
    formato: str = "%.3f",
) -> float:
    """
    Combina slider y number_input sincronizados para entradas con rango visual.
    Los cambios en el slider se reflejan en el number_input y viceversa.

    Returns:
        Valor seleccionado por el usuario.
    """
    clave_slider = f"_slider_{clave_estado}"
    clave_num    = f"_num_{clave_estado}"

    valor_seguro = float(max(minimo, min(maximo, valor)))

    # Inicializar claves si no existen (primer render)
    if clave_slider not in st.session_state:
        st.session_state[clave_slider] = valor_seguro
    if clave_num not in st.session_state:
        st.session_state[clave_num] = valor_seguro

    def _sync_desde_slider() -> None:
        st.session_state[clave_num] = st.session_state[clave_slider]

    def _sync_desde_numero() -> None:
        st.session_state[clave_slider] = st.session_state[clave_num]

    col_s, col_n = st.columns([3, 1])
    with col_s:
        st.slider(
            etiqueta,
            min_value=float(minimo),
            max_value=float(maximo),
            step=float(paso),
            key=clave_slider,
            on_change=_sync_desde_slider,
            help=ayuda,
        )
    with col_n:
        st.number_input(
            unidad,
            min_value=float(minimo),
            max_value=float(maximo),
            step=float(paso),
            format=formato,
            key=clave_num,
            on_change=_sync_desde_numero,
            label_visibility="visible",
        )

    return float(st.session_state[clave_num])


def selector_hormigon(fck_actual: float, fckj_actual: float) -> Tuple[float, float]:
    """
    Selector de resistencia de hormigón (fck y fckj).

    Returns:
        Tupla (fck, fckj) en MPa.
    """
    FCK_OPCIONES: List[int] = [15, 20, 25, 30, 35, 40, 45, 50]
    idx_fck = FCK_OPCIONES.index(int(fck_actual)) if int(fck_actual) in FCK_OPCIONES else 3

    fck = float(
        st.selectbox(
            "Clase de hormigón",
            options=FCK_OPCIONES,
            index=idx_fck,
            format_func=lambda x: f"C{x}  ({x} MPa)",
            key="_sel_fck",
            help=(
                "Resistencia característica a compresión a los 28 días (fck). "
                "Según NBR 6118:2014 §8.2.4. Rango del proyecto: C15 a C50."
            ),
        )
    )

    fckj = st.number_input(
        "Resistencia al tesado fckj (MPa)",
        min_value=round(0.5 * fck, 1),
        max_value=float(fck),
        value=float(min(fckj_actual, fck)),
        step=1.0,
        format="%.1f",
        key="_ni_fckj",
        help=(
            "Resistencia del hormigón en la edad j del día del tesado. "
            "NBR 6118:2014 §9.6.1.1: para postracción se recomienda fckj ≥ 0,75·fck. "
            "Si se tesa a 28 días, fckj = fck."
        ),
    )

    return fck, fckj


def selector_factor_agregado(alpha_E_actual: float) -> float:
    """
    Selector del factor αE según el tipo de árido grueso.

    Returns:
        Valor de alpha_E.
    """
    opciones = {
        1.0: "Granito / Gneiss (αE = 1,0)",
        0.9: "Basalto / Diabásio (αE = 0,9)",
        0.7: "Caliza (αE = 0,7)",
        0.5: "Arenisca (αE = 0,5)",
    }
    valores = list(opciones.keys())
    idx = valores.index(alpha_E_actual) if alpha_E_actual in valores else 0

    return float(
        st.selectbox(
            "Tipo de árido grueso (αE)",
            options=valores,
            index=idx,
            format_func=lambda x: opciones[x],
            key="_sel_alpha_E",
            help=(
                "Factor que ajusta el módulo de elasticidad según el tipo de árido grueso "
                "(NBR 6118:2014 §8.2.8). Granito y gneiss son los más rígidos; "
                "arenisca el más deformable."
            ),
        )
    )


def selector_acero_pretensado(diametro_actual: float) -> float:
    """
    Selector de diámetro de cordón CP-190 RB.

    Returns:
        Diámetro seleccionado en mm.
    """
    from src.materials import CP_190_RB_CATALOG

    diametros = sorted(CP_190_RB_CATALOG.keys())
    idx = diametros.index(diametro_actual) if diametro_actual in diametros else len(diametros) - 1

    return float(
        st.selectbox(
            "Cordón CP-190 RB — diámetro",
            options=diametros,
            index=idx,
            format_func=lambda d: (
                f"Ø {d} mm — {CP_190_RB_CATALOG[d]['fios']} hilos — "
                f"A={CP_190_RB_CATALOG[d]['A_mm2']} mm² — "
                f"Pptk={CP_190_RB_CATALOG[d]['Pptk_kN']:.1f} kN"
            ),
            key="_sel_steel_diam",
            help=(
                "Cordón de acero de pretensado tipo CP-190 RB según catálogo ArcelorMittal "
                "y NBR 6118:2014 §8.4. Los cordones de 3 hilos van de Ø 6,5 a Ø 11,1 mm; "
                "los de 7 hilos van de Ø 9,5 a Ø 15,2 mm."
            ),
        )
    )


def selector_tipo_apoyo(tipo_actual: str) -> str:
    """
    Selector del tipo de condición de apoyo.

    Returns:
        Clave interna del tipo de apoyo.
    """
    opciones = list(TIPOS_APOYO.keys())
    idx = opciones.index(tipo_actual) if tipo_actual in opciones else 0

    return str(
        st.selectbox(
            "Condición de apoyo",
            options=opciones,
            index=idx,
            format_func=lambda k: TIPOS_APOYO[k],
            key="_sel_apoyo",
            help=(
                "Define el esquema estático de la viga. "
                "Simplemente apoyada: sin momentos en los extremos. "
                "Biempotrada: momentos negativos en ambos extremos. "
                "Empotrada-apoyada: empote en un extremo, apoyo en el otro. "
                "Voladizo: empote en un extremo, extremo libre. "
                "Continua de dos vanos: viga continua con apoio central."
            ),
        )
    )


def selector_nivel_pretensado(nivel_actual: str) -> str:
    """
    Selector del nivel de pretensado según NBR 6118:2014 Tabla 13.4.

    Returns:
        Clave interna del nivel: 'completa' | 'limitada' | 'parcial'.
    """
    opciones = list(NIVELES_PRETENSADO.keys())
    idx = opciones.index(nivel_actual) if nivel_actual in opciones else 0

    return str(
        st.selectbox(
            "Nivel de pretensado",
            options=opciones,
            index=idx,
            format_func=lambda k: NIVELES_PRETENSADO[k],
            key="_sel_nivel_prot",
            help=(
                "Define los límites de tensión en ELS — NBR 6118:2014 §13.3.4.2 / Tabla 13.4. "
                "Pretensado completo: no se permiten tracciones en el hormigón. "
                "Limitado: se toleran pequeñas tracciones (≤ fct,m). "
                "Parcial: se admite fisuración controlada."
            ),
        )
    )


def selector_tipo_pretensado(tipo_actual: str) -> str:
    """
    Selector del tipo de pretensado (pre o postracción).

    Returns:
        Clave interna: 'pre_traccion' | 'pos_traccion'.
    """
    opciones = list(TIPOS_PRETENSADO.keys())
    idx = opciones.index(tipo_actual) if tipo_actual in opciones else 1

    return str(
        st.selectbox(
            "Tipo de pretensado",
            options=opciones,
            index=idx,
            format_func=lambda k: TIPOS_PRETENSADO[k],
            key="_sel_tipo_prot",
            help=(
                "Pretracción (pre-tesado): el acero se tensa antes del hormigonado; "
                "armadura siempre adherente. "
                "Postracción (post-tesado): el acero se tensa después del endurecimiento "
                "del hormigón; puede ser adherente (con inyección de lechada) o no adherente."
            ),
        )
    )


def selector_uso_edificacion(uso_actual: str) -> str:
    """
    Selector del uso de la edificación (para coeficientes ψ de NBR 6118).

    Returns:
        Clave interna compatible con PSI_TABLE del backend.
    """
    opciones = list(USOS_EDIFICACION.keys())
    idx = opciones.index(uso_actual) if uso_actual in opciones else 0

    return str(
        st.selectbox(
            "Uso de la edificación",
            options=opciones,
            index=idx,
            format_func=lambda k: USOS_EDIFICACION[k],
            key="_sel_uso",
            help=(
                "Uso principal de la edificación, empleado para determinar los coeficientes "
                "de reducción ψ0, ψ1, ψ2 de las sobrecargas según NBR 6118:2014 Tabla 11.4."
            ),
        )
    )
