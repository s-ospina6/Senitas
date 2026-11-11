
import sys
import subprocess
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QLinearGradient
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStackedWidget,
    QButtonGroup,
    QProgressBar,
    QSizePolicy,
    QMessageBox,
)

from modo_aprendizaje_widget import ModoAprendizajeWidget
from modo_practica_widget import ModoPracticaWidget
from reconocer_senas_widget import ReconocerSenasWidget
from widgetjuego1 import WidgetJuegoMemoria
from juego_camino_letras import JuegoCaminoLetras


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MORADO = "#6C4DC4"
MORADO_OSCURO = "#5B3A9E"
NARANJA = "#F7941D"
NARANJA_PILL = "#FF8A3D"
CREMA = "#FFF3DD"
NAVY = "#2B3A67"
CONTORNO = "#2D3256"


def oscuro(color, factor=135):
    return QColor(color).darker(factor).name()


def claro(color, factor=110):
    return QColor(color).lighter(factor).name()


# ==========================================================
# SECCIONES DE LA APLICACIÓN
# ==========================================================

PAGINAS_JUGAR = [
    {
        "attr": "widget_aprendizaje",
        "fabrica": ModoAprendizajeWidget,
        "nombre": "Aprender",
        "emoji": "📚",
        "subtitulo": "¡Mira cómo se hace cada seña y practícala!",
        "color": "#F0527A",
        "texto_activo": "#FFFFFF",
    },
    {
        "attr": "widget_practica",
        "fabrica": ModoPracticaWidget,
        "nombre": "Practicar",
        "emoji": "🎯",
        "subtitulo": "Haz la seña frente a la cámara y gana estrellas.",
        "color": "#2D9CDB",
        "texto_activo": "#FFFFFF",
    },
    {
        "attr": "widget_reconocer",
        "fabrica": ReconocerSenasWidget,
        "nombre": "Reconocer señas",
        "emoji": "👀",
        "subtitulo": "¡El robot adivina qué seña estás haciendo!",
        "color": "#FFC93C",
        "texto_activo": NAVY,
    },
    {
        "attr": "widget_juego",
        "fabrica": WidgetJuegoMemoria,
        "nombre": "Juego de memoria",
        "emoji": "🎮",
        "subtitulo": "Encuentra las parejas y diviértete.",
        "color": "#4CAF50",
        "texto_activo": "#FFFFFF",
    },
    {
        "attr": "widget_camino",
        "fabrica": JuegoCaminoLetras,
        "nombre": "Camino de letras",
        "emoji": "🧩",
        "subtitulo": "¡Sigue las señas correctas y llega a la meta!",
        "color": "#F7941D",
        "texto_activo": "#FFFFFF",
    },
]


# ==========================================================
# PÁGINA DE ADULTOS
# ==========================================================

PAGINA_ADULTOS = {
    "nombre": "Configuraciones",
    "emoji": "⚙️",
    "subtitulo": "Herramientas para enseñarle señas nuevas al robot.",
    "color": "#8E6FD8",
    "texto_activo": "#FFFFFF",
}


HERRAMIENTAS_ADULTOS = [
    {
        "nombre": "Capturar datos",
        "archivo": "capturar_datos.py",
        "descripcion": "¡Vamos a guardar nuevas señas para que el robot aprenda más!",
        "emoji": "📸",
        "color": "#FF8FAB",
    },
    {
        "nombre": "Crear dataset",
        "archivo": "crear_dataset.py",
        "descripcion": "Preparamos todo lo que capturamos para que esté listo.",
        "emoji": "🧩",
        "color": "#7BC8F6",
    },
    {
        "nombre": "Entrenar modelo",
        "archivo": "entrenar_modelo.py",
        "descripcion": "¡El robot va a estudiar para reconocer tus señas!",
        "emoji": "🤖",
        "color": "#A78BFA",
    },
    {
        "nombre": "Administrar dataset",
        "archivo": "administrar_dataset.py",
        "descripcion": "Ver y organizar las señas guardadas.",
        "emoji": "🗂️",
        "color": "#FBBF24",
    },
]


# ==========================================================
# ESTILOS GENERALES
# ==========================================================

ESTILO = f"""
QWidget {{
    color: {NAVY};
    font-family: "Comic Sans MS", "Verdana", "Sans Serif";
    font-size: 14px;
}}

QLabel {{
    background: transparent;
}}

/* Contenedor principal */

QFrame#telefono {{
    background-color: {CREMA};
    border: 8px solid {CONTORNO};
    border-radius: 46px;
}}

/* Barra lateral */

QFrame#barra {{
    background-color: {NARANJA};
    border: none;
    border-top-left-radius: 38px;
    border-bottom-left-radius: 38px;
}}

QLabel#marca {{
    color: white;
    font-size: 21px;
    font-weight: 900;
    letter-spacing: 1px;
}}

QLabel#marca_sub {{
    color: #FFF3DD;
    font-size: 13px;
    font-weight: 800;
}}

QLabel#grupo {{
    color: #FFF3DD;
    font-size: 12px;
    font-weight: 900;
    letter-spacing: 3px;
    padding-left: 8px;
}}

QProgressBar {{
    background-color: #9C4A12;
    border: none;
    border-radius: 11px;
    min-height: 22px;
    max-height: 22px;
}}

QProgressBar::chunk {{
    background-color: #4CAF50;
    border-radius: 11px;
}}

/* Cabecera morada */

QFrame#cabecera {{
    background-color: {MORADO};
    border: none;
    border-top-right-radius: 38px;
}}

QLabel#titulo {{
    color: white;
    font-size: 32px;
    font-weight: 900;
}}

QLabel#saludo_sub {{
    color: #DCCBFF;
    font-size: 16px;
    font-weight: 700;
}}

QLabel#pastilla {{
    background-color: {NARANJA_PILL};
    border: none;
    border-bottom: 5px solid #D9661A;
    border-radius: 24px;
    color: white;
    font-size: 22px;
    font-weight: 900;
    padding: 4px 18px;
}}

/* Cuerpo crema */

QFrame#cuerpo {{
    background-color: {CREMA};
    border: none;
    border-bottom-right-radius: 38px;
}}

/* Mensajes */

QMessageBox {{
    background-color: {CREMA};
}}

QMessageBox QLabel {{
    font-size: 18px;
    font-weight: 800;
    color: {NAVY};
}}

QMessageBox QPushButton {{
    background-color: {MORADO};
    color: white;
    border: none;
    border-bottom: 5px solid {MORADO_OSCURO};
    border-radius: 20px;
    min-width: 120px;
    min-height: 40px;
    padding: 4px 18px;
    font-size: 17px;
    font-weight: 900;
}}

QMessageBox QPushButton:hover {{
    background-color: #7D60D6;
}}

QToolTip {{
    background-color: {MORADO};
    color: white;
    border: 2px solid #A78BFA;
    border-radius: 12px;
    padding: 8px;
    font-size: 14px;
    font-weight: 700;
}}
"""


# ==========================================================
# ESTILOS DE BOTONES
# ==========================================================

def estilo_pastilla(color, texto=NAVY, fuente=24, radio=30):

    borde = oscuro(color)

    return f"""
        QPushButton {{
            background-color: {color};
            color: {texto};
            border: none;
            border-bottom: 7px solid {borde};
            border-radius: {radio}px;
            padding: 10px 28px;
            font-size: {fuente}px;
            font-weight: 900;
        }}

        QPushButton:hover {{
            background-color: {claro(color)};
        }}

        QPushButton:pressed {{
            border-bottom: 3px solid {borde};
            padding-top: 14px;
        }}
    """


def estilo_nav(color, texto_activo):

    borde = oscuro(color)

    return f"""
        QPushButton {{
            background-color: {CREMA};
            color: {NAVY};
            border: none;
            border-bottom: 7px solid #D98A1A;
            border-radius: 32px;
            padding: 8px 18px;
            text-align: left;
            font-size: 19px;
            font-weight: 900;
        }}

        QPushButton:hover {{
            background-color: #FFFFFF;
        }}

        QPushButton:pressed {{
            border-bottom: 3px solid #D98A1A;
            padding-top: 12px;
        }}

        QPushButton:checked {{
            background-color: {color};
            color: {texto_activo};
            border: 4px solid #FFFFFF;
            border-bottom: 8px solid {borde};
        }}
    """


# ==========================================================
# FONDO AZUL
# ==========================================================

class FondoAzul(QWidget):

    def paintEvent(self, evento):

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        degradado = QLinearGradient(0, 0, 0, h)
        degradado.setColorAt(0.0, QColor("#9BDCF8"))
        degradado.setColorAt(1.0, QColor("#4BB3E8"))

        p.fillRect(self.rect(), degradado)

        p.setPen(Qt.PenStyle.NoPen)

        p.setBrush(QColor(255, 255, 255, 55))

        p.drawEllipse(
            int(-0.06 * w),
            int(0.50 * h),
            int(0.22 * w),
            int(0.55 * h)
        )

        p.drawEllipse(
            int(0.88 * w),
            int(0.05 * h),
            int(0.22 * w),
            int(0.45 * h)
        )

        p.drawEllipse(
            int(0.40 * w),
            int(-0.20 * h),
            int(0.30 * w),
            int(0.35 * h)
        )

        p.setBrush(QColor(30, 140, 210, 60))

        p.drawEllipse(
            int(0.84 * w),
            int(0.62 * h),
            int(0.28 * w),
            int(0.55 * h)
        )

        p.drawEllipse(
            int(-0.08 * w),
            int(-0.10 * h),
            int(0.20 * w),
            int(0.40 * h)
        )

        p.end()


# ==========================================================
# VENTANA PRINCIPAL
# ==========================================================

class GestosVision(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("🤖 SEÑITAS - ¡Aprende jugando! 🤖")
        self.setMinimumSize(1050, 740)

        self.procesos = []
        self.indices = {}
        self.info_paginas = {}
        self.botones_nav = {}
        self.visitadas = set()

        self.setStyleSheet(ESTILO)

        self.crear_interfaz()
        self.ir_a(0)

    # ======================================================
    # INTERFAZ GENERAL
    # ======================================================

    def crear_interfaz(self):

        fondo = FondoAzul()
        self.setCentralWidget(fondo)

        raiz = QVBoxLayout(fondo)
        raiz.setContentsMargins(22, 18, 22, 18)

        telefono = QFrame()
        telefono.setObjectName("telefono")

        raiz.addWidget(telefono)

        fila = QHBoxLayout(telefono)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(0)

        self.stack = QStackedWidget()

        self.stack.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        self.grupo_nav = QButtonGroup(self)
        self.grupo_nav.setExclusive(True)

        # Barra lateral

        barra, self.nav_layout = self.crear_barra_lateral()
        fila.addWidget(barra)

        # Cabecera y contenido

        derecha = QVBoxLayout()
        derecha.setSpacing(0)

        derecha.addWidget(self.crear_cabecera())

        cuerpo = QFrame()
        cuerpo.setObjectName("cuerpo")

        cuerpo_layout = QVBoxLayout(cuerpo)
        cuerpo_layout.setContentsMargins(20, 18, 20, 20)

        cuerpo_layout.addWidget(self.stack, 1)

        derecha.addWidget(cuerpo, 1)

        fila.addLayout(derecha, 1)

        self.crear_paginas()

        self.barra_progreso.setRange(0, self.stack.count())

    # ======================================================
    # BARRA LATERAL
    # ======================================================

    def crear_barra_lateral(self):

        barra = QFrame()
        barra.setObjectName("barra")
        barra.setFixedWidth(300)

        layout = QVBoxLayout(barra)

        layout.setContentsMargins(18, 20, 18, 18)
        layout.setSpacing(10)

        # Marca

        marca_fila = QHBoxLayout()
        marca_fila.setSpacing(12)

        logo = QLabel("🤖")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedSize(62, 62)

        logo.setStyleSheet("""
            background-color: #FFC93C;
            border: none;
            border-bottom: 5px solid #D9A21B;
            border-radius: 31px;
            font-size: 32px;
        """)

        textos = QVBoxLayout()
        textos.setSpacing(0)

        t1 = QLabel("SEÑITAS")
        t1.setObjectName("marca")

        t2 = QLabel("¡Aprende señas! ✨")
        t2.setObjectName("marca_sub")

        textos.addWidget(t1)
        textos.addWidget(t2)

        marca_fila.addWidget(logo)
        marca_fila.addLayout(textos, 1)

        layout.addLayout(marca_fila)
        layout.addSpacing(10)

        # Navegación

        nav = QVBoxLayout()
        nav.setSpacing(10)

        layout.addLayout(nav)

        layout.addStretch(1)

        # Progreso

        self.barra_progreso = QProgressBar()
        self.barra_progreso.setTextVisible(False)

        layout.addWidget(self.barra_progreso)

        # Salir

        salir = QPushButton("👋 Salir")
        salir.setMinimumHeight(54)

        salir.setCursor(Qt.CursorShape.PointingHandCursor)

        salir.setStyleSheet(
            estilo_pastilla(
                "#F87171",
                texto="white",
                fuente=19,
                radio=27
            )
        )

        salir.clicked.connect(self.close)

        layout.addWidget(salir)

        return barra, nav

    # ======================================================
    # CABECERA
    # ======================================================

    def crear_cabecera(self):

        cab = QFrame()
        cab.setObjectName("cabecera")
        cab.setFixedHeight(96)

        lay = QHBoxLayout(cab)

        lay.setContentsMargins(24, 8, 24, 8)
        lay.setSpacing(16)

        avatar = QLabel("🐵")
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(70, 70)

        avatar.setStyleSheet("""
            background-color: #FFD58A;
            border: 4px solid #FFC93C;
            border-radius: 35px;
            font-size: 38px;
        """)

        textos = QVBoxLayout()
        textos.setSpacing(0)

        self.lbl_titulo = QLabel("")
        self.lbl_titulo.setObjectName("titulo")

        self.lbl_sub = QLabel("")
        self.lbl_sub.setObjectName("saludo_sub")

        textos.addWidget(self.lbl_titulo)
        textos.addWidget(self.lbl_sub)

        self.pastilla_estrellas = QLabel("⭐ 0/0")
        self.pastilla_estrellas.setObjectName("pastilla")

        lay.addWidget(avatar)
        lay.addLayout(textos, 1)
        lay.addWidget(self.pastilla_estrellas)

        return cab

    # ======================================================
    # CREAR PÁGINAS
    # ======================================================

    def crear_paginas(self):

        for info in PAGINAS_JUGAR:

            widget = info["fabrica"]()

            setattr(self, info["attr"], widget)

            pagina = self.envolver_en_tarjeta(
                widget,
                info["color"]
            )

            self.agregar_pagina(info, pagina)

            self.indices[info["attr"]] = self.stack.count() - 1

        self.agregar_pagina(
            PAGINA_ADULTOS,
            self.crear_pagina_adultos()
        )

    def agregar_pagina(self, info, pagina):

        indice = self.stack.addWidget(pagina)

        boton = QPushButton(
            f'{info["emoji"]}  {info["nombre"]}'
        )

        boton.setCheckable(True)
        boton.setMinimumHeight(68)

        boton.setCursor(Qt.CursorShape.PointingHandCursor)

        boton.setStyleSheet(
            estilo_nav(
                info["color"],
                info["texto_activo"]
            )
        )

        boton.clicked.connect(
            lambda checked=False, i=indice: self.ir_a(i)
        )

        self.nav_layout.addWidget(boton)

        self.grupo_nav.addButton(boton, indice)

        self.botones_nav[indice] = boton
        self.info_paginas[indice] = info

    # ======================================================
    # TARJETA EXTERIOR
    # ======================================================

    def envolver_en_tarjeta(self, widget, color):

        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta")

        tarjeta.setStyleSheet(f"""
            QFrame#tarjeta {{
                background-color: #FFFFFF;
                border: 5px solid {color};
                border-radius: 32px;
            }}
        """)

        tarjeta.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(12, 12, 12, 12)

        widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        layout.addWidget(widget, 1)

        return tarjeta

    # ======================================================
    # PÁGINA DE ADULTOS
    # ======================================================

    def crear_pagina_adultos(self):

        pagina = QWidget()

        externo = QHBoxLayout(pagina)
        externo.setContentsMargins(0, 0, 0, 0)

        externo.addStretch(1)

        columna = QVBoxLayout()
        columna.setSpacing(16)

        columna.addStretch(1)

        for herramienta in HERRAMIENTAS_ADULTOS:
            columna.addWidget(
                self.crear_fila_herramienta(herramienta)
            )

        columna.addStretch(1)

        contenedor = QWidget()
        contenedor.setMaximumWidth(1000)
        contenedor.setMinimumWidth(600)
        contenedor.setLayout(columna)

        externo.addWidget(contenedor, 10)
        externo.addStretch(1)

        return pagina

    def crear_fila_herramienta(self, h):

        fila = QFrame()
        fila.setObjectName("fila")

        fila.setStyleSheet("""
            QFrame#fila {
                background-color: #FFFFFF;
                border: 4px solid #FFE0B2;
                border-bottom: 8px solid #FFD08A;
                border-radius: 36px;
            }
        """)

        lay = QHBoxLayout(fila)

        lay.setContentsMargins(20, 14, 22, 14)
        lay.setSpacing(20)

        avatar = QLabel(h["emoji"])
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setFixedSize(92, 92)

        avatar.setStyleSheet(f"""
            background-color: {h['color']};
            border: 5px solid {oscuro(h['color'])};
            border-radius: 46px;
            font-size: 46px;
        """)

        textos = QVBoxLayout()
        textos.setSpacing(2)

        nombre = QLabel(h["nombre"])

        nombre.setStyleSheet(
            f"font-size: 28px; font-weight: 900; color: {NAVY};"
        )

        desc = QLabel(h["descripcion"])
        desc.setWordWrap(True)

        desc.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #7A6A99;"
        )

        textos.addWidget(nombre)
        textos.addWidget(desc)

        boton = QPushButton("¡Abrir! 🚀")

        boton.setMinimumSize(200, 68)
        boton.setCursor(Qt.CursorShape.PointingHandCursor)

        boton.setStyleSheet(
            estilo_pastilla(
                h["color"],
                fuente=24,
                radio=34
            )
        )

        boton.clicked.connect(
            lambda checked=False, o=h: self.ejecutar_programa(o)
        )

        lay.addWidget(avatar)
        lay.addLayout(textos, 1)
        lay.addWidget(boton)

        return fila

    # ======================================================
    # NAVEGACIÓN
    # ======================================================

    def ir_a(self, indice):

        self.stack.setCurrentIndex(indice)

        self.botones_nav[indice].setChecked(True)

        info = self.info_paginas[indice]

        self.lbl_titulo.setText(
            f'{info["emoji"]} {info["nombre"]}'
        )

        self.lbl_sub.setText(info["subtitulo"])

        self.visitadas.add(indice)

        total = self.stack.count()

        self.pastilla_estrellas.setText(
            f"⭐ {len(self.visitadas)}/{total}"
        )

        self.barra_progreso.setValue(indice + 1)

        self._al_cambiar_pagina(indice)

    def _al_cambiar_pagina(self, indice):

        acciones = [
            ("widget_reconocer", "detener_reconocimiento"),
            ("widget_practica", "detener_practica"),
            ("widget_juego", "pausar"),
            ("widget_camino", "pausar"),
        ]

        for attr, metodo in acciones:

            if self.indices.get(attr) != indice and hasattr(self, attr):

                try:
                    getattr(
                        getattr(self, attr),
                        metodo
                    )()

                except Exception:
                    pass

    # ======================================================
    # EJECUTAR HERRAMIENTAS
    # ======================================================

    def ejecutar_programa(self, opcion):

        nombre = opcion["nombre"]
        ruta = BASE_DIR / opcion["archivo"]

        if not ruta.is_file():

            QMessageBox.warning(
                self,
                "¡Ups! 🙈",
                f"No encontramos el archivo:\n\n{ruta}\n\n"
                "Pídele a un adulto que lo revise.",
            )

            return

        try:

            proceso = subprocess.Popen(
                [sys.executable, str(ruta)],
                cwd=str(BASE_DIR),
            )

            self.procesos.append(proceso)

        except Exception as error:

            QMessageBox.critical(
                self,
                "¡Algo salió mal! 😢",
                f"No pudimos abrir {nombre}.\n\n{error}",
            )

    # ======================================================
    # CERRAR APLICACIÓN
    # ======================================================

    def closeEvent(self, event):

        respuesta = QMessageBox.question(
            self,
            "¡Hasta pronto! 👋",
            "¿Quieres cerrar SEÑITAS?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if respuesta != QMessageBox.StandardButton.Yes:

            event.ignore()
            return

        limpiezas = [
            ("widget_practica", "detener_practica"),
            ("widget_reconocer", "detener_reconocimiento"),
            ("widget_juego", "liberar"),
            ("widget_camino", "liberar"),
        ]

        for attr, metodo in limpiezas:

            if hasattr(self, attr):

                try:
                    getattr(
                        getattr(self, attr),
                        metodo
                    )()

                except Exception:
                    pass

        for proceso in self.procesos:

            if proceso.poll() is None:

                try:
                    proceso.terminate()

                except Exception:
                    pass

        event.accept()


# ==========================================================
# INICIO
# ==========================================================

def main():

    app = QApplication(sys.argv)

    app.setApplicationName("GESTOSVISION")
    app.setStyle("Fusion")

    ventana = GestosVision()
    ventana.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()