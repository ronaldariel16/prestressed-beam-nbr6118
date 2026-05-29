"""
state.py
Gestión del estado del proyecto mediante st.session_state.

El EstadoProyecto almacena sólo valores primitivos serializables.
Los objetos del backend (RectangularSection, Concrete, etc.) se
reconstruyen bajo demanda con los métodos get_*().
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict, fields
from typing import Any, Dict, List, Optional

import streamlit as st

# Clave principal en session_state
_CLAVE_ESTADO = "proyecto_pretensado"

# Orden y nombres de las etapas del flujo de trabajo
ETAPAS: List[str] = [
    "geometria_materiales",
    "cargas_apoyos",
    "predimensionamiento",
    "magnel",
    "armadura_perfil",
    "perdidas",
    "verificaciones",
    "informe",
]

NOMBRES_ETAPAS: Dict[str, str] = {
    "geometria_materiales":  "1. Geometría y Materiales",
    "cargas_apoyos":         "2. Cargas y Apoyos",
    "predimensionamiento":   "3. Predimensionamiento",
    "magnel":                "4. Diagrama de Magnel",
    "armadura_perfil":       "5. Armadura y Perfil",
    "perdidas":              "6. Pérdidas de Pretensado",
    "verificaciones":        "7. Verificaciones ELU/ELS",
    "informe":               "8. Informe Final",
}

ICONOS_ETAPAS: Dict[str, str] = {
    "geometria_materiales":  "📐",
    "cargas_apoyos":         "⚖️",
    "predimensionamiento":   "📏",
    "magnel":                "📊",
    "armadura_perfil":       "🔗",
    "perdidas":              "📉",
    "verificaciones":        "✅",
    "informe":               "📑",
}


@dataclass
class EstadoProyecto:
    """Estado completo y serializable del proyecto de dimensionamiento."""

    # ── Geometría ──────────────────────────────────────────────────────
    b: float = 0.30    # ancho de la sección (m)
    h: float = 0.80    # altura de la sección (m)

    # ── Hormigón ───────────────────────────────────────────────────────
    fck: float = 30.0    # resistencia característica a 28 días (MPa)
    fckj: float = 30.0   # resistencia al momento del tesado (MPa)
    # factor de tipo de árido: granito=1.0, basalto=0.9, caliza=0.7, arenisca=0.5
    alpha_E: float = 1.0

    # ── Acero de pretensado ────────────────────────────────────────────
    steel_type: str = "CP-190 RB"
    steel_diameter: float = 15.2    # diámetro nominal del cordón (mm)

    # ── Condición de apoyo ─────────────────────────────────────────────
    support_type: str = "simplemente_apoyada"
    L: float = 10.0     # luz principal del vano (m)
    L2: float = 10.0    # luz del segundo vano (m) — solo para viga continua

    # ── Cargas características ─────────────────────────────────────────
    gk: float = 10.0    # carga permanente adicional, excluido peso propio (kN/m)
    qk: float = 10.0    # sobrecarga variable (kN/m)
    usage: str = "residencial"   # clave interna del backend (ver PSI_TABLE)

    # ── Nivel de pretensado y tipo ─────────────────────────────────────
    prestress_level: str = "completa"      # completa | limitada | parcial
    prestress_type: str = "pos_traccion"   # pre_traccion | pos_traccion
    CAA: str = "C"                         # clase de agresividad ambiental

    # ── Coeficientes estimados de pérdidas (Cap. 5 del manual) ────────
    alpha: float = 0.90    # Pt/Pj  (pérdidas inmediatas estimadas)
    beta: float = 0.75     # Ps/Pj  (todas las pérdidas estimadas)

    # ── Resultados del Diagrama de Magnel ─────────────────────────────
    Pj: Optional[float] = None    # fuerza de pretensado en el gato (kN)
    e: Optional[float] = None     # excentricidad de diseño (m)

    # ── Armadura activa ────────────────────────────────────────────────
    n_strands: Optional[int] = None     # número de cordones
    e_real: Optional[float] = None      # excentricidad real recalculada (m)
    profile_type: str = "parabolico"    # recto | parabolico | multiparabolico

    # ── Parámetros de pérdidas ─────────────────────────────────────────
    mu: float = 0.20        # coeficiente de fricción μ (vainas metálicas)
    k_par: float = 0.002    # coeficiente de pérdidas parásitas k (rad/m)
    delta_A: float = 0.006  # asentamiento de anclaje ΔA (m)
    phi_creep: float = 2.0  # coeficiente de fluencia φ(t∞, t0)
    t0: float = 7.0         # edad del hormigón al tesar (días)

    # ── Progreso del proyecto ──────────────────────────────────────────
    etapas_completadas: List[str] = field(default_factory=list)

    # ══════════════════════════════════════════════════════════════════
    # Serialización
    # ══════════════════════════════════════════════════════════════════

    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado a diccionario serializable en JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, datos: Dict[str, Any]) -> "EstadoProyecto":
        """Reconstruye el estado desde un diccionario (ignora claves desconocidas)."""
        nombres_validos = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in datos.items() if k in nombres_validos})

    def save_json(self, ruta: str) -> None:
        """Guarda el estado en un archivo JSON con formato legible."""
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, ruta: str) -> "EstadoProyecto":
        """Carga el estado desde un archivo JSON."""
        with open(ruta, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    # ══════════════════════════════════════════════════════════════════
    # Gestión de progreso
    # ══════════════════════════════════════════════════════════════════

    def etapa_completada(self, etapa: str) -> bool:
        return etapa in self.etapas_completadas

    def marcar_completada(self, etapa: str) -> None:
        if etapa not in self.etapas_completadas:
            self.etapas_completadas.append(etapa)

    def progreso(self) -> float:
        """Fracción de etapas completadas [0.0 → 1.0]."""
        return len(self.etapas_completadas) / len(ETAPAS) if ETAPAS else 0.0

    # ══════════════════════════════════════════════════════════════════
    # Helpers — reconstrucción de objetos del backend bajo demanda
    # ══════════════════════════════════════════════════════════════════

    def get_section(self):
        """Reconstruye RectangularSection con los valores actuales."""
        from src.geometry import RectangularSection
        return RectangularSection(b=self.b, h=self.h)

    def get_concrete(self):
        """Reconstruye Concrete con los valores actuales."""
        from src.materials import Concrete
        return Concrete(fck=self.fck, fckj=self.fckj)

    def get_steel(self):
        """Reconstruye PrestressSteel con los valores actuales."""
        from src.materials import PrestressSteel
        return PrestressSteel(type_=self.steel_type, diameter=self.steel_diameter)

    def get_support(self):
        """Reconstruye el objeto de apoyo según el tipo seleccionado."""
        from src.supports import (
            SimplySupported, FixedFixed, FixedPinned,
            Cantilever, TwoSpanContinuous,
        )
        constructores = {
            "simplemente_apoyada": lambda: SimplySupported(self.L),
            "biempotrada":         lambda: FixedFixed(self.L),
            "empotrada_apoyada":   lambda: FixedPinned(self.L),
            "voladizo":            lambda: Cantilever(self.L),
            "continua_dos_vanos":  lambda: TwoSpanContinuous(self.L, self.L2),
        }
        constructor = constructores.get(self.support_type)
        if constructor is None:
            raise ValueError(f"Tipo de apoyo no reconocido: '{self.support_type}'")
        return constructor()

    def get_loads(self):
        """Reconstruye Loads con los valores actuales."""
        from src.loads import Loads
        return Loads(gk=self.gk, qk=self.qk, usage=self.usage)

    def peso_propio(self) -> float:
        """Peso propio de la viga (kN/m)."""
        section = self.get_section()
        concrete = self.get_concrete()
        return section.A * concrete.gamma_concrete

    def momento_max_total(self) -> Optional[float]:
        """
        Momento máximo total (kN·m) en la sección crítica.
        Devuelve None si el tipo de apoyo aún no está implementado.
        """
        try:
            section = self.get_section()
            concrete = self.get_concrete()
            loads = self.get_loads()
            support = self.get_support()
            pp = section.A * concrete.gamma_concrete
            q_total = pp + loads.gk + loads.qk
            x_critico, _ = support.critical_sections()[0]
            return abs(support.M_uniform(x_critico, q_total))
        except NotImplementedError:
            return None


# ══════════════════════════════════════════════════════════════════════
# Funciones de acceso al estado global en session_state
# ══════════════════════════════════════════════════════════════════════

def obtener_estado() -> EstadoProyecto:
    """Recupera el estado desde session_state; lo inicializa si no existe."""
    if _CLAVE_ESTADO not in st.session_state:
        st.session_state[_CLAVE_ESTADO] = EstadoProyecto()
    return st.session_state[_CLAVE_ESTADO]


def guardar_estado(estado: EstadoProyecto) -> None:
    """Persiste el estado actualizado en session_state."""
    st.session_state[_CLAVE_ESTADO] = estado


def reiniciar_estado() -> None:
    """Reinicia el proyecto a los valores por defecto."""
    st.session_state[_CLAVE_ESTADO] = EstadoProyecto()


def mostrar_barra_lateral(etapa_actual: str = "") -> None:
    """
    Renderiza en st.sidebar el resumen del proyecto y el estado de progreso.
    Llámalo desde cualquier página para tener un sidebar consistente.
    """
    estado = obtener_estado()

    with st.sidebar:
        st.markdown("## 🏗️ Proyecto actual")

        # Resumen de parámetros clave
        if estado.etapa_completada("geometria_materiales"):
            st.markdown(
                f"**Sección:** {estado.b*100:.0f} × {estado.h*100:.0f} cm  \n"
                f"**Hormigón:** C{int(estado.fck)}  \n"
                f"**Acero:** Ø {estado.steel_diameter} mm"
            )
        else:
            st.caption("*Geometría y materiales aún no definidos.*")

        if estado.etapa_completada("cargas_apoyos"):
            tipo_apoyo_es = {
                "simplemente_apoyada": "Simplemente apoyada",
                "biempotrada": "Biempotrada",
                "empotrada_apoyada": "Empotrada-apoyada",
                "voladizo": "Voladizo",
                "continua_dos_vanos": "Continua 2 vanos",
            }.get(estado.support_type, estado.support_type)
            st.markdown(
                f"**Apoyo:** {tipo_apoyo_es}  \n"
                f"**Luz:** {estado.L:.1f} m  \n"
                f"**gk:** {estado.gk:.1f} kN/m  |  **qk:** {estado.qk:.1f} kN/m"
            )

        if estado.Pj is not None:
            st.markdown(
                f"**Pj:** {estado.Pj:.1f} kN  \n"
                f"**e:** {estado.e:.3f} m"
            )

        st.divider()

        # Barra de progreso
        pct = estado.progreso()
        st.markdown(f"**Progreso:** {pct*100:.0f}%")
        st.progress(pct)

        # Estado de cada etapa
        st.markdown("**Etapas:**")
        for etapa in ETAPAS:
            completada = estado.etapa_completada(etapa)
            es_actual = etapa == etapa_actual
            icono = ICONOS_ETAPAS.get(etapa, "")
            nombre = NOMBRES_ETAPAS.get(etapa, etapa)
            if completada:
                st.markdown(f"✅ ~~{icono} {nombre}~~")
            elif es_actual:
                st.markdown(f"▶️ **{icono} {nombre}**")
            else:
                st.markdown(f"⬜ {icono} {nombre}")

        st.divider()

        # Botones de acción del proyecto
        col_n, col_r = st.columns(2)
        with col_n:
            if st.button("🆕 Nuevo", use_container_width=True,
                         help="Reinicia el proyecto y borra todos los datos."):
                reiniciar_estado()
                st.rerun()
        with col_r:
            if st.button("🔄 Reiniciar", use_container_width=True,
                         help="Vuelve a los valores por defecto."):
                reiniciar_estado()
                st.rerun()

        # Guardar proyecto
        st.download_button(
            label="💾 Descargar proyecto (.json)",
            data=json.dumps(estado.to_dict(), ensure_ascii=False, indent=2),
            file_name="proyecto_viga.json",
            mime="application/json",
            use_container_width=True,
            help="Descarga el estado actual del proyecto en formato JSON para reutilizarlo.",
        )

        # Cargar proyecto
        archivo = st.file_uploader(
            "📂 Cargar proyecto (.json)",
            type=["json"],
            help="Sube un archivo JSON previamente guardado para continuar el diseño.",
            label_visibility="visible",
        )
        if archivo is not None:
            try:
                datos = json.load(archivo)
                nuevo_estado = EstadoProyecto.from_dict(datos)
                guardar_estado(nuevo_estado)
                st.success("Proyecto cargado correctamente.")
                st.rerun()
            except Exception as exc:
                st.error(f"Error al cargar el proyecto: {exc}")
