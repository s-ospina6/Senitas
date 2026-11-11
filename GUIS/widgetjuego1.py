# widgetjuego1.py
import sys
from pathlib import Path

# ----------------------------------------------------------
# Añadir la carpeta raíz del proyecto (GESTOSVISION) al sys.path
# para poder importar juego1.py aunque el widget esté en GUIS/
# ----------------------------------------------------------
RUTA_PROYECTO = Path(__file__).resolve().parent.parent  # .../GESTOSVISION
if str(RUTA_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RUTA_PROYECTO))

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QMessageBox,
)

from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtCore import Qt

# Ahora sí se puede importar juego1 desde la carpeta padre
from juego1 import JuegoMemoria, IMAGE_DIR, EXTENSIONS


# ==========================================================
# WIDGET REUTILIZABLE DEL JUEGO
# ==========================================================

class WidgetJuegoMemoria(QWidget):
    """
    Contenedor del juego de memoria.

    - Si se instancia solo, funciona como ventana independiente.
    - Si se incrusta en otro widget (QStackedWidget, QTabWidget, etc.),
      reutiliza el widget central de JuegoMemoria y se adapta al espacio.
    """

    def __init__(self, parent=None, verificar_imagenes=True):

        super().__init__(parent)

        self.setWindowTitle("GESTOSVISION - Juego de memoria")

        # Tamaño acotado a la pantalla disponible
        pantalla = QGuiApplication.primaryScreen().availableGeometry()
        ancho = min(950, pantalla.width() - 60)
        alto = min(780, pantalla.height() - 60)
        self.resize(ancho, alto)

        # Layout raíz (sin márgenes para que el juego ocupe todo)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self.juego = None

        # Verificar imágenes antes de crear el juego
        if verificar_imagenes and not self._hay_imagenes():
            self._mostrar_aviso_sin_imagenes()
            return

        # Crear el juego interno
        self._crear_juego()

    # ======================================================
    # CONSTRUCCIÓN
    # ======================================================

    def _crear_juego(self):
        """Crea JuegoMemoria y extrae su widget central."""

        self.juego = JuegoMemoria()

        # Quitar la barra de estado/menú por si acaso (no hay, pero por seguridad)
        self.juego.setMenuBar(None) if hasattr(self.juego, "setMenuBar") else None

        # Extraer el widget central del QMainWindow y reubicarlo aquí
        central = self.juego.centralWidget()
        central.setParent(self)
        self._layout.addWidget(central)

        # Si el juego interno se cierra, cerramos también el contenedor
        self.juego.closeEvent = self._al_cerrar_juego

        # Interceptar "Nuevo juego"/"Salir" para que se comporten bien dentro del widget
        self._conectar_botones()

    def _conectar_botones(self):
        """Redirige los botones del juego a acciones del contenedor."""
        if self.juego is None:
            return

        # "Salir" debe cerrar el widget contenedor, no solo el QMainWindow interno
        try:
            self.juego.boton_salir.clicked.disconnect()
        except (RuntimeError, TypeError):
            pass
        self.juego.boton_salir.clicked.connect(self._salir)

        # "Nuevo juego" ya apunta a nuevo_juego(); no requiere cambios.

    def _mostrar_aviso_sin_imagenes(self):
        """Muestra un mensaje claro si no hay imágenes."""

        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        titulo = QLabel("No se encontraron imágenes")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))

        detalle = QLabel(
            "Agrega al menos 2 imágenes (.jpg, .jpeg, .png)\n"
            f"en la carpeta:\n{IMAGE_DIR}"
        )
        detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detalle.setFont(QFont("Arial", 11))
        detalle.setWordWrap(True)

        boton_abrir = QPushButton("Abrir carpeta")
        boton_abrir.clicked.connect(self._abrir_carpeta_imagenes)

        boton_reintentar = QPushButton("Reintentar")
        boton_reintentar.clicked.connect(self._reintentar)

        layout.addWidget(titulo)
        layout.addWidget(detalle)
        layout.addWidget(boton_abrir)
        layout.addWidget(boton_reintentar)

        self._contenedor_aviso = contenedor
        self._layout.addWidget(contenedor)

    # ======================================================
    # ACCIONES
    # ======================================================

    def _abrir_carpeta_imagenes(self):
        """Abre la carpeta de imágenes en el explorador del sistema."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl

        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(IMAGE_DIR)))

    def _reintentar(self):
        """Reintenta cargar imágenes y reconstruye el juego."""
        if self._hay_imagenes():
            # Eliminar aviso
            if hasattr(self, "_contenedor_aviso"):
                self._contenedor_aviso.setParent(None)
                self._contenedor_aviso.deleteLater()
                del self._contenedor_aviso
            self._crear_juego()
        else:
            QMessageBox.warning(
                self,
                "Sin imágenes",
                f"Sigue sin haber imágenes en:\n{IMAGE_DIR}"
            )

    def _salir(self):
        """Cierra el widget contenedor (y el juego interno si existe)."""
        if self.juego is not None:
            self.juego.temporizador.stop()
            self.juego.close()
        self.close()

    def _al_cerrar_juego(self, evento):
        """Cuando el QMainWindow interno se cierra, cerramos el contenedor."""
        self.juego.temporizador.stop()
        # Evita reentrada: desconecta el hook
        self.juego.closeEvent = lambda e: None
        self.close()

    # ======================================================
    # UTILIDADES
    # ======================================================

    def _hay_imagenes(self):
        """Comprueba si hay al menos 2 imágenes válidas."""
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)
        try:
            archivos = [
                a for a in IMAGE_DIR.iterdir()
                if a.is_file() and a.suffix.lower() in EXTENSIONS
            ]
        except OSError:
            return False
        return len(archivos) >= 2

    # ======================================================
    # API PÚBLICA
    # ======================================================

    def reiniciar(self):
        """Reinicia el juego desde el contenedor."""
        if self.juego is not None:
            self.juego.nuevo_juego()

    def pausar(self):
        """Detiene el temporizador (útil al cambiar de vista)."""
        if self.juego is not None:
            self.juego.temporizador.stop()

    def liberar(self):
        """Libera recursos del juego (llámalo antes de destruir el widget)."""
        if self.juego is not None:
            self.juego.temporizador.stop()
            self.juego.close()
            self.juego = None


# ==========================================================
# PROGRAMA PRINCIPAL (para probar el widget solo)
# ==========================================================

def main():

    app = QApplication(sys.argv)

    widget = WidgetJuegoMemoria()
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()