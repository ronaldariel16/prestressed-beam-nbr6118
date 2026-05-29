"""
test_app_smoke.py
Pruebas de importación y coherencia básica de la aplicación Streamlit.

Verifican que todos los módulos de app/ importan sin errores y que
los componentes del backend que utilizan siguen siendo compatibles.
"""
import sys
from pathlib import Path

import pytest

# Añadir la raíz del proyecto al path
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))


# ══════════════════════════════════════════════════════════════════════════
# Importaciones de componentes
# ══════════════════════════════════════════════════════════════════════════

def test_importar_state():
    """EstadoProyecto y funciones de estado importan sin errores."""
    from app.components.state import (
        EstadoProyecto,
        ETAPAS,
        NOMBRES_ETAPAS,
        ICONOS_ETAPAS,
        obtener_estado,
        guardar_estado,
        reiniciar_estado,
        mostrar_barra_lateral,
    )
    assert len(ETAPAS) == 8
    assert len(NOMBRES_ETAPAS) == 8
    assert len(ICONOS_ETAPAS) == 8


def test_importar_inputs():
    """Módulo inputs importa sin errores."""
    from app.components.inputs import (
        entrada_numero,
        entrada_con_slider,
        selector_hormigon,
        selector_factor_agregado,
        selector_acero_pretensado,
        selector_tipo_apoyo,
        selector_nivel_pretensado,
        selector_tipo_pretensado,
        selector_uso_edificacion,
        TIPOS_APOYO,
        USOS_EDIFICACION,
    )
    assert "simplemente_apoyada" in TIPOS_APOYO
    assert "residencial" in USOS_EDIFICACION


def test_importar_plots():
    """Módulo plots importa sin errores."""
    from app.components.plots import (
        dibujar_seccion_transversal,
        graficar_diagrama_momentos,
        graficar_tensiones_fibras,
        graficar_perdidas_pretensado,
        COLORES,
    )
    assert "primario" in COLORES


def test_importar_tables():
    """Módulo tables importa sin errores."""
    from app.components.tables import (
        tabla_propiedades_seccion,
        tabla_propiedades_hormigon,
        tabla_propiedades_acero,
        tabla_limites_tension,
        tabla_verificacion_tensiones,
        tabla_combinaciones_carga,
        tabla_perdidas_pretensado,
        tabla_verificacion_elu,
    )


# ══════════════════════════════════════════════════════════════════════════
# EstadoProyecto — serialización
# ══════════════════════════════════════════════════════════════════════════

def test_estado_defecto():
    """EstadoProyecto crea un estado con valores por defecto correctos."""
    from app.components.state import EstadoProyecto
    estado = EstadoProyecto()
    assert estado.b == pytest.approx(0.30)
    assert estado.h == pytest.approx(0.80)
    assert estado.fck == pytest.approx(30.0)
    assert estado.steel_diameter == pytest.approx(15.2)
    assert estado.etapas_completadas == []
    assert estado.progreso() == pytest.approx(0.0)


def test_estado_serializar_deserializar():
    """Round-trip JSON: to_dict → from_dict preserva todos los campos."""
    from app.components.state import EstadoProyecto
    estado = EstadoProyecto(b=0.40, h=1.00, fck=35.0)
    datos = estado.to_dict()
    estado2 = EstadoProyecto.from_dict(datos)
    assert estado2.b == pytest.approx(0.40)
    assert estado2.h == pytest.approx(1.00)
    assert estado2.fck == pytest.approx(35.0)


def test_estado_save_load_json(tmp_path):
    """Guarda y carga un archivo JSON correctamente."""
    from app.components.state import EstadoProyecto
    estado = EstadoProyecto(b=0.35, h=0.90, fck=25.0)
    ruta = str(tmp_path / "proyecto_test.json")
    estado.save_json(ruta)
    estado2 = EstadoProyecto.load_json(ruta)
    assert estado2.b == pytest.approx(0.35)
    assert estado2.h == pytest.approx(0.90)


def test_estado_progreso():
    """El progreso aumenta al marcar etapas como completadas."""
    from app.components.state import EstadoProyecto, ETAPAS
    estado = EstadoProyecto()
    assert estado.progreso() == pytest.approx(0.0)
    estado.marcar_completada(ETAPAS[0])
    assert estado.progreso() == pytest.approx(1 / len(ETAPAS))
    estado.marcar_completada(ETAPAS[0])  # duplicado — no debe contar doble
    assert estado.progreso() == pytest.approx(1 / len(ETAPAS))


# ══════════════════════════════════════════════════════════════════════════
# EstadoProyecto — helpers de reconstrucción del backend
# ══════════════════════════════════════════════════════════════════════════

def test_get_section():
    """get_section() devuelve RectangularSection con las dimensiones correctas."""
    from app.components.state import EstadoProyecto
    estado = EstadoProyecto(b=0.30, h=0.80)
    sec = estado.get_section()
    assert sec.b == pytest.approx(0.30)
    assert sec.h == pytest.approx(0.80)
    assert sec.A == pytest.approx(0.24)


def test_get_concrete():
    """get_concrete() devuelve Concrete con fck correcto."""
    from app.components.state import EstadoProyecto
    estado = EstadoProyecto(fck=30.0, fckj=25.0)
    conc = estado.get_concrete()
    assert conc.fck == pytest.approx(30.0)
    assert conc.fckj == pytest.approx(25.0)


def test_get_steel():
    """get_steel() devuelve PrestressSteel con el diámetro correcto."""
    from app.components.state import EstadoProyecto
    estado = EstadoProyecto(steel_diameter=15.2)
    steel = estado.get_steel()
    assert steel.diameter == pytest.approx(15.2)
    assert steel.Aps_unit_mm2 == pytest.approx(140.0)


def test_get_support_simplemente_apoyada():
    """get_support() devuelve SimplySupported para la opción por defecto."""
    from app.components.state import EstadoProyecto
    from src.supports import SimplySupported
    estado = EstadoProyecto(support_type="simplemente_apoyada", L=10.0)
    apoyo = estado.get_support()
    assert isinstance(apoyo, SimplySupported)
    assert apoyo.L == pytest.approx(10.0)


def test_get_support_desconocido():
    """get_support() lanza ValueError para tipos desconocidos."""
    from app.components.state import EstadoProyecto
    estado = EstadoProyecto(support_type="tipo_inexistente")
    with pytest.raises(ValueError):
        estado.get_support()


# ══════════════════════════════════════════════════════════════════════════
# Tables — generación de DataFrames
# ══════════════════════════════════════════════════════════════════════════

def test_tabla_propiedades_seccion():
    """tabla_propiedades_seccion() produce un DataFrame con las 8 propiedades."""
    from app.components.tables import tabla_propiedades_seccion
    from src.geometry import RectangularSection
    sec = RectangularSection(b=0.30, h=0.80)
    df = tabla_propiedades_seccion(sec)
    assert len(df) == 8
    assert "Propiedad" in df.columns
    assert "Valor" in df.columns


def test_tabla_propiedades_hormigon():
    """tabla_propiedades_hormigon() produce un DataFrame con 8 filas."""
    from app.components.tables import tabla_propiedades_hormigon
    from src.materials import Concrete
    conc = Concrete(fck=30.0)
    df = tabla_propiedades_hormigon(conc)
    assert len(df) == 8


def test_tabla_propiedades_acero():
    """tabla_propiedades_acero() produce un DataFrame con 9 filas."""
    from app.components.tables import tabla_propiedades_acero
    from src.materials import PrestressSteel
    steel = PrestressSteel(diameter=15.2)
    df = tabla_propiedades_acero(steel)
    assert len(df) == 9


# ══════════════════════════════════════════════════════════════════════════
# Plots — generación de figuras (sin interfaz gráfica)
# ══════════════════════════════════════════════════════════════════════════

def test_dibujar_seccion_transversal():
    """dibujar_seccion_transversal() retorna una figura matplotlib válida."""
    import matplotlib.pyplot as plt
    from app.components.plots import dibujar_seccion_transversal
    fig = dibujar_seccion_transversal(b=0.30, h=0.80)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


def test_graficar_diagrama_momentos():
    """graficar_diagrama_momentos() retorna una figura Plotly válida."""
    import numpy as np
    import plotly.graph_objects as go
    from app.components.plots import graficar_diagrama_momentos
    x = np.linspace(0, 10, 21)
    M = x * (10 - x) / 2 * 20
    fig = graficar_diagrama_momentos(x, {"Msw": M})
    assert isinstance(fig, go.Figure)
