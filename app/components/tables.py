"""
tables.py
Formateadores de tablas pandas para presentar resultados del backend.

Cada función recibe instancias del backend (o valores calculados)
y devuelve un pd.DataFrame listo para st.dataframe() o st.table().
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd


# ══════════════════════════════════════════════════════════════════════════
# Geometría
# ══════════════════════════════════════════════════════════════════════════

def tabla_propiedades_seccion(section) -> pd.DataFrame:
    """
    Tabla con las propiedades geométricas de la sección transversal.

    Args:
        section: Instancia de RectangularSection.

    Returns:
        DataFrame con columnas: Propiedad, Símbolo, Valor, Unidad.
    """
    filas = [
        ("Ancho",                          "b",    f"{section.b*100:.2f}",    "cm"),
        ("Altura",                         "h",    f"{section.h*100:.2f}",    "cm"),
        ("Área de la sección",             "A",    f"{section.A:.6f}",        "m²"),
        ("Momento de inercia",             "I",    f"{section.I:.8f}",        "m⁴"),
        ("Dist. fibra superior",           "yt",   f"{section.yt:.4f}",       "m"),
        ("Dist. fibra inferior",           "yb",   f"{section.yb:.4f}",       "m"),
        ("Módulo seccional superior",      "zt",   f"{section.zt:.6f}",       "m³"),
        ("Módulo seccional inferior",      "zb",   f"{section.zb:.6f}",       "m³"),
    ]
    return pd.DataFrame(filas, columns=["Propiedad", "Símbolo", "Valor", "Unidad"])


# ══════════════════════════════════════════════════════════════════════════
# Materiales
# ══════════════════════════════════════════════════════════════════════════

def tabla_propiedades_hormigon(concrete, alpha_E: float = 1.0) -> pd.DataFrame:
    """
    Tabla con las propiedades mecánicas del hormigón.

    Args:
        concrete: Instancia de Concrete.
        alpha_E:  Factor del árido grueso (para Eci, Ecs).

    Returns:
        DataFrame con columnas: Propiedad, Símbolo, Valor, Unidad, Referencia.
    """
    Eci   = concrete.Eci(alpha_E)
    Ecs   = concrete.Ecs(alpha_E)
    Eci_j = concrete.Eci_j(alpha_E)

    filas = [
        ("Resist. característica (28 d.)",   "fck",    f"{concrete.fck:.1f}",    "MPa",  "§8.2.4"),
        ("Resist. al día del tesado",         "fckj",   f"{concrete.fckj:.1f}",   "MPa",  "§9.6.1.1"),
        ("Resist. de cálculo",                "fcd",    f"{concrete.fcd:.2f}",    "MPa",  "§8.2.4"),
        ("Módulo tang. inicial",              "Eci",    f"{Eci:.1f}",             "MPa",  "§8.2.8"),
        ("Módulo secante",                    "Ecs",    f"{Ecs:.1f}",             "MPa",  "§8.2.8"),
        ("Módulo tang. en edad j",            "Eci,j",  f"{Eci_j:.1f}",           "MPa",  "§8.2.8"),
        ("Resist. media a tracción (28 d.)",  "fct,m",  f"{concrete.fct_m:.3f}",  "MPa",  "§8.2.5"),
        ("Resist. media a tracción (edad j)", "fct,mj", f"{concrete.fct_mj:.3f}", "MPa",  "§8.2.5"),
    ]
    return pd.DataFrame(filas, columns=["Propiedad", "Símbolo", "Valor", "Unidad", "Ref. NBR"])


def tabla_propiedades_acero(steel) -> pd.DataFrame:
    """
    Tabla con las propiedades del acero de pretensado.

    Args:
        steel: Instancia de PrestressSteel.

    Returns:
        DataFrame con columnas: Propiedad, Símbolo, Valor, Unidad.
    """
    filas = [
        ("Tipo de acero",               "—",       steel.type_,                         "—"),
        ("Diámetro nominal",            "Ø",       f"{steel.diameter:.1f}",              "mm"),
        ("Número de hilos",             "—",       f"{steel.fios}",                      "—"),
        ("Área por cordón",             "Aps",     f"{steel.Aps_unit_mm2:.1f}",          "mm²"),
        ("Resist. a ruptura",           "fptk",    f"{steel.fptk:.1f}",                  "MPa"),
        ("Tensión de fluencia (1%)",    "fpyk",    f"{steel.fpyk:.1f}",                  "MPa"),
        ("Tensión de cálculo",          "fpd",     f"{steel.fpd:.1f}",                   "MPa"),
        ("Módulo de elasticidad",       "Eps",     f"{steel.Eps:.0f}",                   "MPa"),
        ("Fuerza máx. por cordón",      "Pj,lim",  f"{steel.Pj_lim_unit():.2f}",        "kN"),
    ]
    return pd.DataFrame(filas, columns=["Propiedad", "Símbolo", "Valor", "Unidad"])


# ══════════════════════════════════════════════════════════════════════════
# Límites de tensión
# ══════════════════════════════════════════════════════════════════════════

def tabla_limites_tension(limits) -> pd.DataFrame:
    """
    Tabla con los límites de tensión admisibles en el hormigón.

    Args:
        limits: Instancia de StressLimits.

    Returns:
        DataFrame con columnas: Situación, Fibra, Límite, Valor (MPa).
    """
    filas = [
        ("Ato de transferencia", "Superior (topo)",   "Compresión máx. ftc",  f"{limits.ftc:.2f}"),
        ("Ato de transferencia", "Superior (topo)",   "Tracción máx. ftt",    f"{limits.ftt:.2f}"),
        ("Ato de transferencia", "Inferior (fondo)",  "Compresión máx. ftc",  f"{limits.ftc:.2f}"),
        ("Ato de transferencia", "Inferior (fondo)",  "Tracción máx. ftt",    f"{limits.ftt:.2f}"),
        ("En servicio (ELS)",    "Superior (topo)",   "Compresión máx. fsc",  f"{limits.fsc:.2f}"),
        ("En servicio (ELS)",    "Superior (topo)",   "Tracción máx. fst",    f"{limits.fst:.2f}"),
        ("En servicio (ELS)",    "Inferior (fondo)",  "Compresión máx. fsc",  f"{limits.fsc:.2f}"),
        ("En servicio (ELS)",    "Inferior (fondo)",  "Tracción máx. fst",    f"{limits.fst:.2f}"),
    ]
    return pd.DataFrame(filas, columns=["Situación", "Fibra", "Límite", "Valor (MPa)"])


# ══════════════════════════════════════════════════════════════════════════
# Verificación de tensiones
# ══════════════════════════════════════════════════════════════════════════

def tabla_verificacion_tensiones(
    resultados: list,
    etiquetas: list,
) -> pd.DataFrame:
    """
    Tabla de verificación de tensiones para múltiples situaciones.

    Args:
        resultados: Lista de instancias de StressResult.
        etiquetas:  Etiquetas correspondientes a cada resultado.

    Returns:
        DataFrame con columnas: Situación, σ_top, σ_bot, Estado.
    """
    filas = []
    for etiqueta, res in zip(etiquetas, resultados):
        estado = "✅ OK" if res.ok else "❌ FALLO"
        det_top = "✅" if res.passes_top else "❌"
        det_bot = "✅" if res.passes_bottom else "❌"
        filas.append((
            etiqueta,
            f"{res.sigma_top:.2f} {det_top}",
            f"{res.sigma_bottom:.2f} {det_bot}",
            estado,
        ))
    return pd.DataFrame(filas, columns=["Situación", "σ_top (MPa)", "σ_bot (MPa)", "Estado"])


# ══════════════════════════════════════════════════════════════════════════
# Combinaciones de carga
# ══════════════════════════════════════════════════════════════════════════

def tabla_combinaciones_carga(
    Msw: float,
    Mgk: float,
    Mqk: float,
    Mse: Dict[str, float],
    Md: float,
) -> pd.DataFrame:
    """
    Tabla con todos los momentos de cálculo: peso propio, permanente,
    sobrecarga, ELS y ELU.

    Args:
        Msw:  Momento del peso propio (kN·m).
        Mgk:  Momento de la carga permanente adicional (kN·m).
        Mqk:  Momento de la sobrecarga (kN·m).
        Mse:  Diccionario con las combinaciones ELS.
        Md:   Momento de cálculo ELU (kN·m).

    Returns:
        DataFrame.
    """
    filas: list = [
        ("Peso propio",           "Msw",   f"{Msw:.2f}",  "kN·m"),
        ("Carga permanente",      "Mgk",   f"{Mgk:.2f}",  "kN·m"),
        ("Sobrecarga",            "Mqk",   f"{Mqk:.2f}",  "kN·m"),
    ]
    for clave, valor in Mse.items():
        filas.append((f"ELS — {clave}", clave, f"{valor:.2f}", "kN·m"))
    filas.append(("Cálculo ELU", "Msd", f"{Md:.2f}", "kN·m"))
    return pd.DataFrame(filas, columns=["Descripción", "Símbolo", "Valor", "Unidad"])


# ══════════════════════════════════════════════════════════════════════════
# Pérdidas de pretensado
# ══════════════════════════════════════════════════════════════════════════

def tabla_perdidas_pretensado(
    Pj: float,
    delta_P_fricc: Optional[float],
    delta_P_anc: Optional[float],
    delta_P_elas: Optional[float],
    delta_P_prog: Optional[float],
) -> pd.DataFrame:
    """
    Tabla resumen de las pérdidas de pretensado.

    Returns:
        DataFrame con: Tipo de pérdida, ΔP (kN), % respecto a Pj.
    """
    def _fila(nombre: str, delta_P: Optional[float]) -> tuple:
        if delta_P is None:
            return (nombre, "—", "—")
        pct = 100.0 * delta_P / Pj if Pj > 0 else 0.0
        return (nombre, f"{delta_P:.2f}", f"{pct:.1f}%")

    Pt = Pj
    filas = [("Pj — Fuerza inicial (gato)", f"{Pj:.2f}", "100,0%")]

    if delta_P_fricc is not None:
        Pt -= delta_P_fricc
    if delta_P_anc is not None:
        Pt -= delta_P_anc
    if delta_P_elas is not None:
        Pt -= delta_P_elas

    filas += [
        _fila("Pérdida por fricción",               delta_P_fricc),
        _fila("Pérdida por asentamiento de anclaje", delta_P_anc),
        _fila("Pérdida por acortamiento elástico",   delta_P_elas),
        (f"Pt — Tras pérdidas inmediatas", f"{Pt:.2f}", f"{100*Pt/Pj:.1f}%" if Pj > 0 else "—"),
        _fila("Pérdida progresiva (fluencia+retracción+relajación)", delta_P_prog),
    ]

    Ps = Pt - (delta_P_prog or 0.0)
    filas.append((f"Ps — En servicio", f"{Ps:.2f}", f"{100*Ps/Pj:.1f}%" if Pj > 0 else "—"))

    return pd.DataFrame(filas, columns=["Descripción", "ΔP / P (kN)", "% de Pj"])


# ══════════════════════════════════════════════════════════════════════════
# ELU a flexión
# ══════════════════════════════════════════════════════════════════════════

def tabla_verificacion_elu(
    secciones: list,
    MRd_values: list,
    Msd_values: list,
) -> pd.DataFrame:
    """
    Tabla de verificación ELU a flexión en secciones críticas.

    Args:
        secciones:   Lista de etiquetas de sección.
        MRd_values:  Momento resistente (kN·m) por sección.
        Msd_values:  Momento solicitante de cálculo (kN·m) por sección.

    Returns:
        DataFrame con: Sección, MRd, Msd, MRd/Msd, Estado.
    """
    filas = []
    for sec, MRd, Msd in zip(secciones, MRd_values, Msd_values):
        razon = MRd / Msd if Msd > 0 else float("inf")
        ok = razon >= 1.0
        filas.append((
            sec,
            f"{MRd:.2f}",
            f"{Msd:.2f}",
            f"{razon:.3f}",
            "✅ OK" if ok else "❌ FALLO",
        ))
    return pd.DataFrame(
        filas,
        columns=["Sección", "MRd (kN·m)", "Msd (kN·m)", "MRd/Msd", "Estado"],
    )
