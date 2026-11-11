
import random
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QSizePolicy
)


BASE_DIR = Path(__file__).resolve().parent.parent
IMAGENES_DIR = BASE_DIR / "imagenes_aprendizaje"

MORADO = "#6C4DC4"
MORADO_OSCURO = "#5B3A9E"
NARANJA = "#F7941D"
NAVY = "#2B3A67"
CREMA = "#FFF3DD"
ROSA = "#F0527A"
VERDE = "#4CAF50"


class JuegoCaminoLetras(QWidget):

    FILAS = 4
    COLUMNAS = 4

    INICIO = (0, 0)
    META = (3, 3)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.letras_disponibles = self.cargar_letras()
        self.botones = []
        self.camino = []
        self.letras_celdas = {}

        self.posicion_inicio = self.INICIO
        self.posicion_meta = self.META
        self.posicion_actual = self.INICIO

        self.indice_camino = 0
        self.movimientos = 0
        self.terminado = False
        self.en_pausa = False

        self.crear_interfaz()
        self.nuevo_juego()

    # ------------------------------------------------------
    # CARGAR IMÁGENES
    # ------------------------------------------------------

    def cargar_letras(self):

        letras = {}

        if not IMAGENES_DIR.exists():
            return letras

        for archivo in IMAGENES_DIR.iterdir():

            if archivo.is_file() and archivo.suffix.lower() in (
                ".jpg", ".jpeg", ".png"
            ):

                letra = archivo.stem.upper()

                if len(letra) == 1 and letra.isalpha():
                    letras[letra] = archivo

        return letras

    # ------------------------------------------------------
    # INTERFAZ
    # ------------------------------------------------------

    def crear_interfaz(self):

        principal = QVBoxLayout(self)
        principal.setContentsMargins(12, 12, 12, 12)
        principal.setSpacing(12)

        self.lbl_instruccion = QLabel(
            "¡Encuentra las señas correctas y llega a la meta!"
        )
        self.lbl_instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_instruccion.setWordWrap(True)
        self.lbl_instruccion.setStyleSheet(f"""
            color: {NAVY};
            font-size: 19px;
            font-weight: 900;
            background: transparent;
        """)
        principal.addWidget(self.lbl_instruccion)

        # Tarjeta de objetivo
        tarjeta_objetivo = QFrame()
        tarjeta_objetivo.setStyleSheet("""
            QFrame {
                background-color: #FFF3DD;
                border: 3px solid #FFD08A;
                border-radius: 22px;
            }
        """)

        objetivo_layout = QHBoxLayout(tarjeta_objetivo)
        objetivo_layout.setContentsMargins(12, 8, 12, 8)
        objetivo_layout.setSpacing(12)

        texto_objetivo = QLabel("LETRA OBJETIVO:")
        texto_objetivo.setStyleSheet(f"""
            color: {NAVY};
            font-size: 17px;
            font-weight: 900;
            border: none;
            background: transparent;
        """)

        self.lbl_objetivo = QLabel("?")
        self.lbl_objetivo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_objetivo.setFixedSize(58, 58)
        self.lbl_objetivo.setStyleSheet(f"""
            background-color: {MORADO};
            color: white;
            border: none;
            border-bottom: 5px solid {MORADO_OSCURO};
            border-radius: 18px;
            font-size: 34px;
            font-weight: 900;
        """)

        self.lbl_progreso = QLabel("Camino: 0/6")
        self.lbl_progreso.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_progreso.setStyleSheet(f"""
            color: {NAVY};
            font-size: 16px;
            font-weight: 900;
            background: transparent;
            border: none;
        """)

        objetivo_layout.addWidget(texto_objetivo)
        objetivo_layout.addWidget(self.lbl_objetivo)
        objetivo_layout.addStretch(1)
        objetivo_layout.addWidget(self.lbl_progreso)

        principal.addWidget(tarjeta_objetivo)

        # Tablero
        tarjeta_tablero = QFrame()
        tarjeta_tablero.setStyleSheet("""
            QFrame {
                background-color: #FFFFFF;
                border: 4px solid #FFD08A;
                border-radius: 26px;
            }
        """)

        tablero_layout = QVBoxLayout(tarjeta_tablero)
        tablero_layout.setContentsMargins(12, 12, 12, 12)

        self.layout_tablero = QGridLayout()
        self.layout_tablero.setSpacing(9)
        tablero_layout.addLayout(self.layout_tablero)

        principal.addWidget(tarjeta_tablero, 1)

        # Mensaje de estado
        self.lbl_estado = QLabel("¡Busca la letra objetivo!")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setMinimumHeight(42)
        self.lbl_estado.setStyleSheet(f"""
            color: {MORADO};
            font-size: 16px;
            font-weight: 900;
            background: transparent;
        """)
        principal.addWidget(self.lbl_estado)

        # Botón nuevo juego
        self.boton_nuevo = QPushButton("🔄  ¡Nuevo juego!")
        self.boton_nuevo.setMinimumHeight(58)
        self.boton_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_nuevo.setStyleSheet(f"""
            QPushButton {{
                background-color: {NARANJA};
                color: white;
                border: none;
                border-bottom: 6px solid #D97706;
                border-radius: 24px;
                padding: 8px 20px;
                font-size: 19px;
                font-weight: 900;
            }}
            QPushButton:hover {{
                background-color: #FFAA38;
            }}
            QPushButton:pressed {{
                border-bottom: 2px solid #D97706;
                padding-top: 12px;
            }}
        """)

        self.boton_nuevo.clicked.connect(self.nuevo_juego)
        principal.addWidget(self.boton_nuevo)

        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                font-family: "Comic Sans MS", "Verdana", sans-serif;
            }
        """)

    # ------------------------------------------------------
    # MOVIMIENTOS ENTRE CASILLAS
    # ------------------------------------------------------

    def vecinos(self, posicion):

        fila, columna = posicion

        posibles = [
            (fila - 1, columna),
            (fila + 1, columna),
            (fila, columna - 1),
            (fila, columna + 1),
        ]

        return [
            (f, c) for f, c in posibles
            if 0 <= f < self.FILAS
            and 0 <= c < self.COLUMNAS
        ]

    # ------------------------------------------------------
    # DISTANCIA HASTA LA META
    # ------------------------------------------------------

    def distancia_meta(self, posicion):

        return (
            abs(self.META[0] - posicion[0]) +
            abs(self.META[1] - posicion[1])
        )

    # ------------------------------------------------------
    # GENERAR RECORRIDO CORTO
    # ------------------------------------------------------

    def generar_tablero(self):

        fila, columna = self.INICIO
        camino = []

        movimientos = (
            ["abajo"] * 3 +
            ["derecha"] * 3
        )

        random.shuffle(movimientos)

        for movimiento in movimientos:

            if movimiento == "abajo":
                fila += 1
            else:
                columna += 1

            posicion = (fila, columna)

            if posicion != self.META:
                camino.append(posicion)

        return camino

    # ------------------------------------------------------
    # NUEVA PARTIDA
    # ------------------------------------------------------

    def nuevo_juego(self):

        self.letras_disponibles = self.cargar_letras()

        if len(self.letras_disponibles) < 2:

            self.lbl_estado.setText(
                "No encontramos suficientes imágenes de letras. "
                "Revisa la carpeta imagenes_aprendizaje."
            )

            self.lbl_objetivo.setText("?")
            self.lbl_progreso.setText("Camino: 0/6")

            self.limpiar_tablero()

            self.terminado = True
            self.en_pausa = False

            return

        self.letra_objetivo = random.choice(
            list(self.letras_disponibles.keys())
        )

        self.posicion_inicio = self.INICIO
        self.posicion_meta = self.META
        self.posicion_actual = self.INICIO

        self.camino = self.generar_tablero()

        self.indice_camino = 0
        self.movimientos = 0
        self.terminado = False
        self.en_pausa = False

        self.lbl_objetivo.setText(self.letra_objetivo)
        self.lbl_progreso.setText("Camino: 0/6")

        self.lbl_estado.setText(
            "¡Empieza en la esquina superior izquierda y sigue las señas!"
        )

        self.construir_tablero()

    # ------------------------------------------------------
    # CONSTRUIR TABLERO
    # ------------------------------------------------------

    def limpiar_tablero(self):

        while self.layout_tablero.count():

            elemento = self.layout_tablero.takeAt(0)
            widget = elemento.widget()

            if widget is not None:
                widget.deleteLater()

        self.botones = []

    def construir_tablero(self):

        self.limpiar_tablero()

        ocupadas = {
            self.posicion_inicio,
            self.posicion_meta,
            *self.camino
        }

        distractores = [
            letra for letra in self.letras_disponibles
            if letra != self.letra_objetivo
        ]

        self.letras_celdas = {}

        celdas = {}

        celdas[self.posicion_inicio] = ("inicio", None)
        celdas[self.posicion_meta] = ("meta", None)

        for posicion in self.camino:

            celdas[posicion] = (
                "objetivo",
                self.letra_objetivo
            )

            self.letras_celdas[posicion] = self.letra_objetivo

        for fila in range(self.FILAS):
            for columna in range(self.COLUMNAS):

                posicion = (fila, columna)

                if posicion not in ocupadas:

                    letra = random.choice(distractores)

                    celdas[posicion] = ("distractor", letra)
                    self.letras_celdas[posicion] = letra

        for fila in range(self.FILAS):

            fila_botones = []

            for columna in range(self.COLUMNAS):

                posicion = (fila, columna)
                tipo, letra = celdas[posicion]

                boton = QPushButton()

                boton.setMinimumSize(75, 88)

                boton.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding
                )

                boton.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )

                if tipo == "inicio":

                    boton.setText("🚩\nINICIO")

                    boton.setStyleSheet(
                        self.estilo_casilla(
                            "#E8DFFF",
                            MORADO,
                            MORADO_OSCURO
                        )
                    )

                elif tipo == "meta":

                    boton.setText("🏁\nMETA")

                    boton.setStyleSheet(
                        self.estilo_casilla(
                            "#DDF4DF",
                            VERDE,
                            "#31823A"
                        )
                    )

                else:

                    ruta = self.letras_disponibles[letra]
                    pixmap = QPixmap(str(ruta))

                    boton.setText("")

                    if not pixmap.isNull():

                        imagen = pixmap.scaled(
                            QSize(78, 68),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )

                        boton.setIcon(QIcon(imagen))
                        boton.setIconSize(imagen.size())

                    boton.setStyleSheet(
                        self.estilo_casilla(
                            "#FFF3DD",
                            NARANJA,
                            "#D97706"
                        )
                    )

                boton.clicked.connect(
                    lambda checked=False, p=posicion:
                    self.seleccionar_casilla(p)
                )

                self.layout_tablero.addWidget(
                    boton,
                    fila,
                    columna
                )

                fila_botones.append(boton)

            self.botones.append(fila_botones)

    # ------------------------------------------------------
    # ESTILO DE LAS CASILLAS
    # ------------------------------------------------------

    def estilo_casilla(self, fondo, borde, borde_oscuro):

        return f"""
            QPushButton {{
                background-color: {fondo};
                color: {NAVY};
                border: 3px solid {borde};
                border-bottom: 6px solid {borde_oscuro};
                border-radius: 15px;
                padding: 3px;
                font-size: 15px;
                font-weight: 900;
            }}

            QPushButton:hover {{
                background-color: #FFFFFF;
            }}

            QPushButton:pressed {{
                border-bottom: 2px solid {borde_oscuro};
                padding-top: 5px;
            }}

            QPushButton:disabled {{
                opacity: 1;
            }}
        """

    # ------------------------------------------------------
    # MOVIMIENTO DEL ESTUDIANTE
    # ------------------------------------------------------

    def seleccionar_casilla(self, posicion):

        if self.terminado or self.en_pausa:
            return

        # Solo permitir movimientos a casillas vecinas.
        if posicion not in self.vecinos(self.posicion_actual):

            self.lbl_estado.setText(
                "¡Avanza paso a paso! Busca una carta vecina. 😊"
            )

            return

        # Comprobar si llegó a la meta.
        if posicion == self.posicion_meta:

            if self.distancia_meta(self.posicion_actual) == 1:
                self.ganar_juego()

            else:
                self.lbl_estado.setText(
                    "¡Todavía falta encontrar las señas correctas!"
                )

            return

        # No permitir volver al inicio.
        if posicion == self.posicion_inicio:

            self.lbl_estado.setText(
                "¡Ya estás en el inicio! Continúa hacia la meta."
            )

            return

        # Obtener la letra de la carta.
        letra = self.letras_celdas.get(posicion)

        # Comprobar si es la letra objetivo.
        if letra != self.letra_objetivo:

            self.lbl_estado.setText(
                "¡Esa no es la seña correcta! Busca otra imagen. 😊"
            )

            return

        # Comprobar que el movimiento acerque a la meta.
        distancia_actual = self.distancia_meta(
            self.posicion_actual
        )

        nueva_distancia = self.distancia_meta(posicion)

        if nueva_distancia >= distancia_actual:

            self.lbl_estado.setText(
                "¡Busca una carta correcta que te acerque a la meta! ⭐"
            )

            return

        # Movimiento correcto.
        self.posicion_actual = posicion
        self.movimientos += 1
        self.indice_camino += 1

        boton = self.botones[posicion[0]][posicion[1]]

        boton.setEnabled(False)

        boton.setStyleSheet("""
            QPushButton {
                background-color: #DDF4DF;
                border: 4px solid #4CAF50;
                border-radius: 15px;
            }
        """)

        self.lbl_progreso.setText(
            f"Camino: {self.movimientos}/6"
        )

        if self.distancia_meta(self.posicion_actual) == 1:

            self.lbl_estado.setText(
                "¡Excelente! ¡Ya estás junto a la META! 🏁"
            )

        else:

            self.lbl_estado.setText(
                "¡Muy bien! Encontraste una seña correcta. ⭐"
            )

    # ------------------------------------------------------
    # GANAR JUEGO
    # ------------------------------------------------------

    def ganar_juego(self):

        self.terminado = True
        self.posicion_actual = self.posicion_meta

        self.lbl_estado.setText(
            "🎉 ¡LO LOGRASTE! ¡Llegaste a la meta! 🎉"
        )

        boton_meta = self.botones[
            self.posicion_meta[0]
        ][
            self.posicion_meta[1]
        ]

        boton_meta.setStyleSheet("""
            QPushButton {
                background-color: #B8F2C0;
                color: #205C2B;
                border: 4px solid #4CAF50;
                border-radius: 15px;
                font-size: 17px;
                font-weight: 900;
            }
        """)

        for fila in self.botones:
            for boton in fila:
                boton.setEnabled(False)

    # ------------------------------------------------------
    # CONTROL DESDE LA VENTANA PRINCIPAL
    # ------------------------------------------------------

    def pausar(self):

        self.en_pausa = True

    def reiniciar(self):

        self.nuevo_juego()

    def liberar(self):

        self.en_pausa = True

        for fila in self.botones:
            for boton in fila:
                boton.setEnabled(False)
