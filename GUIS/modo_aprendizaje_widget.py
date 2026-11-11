
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QSplitter,
    QMessageBox,
    QFrame,
)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

# La carpeta GUIS está dentro de GESTOVISION.
# Por eso, parent.parent apunta a la raíz del proyecto.
BASE_DIR = Path(__file__).resolve().parent.parent

IMAGE_DIR = BASE_DIR / "imagenes_aprendizaje"

EXTENSIONES_IMAGEN = {
    ".jpg",
    ".jpeg",
    ".png",
}


# ==========================================================
# WIDGET PRINCIPAL
# ==========================================================

class ModoAprendizajeWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.imagen_actual = None
        self.pixmap_original = None

        self.crear_interfaz()
        self.cargar_lista()

    # ------------------------------------------------------
    # CREAR INTERFAZ
    # ------------------------------------------------------

    def crear_interfaz(self):

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(12)

        # Título
        titulo = QLabel("Modo aprendizaje")
        titulo.setObjectName("tituloAprendizaje")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                color: #f1f5f9;
                padding-bottom: 4px;
            }
        """)

        descripcion = QLabel(
            "Busca una seña y consulta su imagen de referencia."
        )
        descripcion.setStyleSheet("""
            QLabel {
                color: #aeb8c7;
                font-size: 13px;
            }
        """)

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(descripcion)

        # --------------------------------------------------
        # BÚSQUEDA
        # --------------------------------------------------

        layout_busqueda = QHBoxLayout()
        layout_busqueda.setSpacing(8)

        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText(
            "Escribe el nombre de una seña..."
        )
        self.campo_busqueda.setClearButtonEnabled(True)
        self.campo_busqueda.textChanged.connect(
            self.buscar_en_lista
        )
        self.campo_busqueda.returnPressed.connect(
            self.buscar_y_mostrar
        )

        self.boton_buscar = QPushButton("Buscar")
        self.boton_buscar.clicked.connect(
            self.buscar_y_mostrar
        )

        self.boton_actualizar = QPushButton("Actualizar lista")
        self.boton_actualizar.clicked.connect(
            self.actualizar_lista
        )

        layout_busqueda.addWidget(self.campo_busqueda, 1)
        layout_busqueda.addWidget(self.boton_buscar)
        layout_busqueda.addWidget(self.boton_actualizar)

        layout_principal.addLayout(layout_busqueda)

        # --------------------------------------------------
        # PANEL CENTRAL
        # --------------------------------------------------

        separador = QSplitter(Qt.Orientation.Horizontal)
        separador.setChildrenCollapsible(False)

        # Lista de señas
        panel_lista = QFrame()
        panel_lista.setObjectName("panelLista")

        layout_lista = QVBoxLayout(panel_lista)
        layout_lista.setContentsMargins(10, 10, 10, 10)
        layout_lista.setSpacing(8)

        etiqueta_lista = QLabel("Señas disponibles")
        etiqueta_lista.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #e2e8f0;
            }
        """)

        self.lista_senas = QListWidget()
        self.lista_senas.currentItemChanged.connect(
            self.seleccionar_de_lista
        )

        layout_lista.addWidget(etiqueta_lista)
        layout_lista.addWidget(self.lista_senas)

        # Visor de imagen
        panel_imagen = QFrame()
        panel_imagen.setObjectName("panelImagen")

        layout_imagen = QVBoxLayout(panel_imagen)
        layout_imagen.setContentsMargins(12, 12, 12, 12)
        layout_imagen.setSpacing(8)

        self.etiqueta_nombre = QLabel("Selecciona una seña")
        self.etiqueta_nombre.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.etiqueta_nombre.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #e2e8f0;
            }
        """)

        self.vista_imagen = QLabel(
            "Aquí aparecerá la imagen de referencia"
        )
        self.vista_imagen.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.vista_imagen.setMinimumSize(250, 250)
        self.vista_imagen.setWordWrap(True)
        self.vista_imagen.setStyleSheet("""
            QLabel {
                background-color: #111827;
                color: #94a3b8;
                border: 1px dashed #475569;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        self.etiqueta_estado = QLabel("")
        self.etiqueta_estado.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.etiqueta_estado.setWordWrap(True)
        self.etiqueta_estado.setStyleSheet("""
            QLabel {
                color: #aeb8c7;
                font-size: 12px;
            }
        """)

        layout_imagen.addWidget(self.etiqueta_nombre)
        layout_imagen.addWidget(self.vista_imagen, 1)
        layout_imagen.addWidget(self.etiqueta_estado)

        separador.addWidget(panel_lista)
        separador.addWidget(panel_imagen)
        separador.setSizes([250, 600])

        layout_principal.addWidget(separador, 1)

        # --------------------------------------------------
        # ESTILOS GENERALES
        # --------------------------------------------------

        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e2e;
                color: #e2e8f0;
                font-family: "Sans Serif";
                font-size: 13px;
            }

            QFrame#panelLista,
            QFrame#panelImagen {
                background-color: #252638;
                border: 1px solid #383a50;
                border-radius: 10px;
            }

            QLineEdit {
                background-color: #111827;
                color: #f1f5f9;
                border: 1px solid #475569;
                border-radius: 6px;
                padding: 9px;
                selection-background-color: #6366f1;
            }

            QPushButton {
                background-color: #4f46e5;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 12px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #6366f1;
            }

            QPushButton:pressed {
                background-color: #4338ca;
            }

            QListWidget {
                background-color: #111827;
                color: #e2e8f0;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }

            QListWidget::item {
                padding: 9px;
                border-radius: 4px;
            }

            QListWidget::item:selected {
                background-color: #4f46e5;
                color: white;
            }

            QListWidget::item:hover {
                background-color: #34364c;
            }
        """)

    # ------------------------------------------------------
    # OBTENER IMÁGENES
    # ------------------------------------------------------

    def obtener_imagenes(self):

        if not IMAGE_DIR.exists():
            return []

        imagenes = [
            archivo
            for archivo in IMAGE_DIR.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower() in EXTENSIONES_IMAGEN
        ]

        return sorted(
            imagenes,
            key=lambda archivo: archivo.stem.lower()
        )

    # ------------------------------------------------------
    # CARGAR LISTA
    # ------------------------------------------------------

    def cargar_lista(self, conservar_seleccion=False):

        nombre_anterior = None

        if conservar_seleccion:
            elemento = self.lista_senas.currentItem()
            if elemento:
                nombre_anterior = elemento.text()

        self.lista_senas.blockSignals(True)
        self.lista_senas.clear()

        imagenes = self.obtener_imagenes()

        for archivo in imagenes:
            self.lista_senas.addItem(archivo.stem)

        self.lista_senas.blockSignals(False)

        if not IMAGE_DIR.exists():
            self.etiqueta_estado.setText(
                f"No existe la carpeta:\n{IMAGE_DIR}"
            )
            self.vista_imagen.setPixmap(QPixmap())
            self.vista_imagen.setText(
                "No se encontró la carpeta de imágenes."
            )
            self.etiqueta_nombre.setText("Sin imágenes")
            return

        if not imagenes:
            self.etiqueta_estado.setText(
                "Agrega imágenes JPG, JPEG o PNG a la carpeta."
            )
            self.vista_imagen.setPixmap(QPixmap())
            self.vista_imagen.setText(
                "No hay imágenes disponibles."
            )
            self.etiqueta_nombre.setText("Sin imágenes")
            return

        self.etiqueta_estado.setText(
            f"{len(imagenes)} imagen(es) disponibles."
        )

        if nombre_anterior:
            coincidencias = self.lista_senas.findItems(
                nombre_anterior,
                Qt.MatchFlag.MatchExactly
            )
            if coincidencias:
                self.lista_senas.setCurrentItem(coincidencias[0])

    # ------------------------------------------------------
    # ACTUALIZAR LISTA
    # ------------------------------------------------------

    def actualizar_lista(self):

        self.cargar_lista(conservar_seleccion=True)

        elemento = self.lista_senas.currentItem()

        if elemento:
            self.mostrar_imagen(elemento.text())

    # ------------------------------------------------------
    # FILTRAR LISTA MIENTRAS SE ESCRIBE
    # ------------------------------------------------------

    def buscar_en_lista(self, texto):

        texto = texto.strip().casefold()

        for indice in range(self.lista_senas.count()):

            elemento = self.lista_senas.item(indice)

            coincide = texto in elemento.text().casefold()

            elemento.setHidden(not coincide)

    # ------------------------------------------------------
    # BUSCAR Y MOSTRAR
    # ------------------------------------------------------

    def buscar_y_mostrar(self):

        texto = self.campo_busqueda.text().strip().casefold()

        if not texto:
            self.etiqueta_estado.setText(
                "Escribe el nombre de una seña para buscarla."
            )
            self.campo_busqueda.setFocus()
            return

        # Primero intenta encontrar una coincidencia exacta.
        for indice in range(self.lista_senas.count()):

            elemento = self.lista_senas.item(indice)

            if elemento.text().casefold() == texto:
                elemento.setHidden(False)
                self.lista_senas.setCurrentItem(elemento)
                self.mostrar_imagen(elemento.text())
                return

        # Si no hay coincidencia exacta, intenta una parcial.
        for indice in range(self.lista_senas.count()):

            elemento = self.lista_senas.item(indice)

            if texto in elemento.text().casefold():
                elemento.setHidden(False)
                self.lista_senas.setCurrentItem(elemento)
                self.mostrar_imagen(elemento.text())
                return

        self.etiqueta_estado.setText(
            f"No se encontró ninguna imagen para: "
            f"{self.campo_busqueda.text().strip()}"
        )

    # ------------------------------------------------------
    # SELECCIONAR SEÑA DE LA LISTA
    # ------------------------------------------------------

    def seleccionar_de_lista(self, elemento_actual, elemento_anterior):

        if elemento_actual is None:
            return

        self.mostrar_imagen(elemento_actual.text())

    # ------------------------------------------------------
    # MOSTRAR IMAGEN
    # ------------------------------------------------------

    def mostrar_imagen(self, nombre):

        # Busca el archivo ignorando mayúsculas y minúsculas.
        archivo_encontrado = None

        for archivo in self.obtener_imagenes():
            if archivo.stem.casefold() == nombre.casefold():
                archivo_encontrado = archivo
                break

        if archivo_encontrado is None:
            self.etiqueta_estado.setText(
                f"No se encontró el archivo de imagen: {nombre}"
            )
            return

        pixmap = QPixmap(str(archivo_encontrado))

        if pixmap.isNull():
            self.etiqueta_estado.setText(
                "No se pudo cargar la imagen."
            )
            return

        self.imagen_actual = archivo_encontrado
        self.pixmap_original = pixmap

        self.etiqueta_nombre.setText(archivo_encontrado.stem)
        self.etiqueta_estado.setText(
            f"Archivo: {archivo_encontrado.name} | "
            f"{pixmap.width()} × {pixmap.height()} px"
        )

        self.ajustar_imagen()

    # ------------------------------------------------------
    # AJUSTAR IMAGEN AL TAMAÑO DEL PANEL
    # ------------------------------------------------------

    def ajustar_imagen(self):

        if self.pixmap_original is None:
            return

        tamano = self.vista_imagen.size()

        pixmap_escalado = self.pixmap_original.scaled(
            tamano,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        self.vista_imagen.setText("")
        self.vista_imagen.setPixmap(pixmap_escalado)

    # ------------------------------------------------------
    # REDIMENSIONAR IMAGEN CUANDO CAMBIA LA VENTANA
    # ------------------------------------------------------

    def resizeEvent(self, evento):

        super().resizeEvent(evento)
        self.ajustar_imagen()


# ==========================================================
# EJECUCIÓN INDIVIDUAL PARA HACER PRUEBAS
# ==========================================================

if __name__ == "__main__":

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = ModoAprendizajeWidget()
    ventana.resize(1000, 650)
    ventana.setWindowTitle("Modo aprendizaje")

    ventana.show()

    sys.exit(app.exec())
