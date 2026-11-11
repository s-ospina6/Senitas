# juego1.py
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
)

from PySide6.QtGui import QPixmap, QFont, QIcon, QGuiApplication
from PySide6.QtCore import Qt, QTimer


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

IMAGE_DIR = BASE_DIR / "imagenes_aprendizaje"

EXTENSIONS = (".jpg", ".jpeg", ".png")

COLUMNAS_MAX = 6

ANCHO_CARTA_BASE = 110
ALTO_CARTA_BASE = 130

# Proporción de imágenes que se usarán en cada partida (0.5 = la mitad)
PROPORCION_IMAGENES = 0.5

# Mínimo de parejas por partida (aunque haya pocas imágenes)
MIN_PAREDAS = 2


# ==========================================================
# VENTANA PRINCIPAL
# ==========================================================

class JuegoMemoria(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("GESTOSVISION - Juego de memoria")

        # Ajustar tamaño a la pantalla disponible (más compacto)
        pantalla = QGuiApplication.primaryScreen().availableGeometry()
        ancho = min(780, pantalla.width() - 60)
        alto = min(620, pantalla.height() - 60)
        self.resize(ancho, alto)

        # Estado del juego
        self.cartas = []
        self.seleccionadas = []
        self.parejas_encontradas = []

        self.intentos = 0
        self.parejas = 0

        self.bloqueado = False

        self.temporizador = QTimer()
        self.temporizador.setSingleShot(True)
        self.temporizador.timeout.connect(self.ocultar_cartas)

        # Imágenes disponibles en disco
        self.imagenes = []

        # Imágenes elegidas para la partida actual
        self.imagenes_juego = []

        # Tamaño dinámico de cartas
        self.ancho_carta = ANCHO_CARTA_BASE
        self.alto_carta = ALTO_CARTA_BASE
        self.columnas_actuales = 4

        self.crear_interfaz()

        self.cargar_imagenes()

    # ======================================================
    # INTERFAZ
    # ======================================================

    def crear_interfaz(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout_principal = QVBoxLayout(central)
        layout_principal.setSpacing(8)
        layout_principal.setContentsMargins(10, 10, 10, 10)

        # Título
        titulo = QLabel("JUEGO DE MEMORIA")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        layout_principal.addWidget(titulo)

        # Instrucciones
        instrucciones = QLabel(
            "Encuentra la pareja: relaciona cada palabra con su seña."
        )
        instrucciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instrucciones.setFont(QFont("Arial", 10))
        layout_principal.addWidget(instrucciones)

        # Información del juego
        informacion = QHBoxLayout()

        self.label_intentos = QLabel("Intentos: 0")
        self.label_parejas = QLabel("Parejas: 0")

        self.label_intentos.setFont(QFont("Arial", 10))
        self.label_parejas.setFont(QFont("Arial", 10))

        informacion.addWidget(self.label_intentos)
        informacion.addStretch()
        informacion.addWidget(self.label_parejas)

        layout_principal.addLayout(informacion)

        # Tablero dentro de un QScrollArea para que nunca se desborde
        self.contenedor_tablero = QWidget()
        self.tablero = QGridLayout(self.contenedor_tablero)
        self.tablero.setSpacing(8)
        self.tablero.setContentsMargins(5, 5, 5, 5)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.contenedor_tablero)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; }")

        layout_principal.addWidget(self.scroll, stretch=1)

        # Mensaje
        self.mensaje = QLabel("¡Encuentra todas las parejas!")
        self.mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mensaje.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout_principal.addWidget(self.mensaje)

        # Botones inferiores
        botones = QHBoxLayout()

        self.boton_reiniciar = QPushButton("Nuevo juego")
        self.boton_reiniciar.clicked.connect(self.nuevo_juego)

        self.boton_salir = QPushButton("Salir")
        self.boton_salir.clicked.connect(self.close)

        botones.addWidget(self.boton_reiniciar)
        botones.addWidget(self.boton_salir)

        layout_principal.addLayout(botones)

        self.setStyleSheet("""

            QMainWindow {
                background-color: #F2F4F8;
            }

            QLabel {
                color: #202938;
            }

            QPushButton {
                background-color: #FFFFFF;
                border: 2px solid #D5DCE5;
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #E2EAF5;
            }

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

        if len(self.imagenes) < 2:

            QMessageBox.warning(
                self,
                "Imágenes insuficientes",
                "Necesitas al menos dos imágenes para jugar."
            )

            self.close()
            return

        self.nuevo_juego()

    # ======================================================
    # AJUSTAR TAMAÑO DE CARTAS SEGÚN CANTIDAD
    # ======================================================

    def ajustar_tamano_cartas(self):

        total = len(self.imagenes_juego) * 2

        # Columnas: entre 4 y COLUMNAS_MAX
        if total <= 8:
            self.columnas_actuales = 4
        elif total <= 12:
            self.columnas_actuales = 4
        elif total <= 20:
            self.columnas_actuales = 5
        else:
            self.columnas_actuales = COLUMNAS_MAX

        # Cartas más compactas
        if total <= 12:
            self.ancho_carta = ANCHO_CARTA_BASE
            self.alto_carta = ALTO_CARTA_BASE
        elif total <= 20:
            self.ancho_carta = 95
            self.alto_carta = 115
        else:
            self.ancho_carta = 85
            self.alto_carta = 105

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

        # --------------------------------------------------
        # Elegir solo una parte de las imágenes al azar
        # --------------------------------------------------
        total_disponibles = len(self.imagenes)
        cantidad = max(MIN_PAREDAS, int(total_disponibles * PROPORCION_IMAGENES))
        cantidad = min(cantidad, total_disponibles)  # no pedir más de las que hay

        self.imagenes_juego = random.sample(self.imagenes, cantidad)

        self.ajustar_tamano_cartas()

        # Crear dos cartas por imagen:
        # Una carta de texto y otra de imagen.
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

        # Mezclar las cartas
        random.shuffle(self.cartas)

        self.actualizar_informacion()

        self.mensaje.setText("¡Encuentra todas las parejas!")

        self.crear_tablero()

    # ======================================================
    # CONSTRUIR TABLERO
    # ======================================================

    def crear_tablero(self):

        # Eliminar cartas anteriores
        while self.tablero.count():

            elemento = self.tablero.takeAt(0)

            widget = elemento.widget()

            if widget:
                widget.deleteLater()

        self.botones = []

        for indice, carta in enumerate(self.cartas):

            boton = QPushButton("?")

            boton.setFixedSize(self.ancho_carta, self.alto_carta)

            boton.setFont(
                QFont("Arial", 18, QFont.Weight.Bold)
            )

            boton.setStyleSheet("""

                QPushButton {
                    background-color: #34495E;
                    color: white;
                    border: 3px solid #263747;
                    border-radius: 15px;
                }

                QPushButton:hover {
                    background-color: #46627D;
                }

            """)

            boton.clicked.connect(
                lambda checked=False, i=indice: self.voltear_carta(i)
            )

            fila = indice // self.columnas_actuales
            columna = indice % self.columnas_actuales

            self.tablero.addWidget(boton, fila, columna)

            self.botones.append(boton)

        self.tablero.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

    # ======================================================
    # MOSTRAR CARTA
    # ======================================================

    def mostrar_carta(self, indice):

        carta = self.cartas[indice]
        boton = self.botones[indice]

        if carta["tipo"] == "texto":

            boton.setText(carta["nombre"])
            boton.setIcon(QIcon())

            boton.setStyleSheet("""

                QPushButton {
                    background-color: #FFFFFF;
                    color: #2457A7;
                    border: 3px solid #2457A7;
                    border-radius: 15px;
                    font-size: 14px;
                    font-weight: bold;
                }

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

            boton.setStyleSheet("""

                QPushButton {
                    background-color: #FFFFFF;
                    border: 3px solid #2457A7;
                    border-radius: 15px;
                }

            """)

    # ======================================================
    # OCULTAR CARTA
    # ======================================================

    def ocultar_carta(self, indice):

        boton = self.botones[indice]

        boton.setText("?")
        boton.setIcon(QIcon())

        boton.setStyleSheet("""

            QPushButton {
                background-color: #34495E;
                color: white;
                border: 3px solid #263747;
                border-radius: 15px;
                font-size: 18px;
                font-weight: bold;
            }

        """)

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

            self.parejas_encontradas.extend(self.seleccionadas)
            self.parejas += 1

            for indice in self.seleccionadas:

                self.botones[indice].setStyleSheet("""

                    QPushButton {
                        background-color: #C9F2D4;
                        color: #176B35;
                        border: 3px solid #37A45B;
                        border-radius: 15px;
                    }

                """)

                self.botones[indice].setEnabled(False)

            self.seleccionadas = []
            self.actualizar_informacion()

            if self.parejas == len(self.imagenes_juego):
                self.finalizar_juego()

        else:

            self.mensaje.setText("No coinciden. ¡Inténtalo otra vez!")

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

        self.mensaje.setText("¡Continúa buscando las parejas!")

    # ======================================================
    # ACTUALIZAR INFORMACIÓN
    # ======================================================

    def actualizar_informacion(self):

        self.label_intentos.setText(f"Intentos: {self.intentos}")
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
            "Juego terminado",
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