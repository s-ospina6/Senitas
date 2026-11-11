
import sys
import random
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QFrame,
)

from PySide6.QtGui import QPixmap, QFont, QIcon, QGuiApplication
from PySide6.QtCore import Qt, QTimer


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "imagenes_aprendizaje"

EXTENSIONS = (".jpg", ".jpeg", ".png")

COLUMNAS_MAX = 7

ANCHO_CARTA_BASE = 110
ALTO_CARTA_BASE = 130

PROPORCION_IMAGENES = 0.5
MIN_PAREJAS = 2
MAX_PAREJAS = 14


# ==========================================================
# PALETA GESTOSVISION
# ==========================================================

MORADO = "#6C4DC4"
MORADO_OSCURO = "#5B3A9E"

NARANJA = "#F7941D"
NARANJA_CLARO = "#FFB347"
NARANJA_OSCURO = "#D97706"

ROSA = "#F0527A"
ROSA_OSCURO = "#C93660"

CREMA = "#FFF3DD"
NAVY = "#2B3A67"
BLANCO = "#FFFFFF"

VERDE = "#4CAF50"
VERDE_CLARO = "#DDF5E3"
VERDE_OSCURO = "#318344"

LAVANDA = "#E8DFFF"
SECUNDARIO = "#7A6A99"
BORDE = "#FFD08A"


# ==========================================================
# VENTANA PRINCIPAL
# ==========================================================

class JuegoMemoria(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("GESTOSVISION - Juego de memoria")

        pantalla = QGuiApplication.primaryScreen().availableGeometry()

        ancho = min(780, pantalla.width() - 60)
        alto = min(620, pantalla.height() - 60)

        self.resize(ancho, alto)

        self.cartas = []
        self.seleccionadas = []
        self.parejas_encontradas = []

        self.intentos = 0
        self.parejas = 0
        self.bloqueado = False

        self.temporizador = QTimer()
        self.temporizador.setSingleShot(True)
        self.temporizador.timeout.connect(self.ocultar_cartas)

        self.imagenes = []
        self.imagenes_juego = []

        self.ancho_carta = ANCHO_CARTA_BASE
        self.alto_carta = ALTO_CARTA_BASE
        self.columnas_actuales = COLUMNAS_MAX

        self.botones = []

        self.crear_interfaz()
        self.cargar_imagenes()

    # ======================================================
    # INTERFAZ
    # ======================================================

    def crear_interfaz(self):

        central = QWidget()
        central.setObjectName("centralJuego")
        self.setCentralWidget(central)

        layout_principal = QVBoxLayout(central)
        layout_principal.setSpacing(10)
        layout_principal.setContentsMargins(14, 12, 14, 12)

        # Título

        titulo = QLabel("¡JUEGO DE MEMORIA!")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Comic Sans MS", 19, QFont.Weight.Bold))

        titulo.setStyleSheet(f"""
            QLabel {{
                color: {NAVY};
                background: transparent;
                border: none;
                padding: 4px;
            }}
        """)

        layout_principal.addWidget(titulo)

        # Instrucciones

        instrucciones = QLabel(
            "Encuentra la pareja: relaciona cada palabra con su seña."
        )

        instrucciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instrucciones.setWordWrap(True)

        instrucciones.setStyleSheet(f"""
            QLabel {{
                color: {SECUNDARIO};
                font-family: "Comic Sans MS", "Verdana";
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
                padding: 2px;
            }}
        """)

        layout_principal.addWidget(instrucciones)

        # Marcadores

        informacion = QHBoxLayout()
        informacion.setSpacing(12)

        self.label_intentos = QLabel("Intentos: 0")
        self.label_parejas = QLabel("Parejas: 0")

        for etiqueta in (
            self.label_intentos,
            self.label_parejas
        ):

            etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)

            etiqueta.setStyleSheet(f"""
                QLabel {{
                    background-color: {LAVANDA};
                    color: {MORADO_OSCURO};
                    border: 2px solid {MORADO};
                    border-radius: 12px;
                    padding: 8px 14px;
                    font-family: "Comic Sans MS", "Verdana";
                    font-size: 12px;
                    font-weight: bold;
                }}
            """)

        informacion.addWidget(self.label_intentos)
        informacion.addStretch()
        informacion.addWidget(self.label_parejas)

        layout_principal.addLayout(informacion)

        # Tablero

        self.contenedor_tablero = QWidget()
        self.contenedor_tablero.setStyleSheet(
            "background-color: transparent;"
        )

        self.tablero = QGridLayout(self.contenedor_tablero)
        self.tablero.setSpacing(10)
        self.tablero.setContentsMargins(8, 8, 8, 8)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.contenedor_tablero)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}

            QScrollArea > QWidget > QWidget {{
                background-color: transparent;
            }}
        """)

        layout_principal.addWidget(self.scroll, stretch=1)

        # Mensaje

        self.mensaje = QLabel("¡Encuentra todas las parejas!")

        self.mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mensaje.setWordWrap(True)

        self.mensaje.setStyleSheet(f"""
            QLabel {{
                color: {NAVY};
                background-color: {CREMA};
                border: 2px solid {BORDE};
                border-radius: 14px;
                padding: 9px;
                font-family: "Comic Sans MS", "Verdana";
                font-size: 12px;
                font-weight: bold;
            }}
        """)

        layout_principal.addWidget(self.mensaje)

        # Únicamente el botón de nuevo juego.

        self.boton_reiniciar = QPushButton("↻  Nuevo juego")
        self.boton_reiniciar.setMinimumHeight(44)
        self.boton_reiniciar.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.boton_reiniciar.clicked.connect(self.nuevo_juego)

        self.boton_reiniciar.setStyleSheet(f"""
            QPushButton {{
                background-color: {MORADO};
                color: {BLANCO};
                border: 2px solid {MORADO};
                border-bottom: 5px solid {MORADO_OSCURO};
                border-radius: 15px;
                padding: 8px 20px;
                font-family: "Comic Sans MS", "Verdana";
                font-size: 13px;
                font-weight: bold;
            }}

            QPushButton:hover {{
                background-color: #8065D5;
            }}

            QPushButton:pressed {{
                background-color: {MORADO_OSCURO};
                border-bottom: 2px solid {MORADO_OSCURO};
            }}
        """)

        layout_principal.addWidget(self.boton_reiniciar)

        # Fondo general

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {CREMA};
            }}

            QWidget#centralJuego {{
                background-color: transparent;
                color: {NAVY};
                font-family: "Comic Sans MS", "Verdana";
            }}
        """)

    # ======================================================
    # CARGAR IMÁGENES
    # ======================================================

    def cargar_imagenes(self):

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

        self.imagenes = sorted(
            [
                archivo
                for archivo in IMAGE_DIR.iterdir()
                if archivo.is_file()
                and archivo.suffix.lower() in EXTENSIONS
            ],
            key=lambda x: x.stem.casefold()
        )

        if not self.imagenes:

            QMessageBox.warning(
                self,
                "Sin imágenes",
                f"No hay imágenes disponibles en:\n{IMAGE_DIR}"
            )

            self.close()
            return

        if len(self.imagenes) < MIN_PAREJAS:

            QMessageBox.warning(
                self,
                "Imágenes insuficientes",
                "Necesitas al menos dos imágenes para jugar."
            )

            self.close()
            return

        self.nuevo_juego()

    # ======================================================
    # AJUSTAR TAMAÑO Y DISTRIBUCIÓN DE CARTAS
    # ======================================================

    def ajustar_tamano_cartas(self):

        # Siempre utilizar 7 columnas.

        self.columnas_actuales = COLUMNAS_MAX

        # Mantener el tamaño original de las tarjetas.

        self.ancho_carta = ANCHO_CARTA_BASE
        self.alto_carta = ALTO_CARTA_BASE

    # ======================================================
    # CREAR JUEGO
    # ======================================================

    def nuevo_juego(self):

        self.temporizador.stop()

        self.seleccionadas = []
        self.parejas_encontradas = []

        self.intentos = 0
        self.parejas = 0

        self.bloqueado = False

        total_disponibles = len(self.imagenes)

        if total_disponibles < MIN_PAREJAS:
            return

        # Seleccionar hasta 14 imágenes para crear
        # un máximo de 28 tarjetas.

        cantidad = min(
            MAX_PAREJAS,
            total_disponibles
        )

        self.imagenes_juego = random.sample(
            self.imagenes,
            cantidad
        )

        self.ajustar_tamano_cartas()

        self.cartas = []

        for imagen in self.imagenes_juego:

            nombre = imagen.stem.upper()

            self.cartas.append({
                "tipo": "texto",
                "nombre": nombre,
                "imagen": imagen,
            })

            self.cartas.append({
                "tipo": "imagen",
                "nombre": nombre,
                "imagen": imagen,
            })

        random.shuffle(self.cartas)

        self.actualizar_informacion()

        self.mensaje.setText("¡Encuentra todas las parejas!")

        self.crear_tablero()

    # ======================================================
    # CONSTRUIR TABLERO
    # ======================================================

    def crear_tablero(self):

        while self.tablero.count():

            elemento = self.tablero.takeAt(0)
            widget = elemento.widget()

            if widget:
                widget.deleteLater()

        self.botones = []

        for indice, carta in enumerate(self.cartas):

            boton = QPushButton("?")

            boton.setFixedSize(
                self.ancho_carta,
                self.alto_carta
            )

            boton.setFont(
                QFont("Comic Sans MS", 22, QFont.Weight.Bold)
            )

            self.aplicar_estilo_carta_oculta(boton)

            boton.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            boton.clicked.connect(
                lambda checked=False, i=indice:
                self.voltear_carta(i)
            )

            fila = indice // self.columnas_actuales
            columna = indice % self.columnas_actuales

            self.tablero.addWidget(
                boton,
                fila,
                columna
            )

            self.botones.append(boton)

        self.tablero.setAlignment(
            Qt.AlignmentFlag.AlignTop |
            Qt.AlignmentFlag.AlignHCenter
        )

    # ======================================================
    # ESTILO DE CARTA OCULTA
    # ======================================================

    def aplicar_estilo_carta_oculta(self, boton):

        boton.setStyleSheet(f"""
            QPushButton {{
                background-color: {NARANJA};
                color: {BLANCO};
                border: 3px solid {NARANJA_OSCURO};
                border-bottom: 7px solid #B85F08;
                border-radius: 17px;
                font-family: "Comic Sans MS", "Verdana";
                font-size: 24px;
                font-weight: bold;
            }}

            QPushButton:hover:enabled {{
                background-color: {NARANJA_CLARO};
                border-color: {NARANJA_OSCURO};
                border-bottom: 7px solid #B85F08;
            }}

            QPushButton:pressed:enabled {{
                background-color: {NARANJA_OSCURO};
                border-bottom: 3px solid #B85F08;
            }}

            QPushButton:disabled {{
                background-color: {NARANJA};
                color: {BLANCO};
            }}
        """)

    # ======================================================
    # MOSTRAR CARTA
    # ======================================================

    def mostrar_carta(self, indice):

        carta = self.cartas[indice]
        boton = self.botones[indice]

        if carta["tipo"] == "texto":

            boton.setText(carta["nombre"])
            boton.setIcon(QIcon())

            boton.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BLANCO};
                    color: {MORADO_OSCURO};
                    border: 3px solid {MORADO};
                    border-bottom: 6px solid {MORADO_OSCURO};
                    border-radius: 17px;
                    font-family: "Comic Sans MS", "Verdana";
                    font-size: 13px;
                    font-weight: bold;
                    padding: 4px;
                }}
            """)

        else:

            pixmap = QPixmap(str(carta["imagen"]))

            pixmap = pixmap.scaled(
                self.ancho_carta - 25,
                self.alto_carta - 35,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            boton.setText("")
            boton.setIcon(QIcon(pixmap))
            boton.setIconSize(pixmap.size())

            boton.setStyleSheet(f"""
                QPushButton {{
                    background-color: {BLANCO};
                    border: 3px solid {MORADO};
                    border-bottom: 6px solid {MORADO_OSCURO};
                    border-radius: 17px;
                    padding: 4px;
                }}
            """)

    # ======================================================
    # OCULTAR CARTA
    # ======================================================

    def ocultar_carta(self, indice):

        boton = self.botones[indice]

        boton.setText("?")
        boton.setIcon(QIcon())

        self.aplicar_estilo_carta_oculta(boton)

    # ======================================================
    # VOLTEAR CARTA
    # ======================================================

    def voltear_carta(self, indice):

        if self.bloqueado:
            return

        if indice in self.seleccionadas:
            return

        if indice in self.parejas_encontradas:
            return

        self.mostrar_carta(indice)

        self.seleccionadas.append(indice)

        if len(self.seleccionadas) == 2:

            self.intentos += 1

            self.actualizar_informacion()
            self.comprobar_pareja()

    # ======================================================
    # COMPROBAR PAREJA
    # ======================================================

    def comprobar_pareja(self):

        carta1 = self.cartas[self.seleccionadas[0]]
        carta2 = self.cartas[self.seleccionadas[1]]

        if (
            carta1["nombre"] == carta2["nombre"]
            and carta1["tipo"] != carta2["tipo"]
        ):

            self.mensaje.setText(
                f"¡Correcto! Encontraste: {carta1['nombre']}"
            )

            self.parejas_encontradas.extend(
                self.seleccionadas
            )

            self.parejas += 1

            for indice in self.seleccionadas:

                boton = self.botones[indice]

                boton.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {VERDE_CLARO};
                        color: {VERDE_OSCURO};
                        border: 3px solid {VERDE};
                        border-bottom: 6px solid {VERDE_OSCURO};
                        border-radius: 17px;
                        font-family: "Comic Sans MS", "Verdana";
                        font-weight: bold;
                    }}
                """)

                boton.setEnabled(False)

            self.seleccionadas = []

            self.actualizar_informacion()

            if self.parejas == len(self.imagenes_juego):
                self.finalizar_juego()

        else:

            self.mensaje.setText(
                "No coinciden. ¡Inténtalo otra vez!"
            )

            self.bloqueado = True
            self.temporizador.start(1000)

    # ======================================================
    # OCULTAR CARTAS INCORRECTAS
    # ======================================================

    def ocultar_cartas(self):

        for indice in self.seleccionadas:
            self.ocultar_carta(indice)

        self.seleccionadas = []
        self.bloqueado = False

        self.mensaje.setText(
            "¡Continúa buscando las parejas!"
        )

    # ======================================================
    # ACTUALIZAR INFORMACIÓN
    # ======================================================

    def actualizar_informacion(self):

        self.label_intentos.setText(
            f"Intentos: {self.intentos}"
        )

        self.label_parejas.setText(
            f"Parejas: {self.parejas}/{len(self.imagenes_juego)}"
        )

    # ======================================================
    # FINALIZAR JUEGO
    # ======================================================

    def finalizar_juego(self):

        self.mensaje.setText(
            "¡FELICITACIONES! Encontraste todas las parejas."
        )

        QMessageBox.information(
            self,
            "¡Juego terminado!",
            f"¡Excelente trabajo!\n\n"
            f"Parejas encontradas: {self.parejas}\n"
            f"Intentos realizados: {self.intentos}"
        )


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():

    app = QApplication(sys.argv)

    ventana = JuegoMemoria()
    ventana.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
