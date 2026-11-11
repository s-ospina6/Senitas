
import sys
from pathlib import Path

# ==========================================================
# RUTA DEL PROYECTO
# ==========================================================

RUTA_PROYECTO = Path(__file__).resolve().parent.parent

if str(RUTA_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RUTA_PROYECTO))


# ==========================================================
# IMPORTACIONES
# ==========================================================

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
    QHBoxLayout,
    QFrame,
)

from PySide6.QtGui import QGuiApplication
from PySide6.QtCore import Qt

from juego1 import JuegoMemoria, IMAGE_DIR, EXTENSIONS


# ==========================================================
# PALETA GESTOSVISION
# ==========================================================

MORADO = "#6C4DC4"
MORADO_OSCURO = "#5B3A9E"

NARANJA = "#F7941D"
NARANJA_OSCURO = "#D97706"

ROSA = "#F0527A"
ROSA_OSCURO = "#C93660"

CREMA = "#FFF3DD"
NAVY = "#2B3A67"
BLANCO = "#FFFFFF"

LAVANDA = "#E8DFFF"
SECUNDARIO = "#7A6A99"
BORDE = "#FFE0B2"


# ==========================================================
# WIDGET REUTILIZABLE DEL JUEGO
# ==========================================================

class WidgetJuegoMemoria(QWidget):

    """
    Contenedor del juego de memoria.

    Se puede integrar dentro de la interfaz principal
    y conserva la lógica de JuegoMemoria.
    """

    def __init__(self, parent=None, verificar_imagenes=True):

        super().__init__(parent)

        self.setWindowTitle("GESTOSVISION - Juego de memoria")

        pantalla = QGuiApplication.primaryScreen().availableGeometry()

        ancho = min(950, pantalla.width() - 60)
        alto = min(780, pantalla.height() - 60)

        self.resize(ancho, alto)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(0)

        self.juego = None
        self._contenedor_aviso = None

        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                color: {NAVY};
                font-family: "Comic Sans MS", "Verdana";
            }}
        """)

        if verificar_imagenes and not self._hay_imagenes():

            self._mostrar_aviso_sin_imagenes()
            return

        self._crear_juego()

    # ======================================================
    # CONSTRUCCIÓN DEL JUEGO
    # ======================================================

    def _crear_juego(self):

        if self.juego is not None:
            self.liberar()

        self.juego = JuegoMemoria()

        # Quitar barra de menú si existe

        if hasattr(self.juego, "setMenuBar"):
            self.juego.setMenuBar(None)

        # Obtener el contenido central del juego

        central = self.juego.centralWidget()

        if central is None:
            return

        central.setParent(self)

        central.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
        """)

        self._layout.addWidget(central)

        # No se conecta ningún botón Salir.
        # El usuario cambia de actividad desde el menú principal.

        self._conectar_botones()

    # ======================================================
    # CONECTAR BOTONES
    # ======================================================

    def _conectar_botones(self):

        # El juego ya no tiene botón Salir.
        # El botón Nuevo juego funciona directamente
        # desde la clase JuegoMemoria.

        pass

    # ======================================================
    # AVISO SIN IMÁGENES
    # ======================================================

    def _mostrar_aviso_sin_imagenes(self):

        contenedor = QFrame()
        contenedor.setObjectName("avisoImagenes")

        layout = QVBoxLayout(contenedor)

        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icono

        icono = QLabel("🧩")
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icono.setStyleSheet("""
            QLabel {
                font-size: 55px;
                background: transparent;
                border: none;
            }
        """)

        # Título

        titulo = QLabel("¡Ups! No encontramos imágenes")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setWordWrap(True)

        titulo.setStyleSheet(f"""
            QLabel {{
                color: {NAVY};
                font-family: "Comic Sans MS", "Verdana";
                font-size: 22px;
                font-weight: 900;
                background: transparent;
                border: none;
            }}
        """)

        # Descripción

        detalle = QLabel(
            "Para jugar necesitas al menos 2 imágenes.\n\n"
            "Agrega archivos JPG, JPEG o PNG en la carpeta:"
        )

        detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detalle.setWordWrap(True)

        detalle.setStyleSheet(f"""
            QLabel {{
                color: {SECUNDARIO};
                font-family: "Comic Sans MS", "Verdana";
                font-size: 13px;
                background: transparent;
                border: none;
            }}
        """)

        # Ruta

        ruta = QLabel(str(IMAGE_DIR))

        ruta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta.setWordWrap(True)

        ruta.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        ruta.setStyleSheet(f"""
            QLabel {{
                color: {MORADO};
                background-color: {LAVANDA};
                border-radius: 12px;
                padding: 12px;
                font-size: 11px;
                font-weight: bold;
                border: none;
            }}
        """)

        # Botones

        fila_botones = QHBoxLayout()
        fila_botones.setSpacing(12)

        boton_abrir = QPushButton("📁  Abrir carpeta")

        boton_abrir.setMinimumHeight(46)
        boton_abrir.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        boton_abrir.clicked.connect(
            self._abrir_carpeta_imagenes
        )

        boton_reintentar = QPushButton("↻  Reintentar")

        boton_reintentar.setObjectName("principal")
        boton_reintentar.setMinimumHeight(46)

        boton_reintentar.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        boton_reintentar.clicked.connect(
            self._reintentar
        )

        fila_botones.addWidget(boton_abrir)
        fila_botones.addWidget(boton_reintentar)

        # Añadir elementos

        layout.addWidget(icono)
        layout.addWidget(titulo)
        layout.addWidget(detalle)
        layout.addWidget(ruta)
        layout.addSpacing(8)
        layout.addLayout(fila_botones)

        self._contenedor_aviso = contenedor

        self._layout.addWidget(contenedor)

        # Estilos del aviso

        contenedor.setStyleSheet(f"""
            QFrame#avisoImagenes {{
                background-color: {BLANCO};
                border: 3px solid {BORDE};
                border-bottom: 6px solid {NARANJA};
                border-radius: 28px;
            }}

            QPushButton {{
                background-color: {LAVANDA};
                color: {NAVY};
                border: 2px solid {MORADO};
                border-bottom: 5px solid {MORADO_OSCURO};
                border-radius: 15px;
                padding: 9px 16px;
                font-family: "Comic Sans MS", "Verdana";
                font-size: 12px;
                font-weight: 900;
            }}

            QPushButton:hover:enabled {{
                background-color: #D8C9FF;
            }}

            QPushButton:pressed:enabled {{
                background-color: #C7B5F5;
                border-bottom: 2px solid {MORADO_OSCURO};
            }}

            QPushButton#principal {{
                background-color: {ROSA};
                color: {BLANCO};
                border: 2px solid {ROSA};
                border-bottom: 5px solid {ROSA_OSCURO};
            }}

            QPushButton#principal:hover:enabled {{
                background-color: #FF7094;
            }}

            QPushButton#principal:pressed:enabled {{
                background-color: {ROSA_OSCURO};
                border-bottom: 2px solid {ROSA_OSCURO};
            }}
        """)

    # ======================================================
    # ABRIR CARPETA DE IMÁGENES
    # ======================================================

    def _abrir_carpeta_imagenes(self):

        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        IMAGE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        QDesktopServices.openUrl(
            QUrl.fromLocalFile(str(IMAGE_DIR))
        )

    # ======================================================
    # REINTENTAR
    # ======================================================

    def _reintentar(self):

        if self._hay_imagenes():

            if self._contenedor_aviso is not None:

                self._contenedor_aviso.setParent(None)
                self._contenedor_aviso.deleteLater()

                self._contenedor_aviso = None

            self._crear_juego()

        else:

            QMessageBox.warning(
                self,
                "Sin imágenes",
                f"Sigue sin haber imágenes en:\n{IMAGE_DIR}",
            )

    # ======================================================
    # SALIR INTERNO
    # ======================================================

    def _salir(self):

        # Se conserva este método por compatibilidad,
        # pero no existe un botón Salir en el juego.

        self.liberar()
        self.close()

    # ======================================================
    # CIERRE DEL JUEGO INTERNO
    # ======================================================

    def _al_cerrar_juego(self, evento):

        self.liberar()

        if evento is not None:
            evento.accept()

    # ======================================================
    # UTILIDADES
    # ======================================================

    def _hay_imagenes(self):

        IMAGE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:

            archivos = [
                archivo
                for archivo in IMAGE_DIR.iterdir()
                if archivo.is_file()
                and archivo.suffix.lower() in EXTENSIONS
            ]

        except OSError:

            return False

        return len(archivos) >= 2

    # ======================================================
    # API PÚBLICA
    # ======================================================

    def reiniciar(self):

        if self.juego is not None:
            self.juego.nuevo_juego()

    def pausar(self):

        if self.juego is not None:
            self.juego.temporizador.stop()

    def liberar(self):

        if self.juego is not None:

            self.juego.temporizador.stop()

            self.juego.close()
            self.juego = None

    # ======================================================
    # LIMPIEZA
    # ======================================================

    def closeEvent(self, event):

        self.liberar()

        super().closeEvent(event)


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():

    app = QApplication(sys.argv)

    widget = WidgetJuegoMemoria()
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":

    main()
