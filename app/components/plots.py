"""
plots.py
Funciones de visualización para la aplicación.

Convención:
  - Matplotlib: vistas estáticas de la sección transversal.
  - Plotly:     gráficos interactivos (diagramas de momentos, Magnel, etc.).
"""
from __future__ import annotations

from typing import List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")  # backend no interactivo para Streamlit
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go

# ── Paleta de colores del proyecto ────────────────────────────────────────
COLORES = {
    "primario":       "#1565C0",   # azul oscuro
    "secundario":     "#FF6F00",   # naranja
    "acento":         "#2E7D32",   # verde oscuro
    "peligro":        "#C62828",   # rojo oscuro
    "advertencia":    "#F9A825",   # amarillo
    "relleno_seccion": "#DDEEFF",  # azul muy claro
    "borde_seccion":  "#1565C0",   # azul oscuro
    "centroide":      "#C62828",   # rojo
    "cordon":         "#37474F",   # gris oscuro
    "admisible":      "rgba(46,125,50,0.15)",  # verde transparente
}


# ══════════════════════════════════════════════════════════════════════════
# Sección transversal (matplotlib)
# ══════════════════════════════════════════════════════════════════════════

def dibujar_seccion_transversal(
    b: float,
    h: float,
    cordones: Optional[List[Tuple[float, float]]] = None,
    cobertura: float = 0.04,
) -> plt.Figure:
    """
    Dibuja la sección transversal rectangular con cotas y línea del centroide.

    Args:
        b:        Ancho de la sección (m).
        h:        Altura de la sección (m).
        cordones: Lista de posiciones (y_desde_abajo, x_desde_izq) en metros.
                  Si se pasa, dibuja los cordones.
        cobertura: Cobertura del recubrimiento (m), para referencia visual.

    Returns:
        Figura de matplotlib lista para st.pyplot().
    """
    # Márgenes proporcionales para las cotas
    mx = max(b * 0.45, 0.05)
    my = max(h * 0.18, 0.05)

    fig, ax = plt.subplots(figsize=(4.5, 6.0))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # ── Relleno de la sección ──────────────────────────────────────
    rect = patches.Rectangle(
        (0.0, 0.0), b, h,
        facecolor=COLORES["relleno_seccion"],
        edgecolor=COLORES["borde_seccion"],
        linewidth=2.0,
        zorder=2,
    )
    ax.add_patch(rect)

    # ── Línea del centroide ────────────────────────────────────────
    yt = h / 2.0
    ax.plot([0, b], [yt, yt],
            color=COLORES["centroide"], linewidth=1.2,
            linestyle="--", alpha=0.9, zorder=3)
    ax.plot(b / 2, yt, "o",
            color=COLORES["centroide"], markersize=7, zorder=4)
    ax.text(b + mx * 0.05, yt, "  CG",
            va="center", ha="left", fontsize=8,
            color=COLORES["centroide"])

    # ── Cordones (opcional) ────────────────────────────────────────
    if cordones:
        for (y_cord, x_cord) in cordones:
            ax.plot(x_cord, y_cord, "o",
                    color=COLORES["cordon"],
                    markersize=6, zorder=5)

    # ── Cota horizontal b (arriba) ─────────────────────────────────
    y_cota_b = h + my * 0.55
    _flecha_cota_h(ax, 0, b, y_cota_b,
                   f"b = {b*100:.1f} cm",
                   desplazamiento_texto=my * 0.20)
    ax.plot([0, 0], [h, y_cota_b], "--", color="#AAAAAA", lw=0.8)
    ax.plot([b, b], [h, y_cota_b], "--", color="#AAAAAA", lw=0.8)

    # ── Cota vertical h (derecha) ──────────────────────────────────
    x_cota_h = b + mx * 0.55
    _flecha_cota_v(ax, 0, h, x_cota_h,
                   f"h = {h*100:.1f} cm",
                   desplazamiento_texto=mx * 0.18)
    ax.plot([b, x_cota_h], [0, 0], "--", color="#AAAAAA", lw=0.8)
    ax.plot([b, x_cota_h], [h, h], "--", color="#AAAAAA", lw=0.8)

    # ── Texto de yt y yb ──────────────────────────────────────────
    ax.text(-mx * 0.05, yt / 2, f"yb = {yt*100:.1f} cm",
            ha="right", va="center", fontsize=7.5, color="#444444")
    ax.text(-mx * 0.05, yt + yt / 2, f"yt = {yt*100:.1f} cm",
            ha="right", va="center", fontsize=7.5, color="#444444")

    # ── Configuración del eje ──────────────────────────────────────
    ax.set_xlim(-mx * 0.45, b + mx * 1.9)
    ax.set_ylim(-my * 0.6, h + my * 1.3)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title("Sección transversal", fontsize=11, pad=6)

    plt.tight_layout()
    return fig


def _flecha_cota_h(
    ax: plt.Axes,
    x_ini: float,
    x_fin: float,
    y: float,
    texto: str,
    desplazamiento_texto: float = 0.02,
) -> None:
    """Dibuja una flecha de cota horizontal con texto centrado."""
    ax.annotate(
        "",
        xy=(x_fin, y),
        xytext=(x_ini, y),
        arrowprops=dict(arrowstyle="<->", color="#333333", lw=1.3),
    )
    ax.text(
        (x_ini + x_fin) / 2, y + desplazamiento_texto,
        texto,
        ha="center", va="bottom",
        fontsize=9.5, fontweight="bold", color="#222222",
    )


def _flecha_cota_v(
    ax: plt.Axes,
    y_ini: float,
    y_fin: float,
    x: float,
    texto: str,
    desplazamiento_texto: float = 0.02,
) -> None:
    """Dibuja una flecha de cota vertical con texto centrado."""
    ax.annotate(
        "",
        xy=(x, y_fin),
        xytext=(x, y_ini),
        arrowprops=dict(arrowstyle="<->", color="#333333", lw=1.3),
    )
    ax.text(
        x + desplazamiento_texto, (y_ini + y_fin) / 2,
        texto,
        ha="left", va="center",
        fontsize=9.5, fontweight="bold", color="#222222",
        rotation=0,
    )


# ══════════════════════════════════════════════════════════════════════════
# Utilidad de color
# ══════════════════════════════════════════════════════════════════════════

def _hex_a_rgba(hex_color: str, alpha: float = 1.0) -> str:
    """
    Convierte un color hexadecimal (#RRGGBB) a formato rgba() de CSS/Plotly.
    Plotly no acepta hex con canal alfa (#RRGGBBAA); se usa rgba() en su lugar.
    """
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ══════════════════════════════════════════════════════════════════════════
# Diagramas de momentos (plotly interactivo)
# ══════════════════════════════════════════════════════════════════════════

def graficar_diagrama_momentos(
    x: np.ndarray,
    momentos: dict,
    titulo: str = "Diagrama de momentos flectores",
) -> go.Figure:
    """
    Grafica uno o varios diagramas de momentos a lo largo de la viga.

    Args:
        x:        Array de posiciones a lo largo de la viga (m).
        momentos: Diccionario {etiqueta: array_M}. Cada array debe tener
                  la misma longitud que x.
        titulo:   Título del gráfico.

    Returns:
        Figura Plotly lista para st.plotly_chart().
    """
    colores_curvas = [
        COLORES["primario"], COLORES["secundario"],
        COLORES["acento"], COLORES["peligro"], COLORES["advertencia"],
        "#7B1FA2",
    ]

    fig = go.Figure()

    for i, (etiqueta, M) in enumerate(momentos.items()):
        color = colores_curvas[i % len(colores_curvas)]
        fig.add_trace(go.Scatter(
            x=x,
            y=M,
            mode="lines",
            name=etiqueta,
            line=dict(color=color, width=2.5),
            hovertemplate=(
                f"<b>{etiqueta}</b><br>"
                "x = %{x:.2f} m<br>"
                "M = %{y:.2f} kN·m<extra></extra>"
            ),
        ))

        # Relleno bajo la curva con transparencia (rgba siempre)
        fig.add_trace(go.Scatter(
            x=np.concatenate([x, x[::-1]]),
            y=np.concatenate([M, np.zeros_like(M)]),
            fill="toself",
            fillcolor=_hex_a_rgba(color, alpha=0.10),
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Línea de referencia en M=0
    fig.add_hline(y=0, line=dict(color="#888888", width=1.0, dash="dash"))

    fig.update_layout(
        title=dict(text=titulo, font=dict(size=14)),
        xaxis=dict(
            title="Posición a lo largo de la viga x (m)",
            gridcolor="#EEEEEE",
            showgrid=True,
        ),
        yaxis=dict(
            title="Momento flector M (kN·m)",
            gridcolor="#EEEEEE",
            showgrid=True,
        ),
        legend=dict(orientation="h", y=-0.18),
        plot_bgcolor="white",
        paper_bgcolor="white",
        hovermode="x unified",
        margin=dict(t=50, b=60, l=60, r=20),
    )

    return fig


def graficar_tensiones_fibras(
    situaciones: List[dict],
    etiquetas: List[str],
) -> go.Figure:
    """
    Gráfico de barras apiladas mostrando tensiones en fibra superior e inferior.

    Args:
        situaciones: Lista de dicts con claves 'sigma_top' y 'sigma_bottom'.
        etiquetas:   Etiquetas para cada situación (eje X).

    Returns:
        Figura Plotly.
    """
    sig_top = [s["sigma_top"] for s in situaciones]
    sig_bot = [s["sigma_bottom"] for s in situaciones]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Fibra superior (σ topo)",
        x=etiquetas,
        y=sig_top,
        marker_color=COLORES["primario"],
        hovertemplate="σ<sub>sup</sub> = %{y:.2f} MPa<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        name="Fibra inferior (σ fondo)",
        x=etiquetas,
        y=sig_bot,
        marker_color=COLORES["secundario"],
        hovertemplate="σ<sub>inf</sub> = %{y:.2f} MPa<extra></extra>",
    ))

    fig.add_hline(y=0, line=dict(color="#333333", width=1.0))

    fig.update_layout(
        title="Tensiones en las fibras extremas (MPa)",
        yaxis=dict(title="Tensión (MPa) — tracción (+), compresión (−)"),
        xaxis=dict(title="Situación de carga"),
        barmode="group",
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.20),
        margin=dict(t=50, b=80, l=60, r=20),
    )

    return fig


def graficar_perdidas_pretensado(
    x: np.ndarray,
    Pj: np.ndarray,
    Pt: Optional[np.ndarray] = None,
    Ps: Optional[np.ndarray] = None,
) -> go.Figure:
    """
    Grafica las fuerzas de pretensado Pj(x), Pt(x) y Ps(x) a lo largo de la viga.

    Args:
        x:   Posiciones (m).
        Pj:  Fuerza inicial en el gato (kN).
        Pt:  Fuerza tras pérdidas inmediatas (kN), opcional.
        Ps:  Fuerza en servicio (kN), opcional.

    Returns:
        Figura Plotly.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=Pj, mode="lines",
        name="Pj — Fuerza inicial",
        line=dict(color=COLORES["primario"], width=2.5),
        hovertemplate="Pj = %{y:.1f} kN  @ x=%{x:.2f} m<extra></extra>",
    ))

    if Pt is not None:
        fig.add_trace(go.Scatter(
            x=x, y=Pt, mode="lines",
            name="Pt — Tras pérdidas inmediatas",
            line=dict(color=COLORES["advertencia"], width=2.5, dash="dash"),
            hovertemplate="Pt = %{y:.1f} kN  @ x=%{x:.2f} m<extra></extra>",
        ))

    if Ps is not None:
        fig.add_trace(go.Scatter(
            x=x, y=Ps, mode="lines",
            name="Ps — En servicio",
            line=dict(color=COLORES["peligro"], width=2.5, dash="dot"),
            hovertemplate="Ps = %{y:.1f} kN  @ x=%{x:.2f} m<extra></extra>",
        ))

    fig.update_layout(
        title="Evolución de la fuerza de pretensado a lo largo de la viga",
        xaxis=dict(title="Posición x (m)", gridcolor="#EEEEEE"),
        yaxis=dict(title="Fuerza de pretensado (kN)", gridcolor="#EEEEEE"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", y=-0.20),
        hovermode="x unified",
        margin=dict(t=50, b=80, l=60, r=20),
    )

    return fig
