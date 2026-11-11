
import random
import sys
from collections import deque
from pathlib import Path

import cv2
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
    QSizePolicy,
)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_DIR = BASE_DIR / "modelos"
MODEL_FILE = MODEL_DIR / "gestos_lstm.keras"
LABELS_FILE = MODEL_DIR / "gestos_lstm_labels.npz"

SEQUENCE_LENGTH = 30
FEATURE_COUNT = 126
MIN_FRAMES = 8
DELAY_FRAMES = 5
CONFIDENCE_THRESHOLD = 0.6


# ==========================================================
# WIDGET
# ==========================================================

class ModoPracticaWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Recursos del reconocimiento
        self.classifier = None
        self.class_names = []
        self.camera = None
        self.holistic = None

        # Estado de la práctica
        self.target = None
        self.phase = "inactivo"

        self.sequence = []
        self.total_frames = 0
        self.empty_frames = 0

        self.last_prediction = ""
        self.confidence = 0.0

        self.correct = 0
        self.incorrect = 0
        self.attempts = 0

        self.result_text = ""
        self.result_color = (255, 255, 255)

        self.history = deque(maxlen=6)

        # Timer de cámara
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._procesar_frame)

        # Crear interfaz
        self.crear_interfaz()

    # ======================================================
    # INTERFAZ
    # ======================================================

    def crear_interfaz(self):

        # --------------------------------------------------
        # PALETA GESTOSVISION
        # --------------------------------------------------

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

        # --------------------------------------------------
        # CONTENEDOR PRINCIPAL
        # --------------------------------------------------

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(18, 18, 18, 18)
        layout_principal.setSpacing(12)

        # --------------------------------------------------
        # TÍTULO Y DESCRIPCIÓN
        # --------------------------------------------------

        titulo = QLabel("🎯  Modo práctica")
        titulo.setStyleSheet(f"""
            QLabel {{
                font-family: "Comic Sans MS", "Verdana";
                font-size: 23px;
                font-weight: 900;
                color: {NAVY};
                background: transparent;
            }}
        """)

        descripcion = QLabel(
            "Realiza la seña indicada y comprueba si el modelo "
            "la reconoce correctamente."
        )
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet(f"""
            QLabel {{
                color: {SECUNDARIO};
                font-family: "Comic Sans MS", "Verdana";
                font-size: 13px;
                background: transparent;
            }}
        """)

        layout_principal.addWidget(titulo)
        layout_principal.addWidget(descripcion)

        # --------------------------------------------------
        # PANEL CENTRAL
        # --------------------------------------------------

        central = QHBoxLayout()
        central.setSpacing(14)

        # --------------------------------------------------
        # VISOR DE CÁMARA
        # --------------------------------------------------

        panel_camara = QFrame()
        panel_camara.setObjectName("panelCamara")

        layout_camara = QVBoxLayout(panel_camara)
        layout_camara.setContentsMargins(10, 10, 10, 10)
        layout_camara.setSpacing(8)

        etiqueta_camara = QLabel("📷  TU CÁMARA")
        etiqueta_camara.setStyleSheet(f"""
            QLabel {{
                color: {MORADO};
                font-family: "Comic Sans MS", "Verdana";
                font-size: 12px;
                font-weight: 900;
                background: transparent;
                padding: 3px;
            }}
        """)

        self.vista_camara = QLabel(
            "Pulsa «Iniciar práctica» para abrir la cámara."
        )

        self.vista_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vista_camara.setMinimumSize(400, 300)

        self.vista_camara.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self.vista_camara.setStyleSheet(f"""
            QLabel {{
                background-color: #FFF9EF;
                color: {SECUNDARIO};
                border: 3px dashed {NARANJA};
                border-radius: 22px;
                padding: 12px;
                font-family: "Comic Sans MS", "Verdana";
                font-size: 14px;
                font-weight: bold;
            }}
        """)

        layout_camara.addWidget(etiqueta_camara)
        layout_camara.addWidget(self.vista_camara, 1)

        # --------------------------------------------------
        # PANEL LATERAL DE INFORMACIÓN
        # --------------------------------------------------

        panel_info = QFrame()
        panel_info.setObjectName("panelInfo")
        panel_info.setFixedWidth(260)

        layout_info = QVBoxLayout(panel_info)
        layout_info.setContentsMargins(16, 16, 16, 16)
        layout_info.setSpacing(9)

        # Objetivo

        etiqueta_obj = QLabel("🎯  OBJETIVO")
        etiqueta_obj.setStyleSheet(f"""
            QLabel {{
                color: {MORADO};
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
            }}
        """)

        self.lbl_objetivo = QLabel("—")
        self.lbl_objetivo.setWordWrap(True)
        self.lbl_objetivo.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.lbl_objetivo.setStyleSheet(f"""
            QLabel {{
                color: {NARANJA_OSCURO};
                background-color: {CREMA};
                border: 2px solid {NARANJA};
                border-radius: 16px;
                padding: 12px 8px;
                font-family: "Comic Sans MS", "Verdana";
                font-size: 25px;
                font-weight: 900;
            }}
        """)

        # Estado

        etiqueta_estado = QLabel("✨  ESTADO")
        etiqueta_estado.setStyleSheet(f"""
            QLabel {{
                color: {MORADO};
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
            }}
        """)

        self.lbl_estado = QLabel("Listo para empezar")
        self.lbl_estado.setWordWrap(True)
        self.lbl_estado.setStyleSheet(f"""
            QLabel {{
                color: {NAVY};
                background-color: {LAVANDA};
                border-radius: 12px;
                padding: 10px;
                font-size: 14px;
                font-weight: 900;
            }}
        """)

        self.lbl_prediccion = QLabel("")
        self.lbl_prediccion.setWordWrap(True)
        self.lbl_prediccion.setStyleSheet(f"""
            QLabel {{
                color: {SECUNDARIO};
                font-size: 12px;
                background: transparent;
                padding: 3px;
            }}
        """)

        # Separador

        separador1 = QFrame()
        separador1.setFrameShape(QFrame.Shape.HLine)
        separador1.setStyleSheet(f"""
            background-color: {BORDE};
            max-height: 2px;
            border: none;
        """)

        # Marcador

        etiqueta_marcador = QLabel("🏆  MARCADOR")
        etiqueta_marcador.setStyleSheet(f"""
            QLabel {{
                color: {MORADO};
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
            }}
        """)

        self.lbl_marcador = QLabel(
            "Aciertos: 0\n"
            "Errores: 0\n"
            "Efectividad: 0.0%"
        )

        self.lbl_marcador.setStyleSheet(f"""
            QLabel {{
                color: {NAVY};
                background-color: #FFF9EF;
                border: 2px solid {BORDE};
                border-radius: 14px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
                line-height: 1.5;
            }}
        """)

        # Historial

        etiqueta_historial = QLabel("📋  HISTORIAL")
        etiqueta_historial.setStyleSheet(f"""
            QLabel {{
                color: {MORADO};
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 1px;
                background: transparent;
            }}
        """)

        self.lbl_historial = QLabel("—")
        self.lbl_historial.setWordWrap(True)
        self.lbl_historial.setStyleSheet(f"""
            QLabel {{
                color: {SECUNDARIO};
                background-color: {LAVANDA};
                border-radius: 12px;
                padding: 10px;
                font-size: 12px;
                font-weight: bold;
            }}
        """)

        layout_info.addWidget(etiqueta_obj)
        layout_info.addWidget(self.lbl_objetivo)

        layout_info.addWidget(etiqueta_estado)
        layout_info.addWidget(self.lbl_estado)
        layout_info.addWidget(self.lbl_prediccion)

        layout_info.addWidget(separador1)

        layout_info.addWidget(etiqueta_marcador)
        layout_info.addWidget(self.lbl_marcador)

        layout_info.addWidget(etiqueta_historial)
        layout_info.addWidget(self.lbl_historial)

        layout_info.addStretch()

        central.addWidget(panel_camara, 1)
        central.addWidget(panel_info)

        layout_principal.addLayout(central, 1)

        # --------------------------------------------------
        # BOTONES
        # --------------------------------------------------

        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(9)

        self.boton_iniciar = QPushButton("▶  Iniciar práctica")
        self.boton_iniciar.setObjectName("principal")
        self.boton_iniciar.setMinimumHeight(46)
        self.boton_iniciar.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.boton_iniciar.clicked.connect(
            self.iniciar_practica
        )

        self.boton_repetir = QPushButton("↻  Repetir (R)")
        self.boton_repetir.setMinimumHeight(46)
        self.boton_repetir.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.boton_repetir.setEnabled(False)
        self.boton_repetir.clicked.connect(
            self.repetir_sena
        )

        self.boton_siguiente = QPushButton("→  Siguiente")
        self.boton_siguiente.setMinimumHeight(46)
        self.boton_siguiente.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.boton_siguiente.setEnabled(False)
        self.boton_siguiente.clicked.connect(
            self.siguiente_sena
        )

        self.boton_detener = QPushButton("■  Detener")
        self.boton_detener.setObjectName("detener")
        self.boton_detener.setMinimumHeight(46)
        self.boton_detener.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.boton_detener.setEnabled(False)
        self.boton_detener.clicked.connect(
            self.detener_practica
        )

        layout_botones.addWidget(self.boton_iniciar)
        layout_botones.addWidget(self.boton_repetir)
        layout_botones.addWidget(self.boton_siguiente)

        layout_botones.addStretch()

        layout_botones.addWidget(self.boton_detener)

        layout_principal.addLayout(layout_botones)

        # --------------------------------------------------
        # ESTILOS GENERALES
        # --------------------------------------------------

        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                color: {NAVY};
                font-family: "Comic Sans MS", "Verdana";
                font-size: 13px;
            }}

            QFrame#panelCamara,
            QFrame#panelInfo {{
                background-color: {BLANCO};
                border: 3px solid {BORDE};
                border-bottom: 5px solid {NARANJA};
                border-radius: 24px;
            }}

            QPushButton {{
                background-color: {LAVANDA};
                color: {NAVY};
                border: 2px solid {MORADO};
                border-bottom: 5px solid {MORADO_OSCURO};
                border-radius: 15px;
                padding: 9px 12px;
                font-family: "Comic Sans MS", "Verdana";
                font-size: 12px;
                font-weight: 900;
            }}

            QPushButton:hover:enabled {{
                background-color: #D8C9FF;
                border: 2px solid {MORADO_OSCURO};
                border-bottom: 5px solid {MORADO_OSCURO};
            }}

            QPushButton:pressed:enabled {{
                background-color: #C7B5F5;
                border-bottom: 2px solid {MORADO_OSCURO};
                padding-top: 12px;
            }}

            QPushButton:disabled {{
                background-color: #EEEAF4;
                color: #A69AB8;
                border: 2px solid #D8D0E2;
                border-bottom: 4px solid #D8D0E2;
            }}

            QPushButton#principal {{
                background-color: {ROSA};
                color: {BLANCO};
                border: 2px solid {ROSA};
                border-bottom: 5px solid {ROSA_OSCURO};
            }}

            QPushButton#principal:hover:enabled {{
                background-color: #FF7094;
                border-bottom: 5px solid {ROSA_OSCURO};
            }}

            QPushButton#principal:pressed:enabled {{
                background-color: {ROSA_OSCURO};
                border-bottom: 2px solid {ROSA_OSCURO};
            }}

            QPushButton#detener {{
                background-color: {NARANJA};
                color: {BLANCO};
                border: 2px solid {NARANJA};
                border-bottom: 5px solid {NARANJA_OSCURO};
            }}

            QPushButton#detener:hover:enabled {{
                background-color: #FFAA45;
            }}

            QPushButton#detener:pressed:enabled {{
                background-color: {NARANJA_OSCURO};
                border-bottom: 2px solid {NARANJA_OSCURO};
            }}
        """)

    # ======================================================
    # INICIAR PRÁCTICA
    # ======================================================

    def iniciar_practica(self):

        if self.timer.isActive():
            return

        if not self._cargar_modelo():
            return

        if not self._abrir_camara():
            return

        self.correct = 0
        self.incorrect = 0
        self.attempts = 0

        self.history.clear()

        self.target = self._elegir_objetivo()

        self.lbl_objetivo.setText(
            self._formatear(self.target)
        )

        self._actualizar_marcador()
        self._actualizar_historial()

        self.phase = "esperando"

        self.sequence = []
        self.total_frames = 0
        self.empty_frames = 0

        self.last_prediction = ""
        self.confidence = 0.0
        self.result_text = ""

        self.lbl_prediccion.setText("")
        self.lbl_estado.setText("¡Haz la seña indicada!")

        self.boton_iniciar.setEnabled(False)
        self.boton_detener.setEnabled(True)
        self.boton_repetir.setEnabled(True)
        self.boton_siguiente.setEnabled(False)

        self.timer.start()

    # ======================================================
    # CARGAR MODELO
    # ======================================================

    def _cargar_modelo(self):

        if self.classifier is not None and self.class_names:
            return True

        if not MODEL_FILE.exists():
            QMessageBox.warning(
                self,
                "Modelo no encontrado",
                f"No existe el modelo:\n{MODEL_FILE}\n\n"
                "Comprueba que el modelo esté en la carpeta modelos.",
            )
            return False

        if not LABELS_FILE.exists():
            QMessageBox.warning(
                self,
                "Etiquetas no encontradas",
                f"No existe el archivo:\n{LABELS_FILE}",
            )
            return False

        try:
            from tensorflow.keras.models import load_model

            self.classifier = load_model(MODEL_FILE)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error cargando el modelo",
                str(error),
            )
            return False

        try:
            with np.load(LABELS_FILE, allow_pickle=False) as data:
                self.class_names = (
                    data["class_names"].astype(str).tolist()
                )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error cargando etiquetas",
                str(error),
            )
            return False

        if not self.class_names:
            QMessageBox.warning(
                self,
                "Sin clases",
                "El modelo no tiene señas registradas.",
            )
            return False

        return True

    # ======================================================
    # ABRIR CÁMARA
    # ======================================================

    def _abrir_camara(self):

        if self.camera is not None and self.camera.isOpened():
            return True

        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            QMessageBox.critical(
                self,
                "Cámara no disponible",
                "No se pudo abrir la cámara.",
            )

            self.camera = None
            return False

        try:
            self.holistic = self._crear_holistic()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Error de MediaPipe",
                str(error),
            )

            self.camera.release()
            self.camera = None
            self.holistic = None
            return False

        return True

    # ======================================================
    # IMPORTS DIFERIDOS DEL PROYECTO
    # ======================================================

    def _importar_modelo_utils(self):

        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))

        from model import (
            create_holistic,
            extract_features,
            draw_hands,
        )

        return create_holistic, extract_features, draw_hands

    def _crear_holistic(self):

        create_holistic, _, _ = self._importar_modelo_utils()

        return create_holistic()

    # ======================================================
    # PROCESAR FRAME
    # ======================================================

    def _procesar_frame(self):

        if self.camera is None:
            return

        ok, frame = self.camera.read()

        if not ok:
            self.detener_practica()
            return

        frame = cv2.flip(frame, 1)

        try:
            _, extract_features, draw_hands = (
                self._importar_modelo_utils()
            )

            processing = cv2.resize(
                frame,
                (320, 240),
                interpolation=cv2.INTER_AREA,
            )

            rgb = cv2.cvtColor(
                processing,
                cv2.COLOR_BGR2RGB,
            )

            rgb.flags.writeable = False
            results = self.holistic.process(rgb)
            rgb.flags.writeable = True

            left = results.left_hand_landmarks is not None
            right = results.right_hand_landmarks is not None

            any_hand = left or right

            draw_hands(frame, results)

            # Captura del movimiento

            if self.phase in ("esperando", "grabando"):

                if any_hand:

                    self.empty_frames = 0

                    features = np.asarray(
                        extract_features(results),
                        dtype=np.float32,
                    ).reshape(-1)

                    if features.size == FEATURE_COUNT:

                        if self.phase == "esperando":

                            self.phase = "grabando"

                            self.sequence = []
                            self.total_frames = 0

                            self.lbl_estado.setText(
                                "Capturando movimiento..."
                            )

                            self.lbl_prediccion.setText("")

                        self.sequence.append(features)
                        self.total_frames += 1

                elif self.phase == "grabando":

                    self.empty_frames += 1

                    if self.empty_frames >= DELAY_FRAMES:
                        self._evaluar_secuencia()

            self._dibujar_hud(frame)
            self._mostrar_frame(frame)

        except Exception as error:

            self.lbl_estado.setText("Error procesando cámara")
            self.lbl_prediccion.setText(str(error))

            self.detener_practica()

    # ======================================================
    # EVALUAR SECUENCIA
    # ======================================================

    def _evaluar_secuencia(self):

        self.phase = "resultado"

        if self.total_frames < MIN_FRAMES:

            self.last_prediction = ""
            self.confidence = 0.0

            self.result_text = "SEÑA MUY CORTA"
            self.result_color = (0, 165, 255)

            self.lbl_estado.setText("Seña muy corta")

            self.lbl_prediccion.setText(
                "Intenta de nuevo con «Repetir»."
            )

            self.boton_siguiente.setEnabled(True)

            self._reset_secuencia()

            return

        try:

            normalized = self._normalizar_secuencia(
                self.sequence
            )

            prediction = self.classifier.predict(
                np.expand_dims(normalized, axis=0),
                verbose=0,
            )[0]

            index = int(np.argmax(prediction))

            self.confidence = float(prediction[index])

            self.last_prediction = self.class_names[index]

            self.attempts += 1

            reconocida = (
                self.confidence >= CONFIDENCE_THRESHOLD
            )

            if reconocida and self.last_prediction == self.target:

                self.correct += 1

                self.result_text = "CORRECTO"
                self.result_color = (0, 200, 0)

                self.history.append(
                    f"✓  {self._formatear(self.target)}"
                )

                self.lbl_estado.setText("¡Excelente! ¡Correcto!")

            else:

                self.incorrect += 1

                if reconocida:
                    self.result_text = "INCORRECTO"
                else:
                    self.result_text = "NO RECONOCIDA"

                self.result_color = (0, 0, 255)

                self.history.append(
                    f"✗  {self._formatear(self.target)}"
                )

                self.lbl_estado.setText(
                    self.result_text.title()
                )

            self.lbl_prediccion.setText(
                f"Tu seña: {self._formatear(self.last_prediction)}\n"
                f"Confianza: {self.confidence:.1%}"
            )

            self._actualizar_marcador()
            self._actualizar_historial()

        except Exception as error:

            self.last_prediction = ""
            self.confidence = 0.0

            self.result_text = "ERROR AL EVALUAR"
            self.result_color = (0, 0, 255)

            self.lbl_estado.setText("Error al evaluar")
            self.lbl_prediccion.setText(str(error))

        self.boton_siguiente.setEnabled(True)

        self._reset_secuencia()

    def _normalizar_secuencia(
        self,
        frames,
        target_length=SEQUENCE_LENGTH,
    ):

        sequence = np.asarray(
            frames,
            dtype=np.float32,
        )

        indices = np.linspace(
            0,
            len(sequence) - 1,
            target_length,
        ).astype(int)

        return sequence[indices]

    def _reset_secuencia(self):

        self.sequence = []
        self.total_frames = 0
        self.empty_frames = 0

    # ======================================================
    # DIBUJAR INFORMACIÓN SOBRE LA CÁMARA
    # ======================================================

    def _dibujar_hud(self, frame):

        def texto(
            txt,
            y,
            color=(255, 255, 255),
            scale=0.6,
        ):

            cv2.putText(
                frame,
                txt,
                (10, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                scale,
                color,
                2,
                cv2.LINE_AA,
            )

        texto(
            "GESTOSVISION - MODO PRACTICA",
            28,
            (255, 255, 0),
            0.6,
        )

        texto(
            f"OBJETIVO: {self._formatear(self.target) if self.target else '-'}",
            65,
            (0, 255, 255),
            0.8,
        )

        if self.phase == "esperando":

            texto(
                "HAZ LA SENA",
                100,
                (0, 255, 255),
                0.8,
            )

        elif self.phase == "grabando":

            texto(
                f"CAPTURANDO... ({self.total_frames})",
                100,
                (0, 200, 255),
                0.8,
            )

        elif self.phase == "resultado":

            texto(
                self.result_text or "",
                100,
                self.result_color,
                0.8,
            )

        texto(
            f"Aciertos: {self.correct}  Errores: {self.incorrect}",
            135,
            (0, 255, 0),
            0.55,
        )

        accuracy = (
            self.correct / self.attempts * 100
            if self.attempts > 0
            else 0.0
        )

        texto(
            f"Efectividad: {accuracy:.1f}%",
            160,
            (255, 255, 255),
            0.55,
        )

    # ======================================================
    # MOSTRAR FRAME
    # ======================================================

    def _mostrar_frame(self, frame_bgr):

        rgb = cv2.cvtColor(
            frame_bgr,
            cv2.COLOR_BGR2RGB,
        )

        h, w, ch = rgb.shape

        bytes_per_line = ch * w

        imagen = QImage(
            rgb.data,
            w,
            h,
            bytes_per_line,
            QImage.Format.Format_RGB888,
        ).copy()

        pixmap = QPixmap.fromImage(imagen)

        self.vista_camara.setPixmap(
            pixmap.scaled(
                self.vista_camara.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    # ======================================================
    # CONTROLES
    # ======================================================

    def repetir_sena(self):

        if self.phase == "inactivo" or not self.timer.isActive():
            return

        self.phase = "esperando"

        self._reset_secuencia()

        self.last_prediction = ""
        self.confidence = 0.0
        self.result_text = ""

        self.lbl_estado.setText("¡Haz la seña indicada!")
        self.lbl_prediccion.setText("")

        self.boton_siguiente.setEnabled(False)

    def siguiente_sena(self):

        if self.phase != "resultado" or not self.timer.isActive():
            return

        self.target = self._elegir_objetivo(
            anterior=self.target
        )

        self.lbl_objetivo.setText(
            self._formatear(self.target)
        )

        self.phase = "esperando"

        self._reset_secuencia()

        self.last_prediction = ""
        self.confidence = 0.0
        self.result_text = ""

        self.lbl_estado.setText("¡Haz la seña indicada!")
        self.lbl_prediccion.setText("")

        self.boton_siguiente.setEnabled(False)

    def detener_practica(self):

        self.timer.stop()

        self.phase = "inactivo"

        if self.holistic is not None:

            try:
                self.holistic.close()
            except Exception:
                pass

            self.holistic = None

        if self.camera is not None:

            try:
                self.camera.release()
            except Exception:
                pass

            self.camera = None

        self.vista_camara.setPixmap(QPixmap())

        self.vista_camara.setText(
            "Pulsa «Iniciar práctica» para abrir la cámara."
        )

        self.boton_iniciar.setEnabled(True)
        self.boton_detener.setEnabled(False)
        self.boton_repetir.setEnabled(False)
        self.boton_siguiente.setEnabled(False)

        self.lbl_estado.setText("Práctica detenida")
        self.lbl_prediccion.setText("")
        self.lbl_objetivo.setText("—")

    # ======================================================
    # UTILIDADES
    # ======================================================

    def _elegir_objetivo(self, anterior=None):

        opciones = [
            c for c in self.class_names
            if c != anterior
        ]

        if not opciones:
            opciones = self.class_names

        return random.choice(opciones)

    def _formatear(self, etiqueta):

        if not etiqueta:
            return "—"

        return str(etiqueta).replace("_", " ").upper()

    def _actualizar_marcador(self):

        accuracy = (
            self.correct / self.attempts * 100
            if self.attempts > 0
            else 0.0
        )

        self.lbl_marcador.setText(
            f"Aciertos: {self.correct}\n"
            f"Errores: {self.incorrect}\n"
            f"Efectividad: {accuracy:.1f}%"
        )

    def _actualizar_historial(self):

        if not self.history:
            self.lbl_historial.setText("—")

        else:
            self.lbl_historial.setText(
                "\n".join(self.history)
            )

    # ======================================================
    # ATAJOS DE TECLADO
    # ======================================================

    def keyPressEvent(self, event):

        if event.key() == Qt.Key.Key_R:

            self.repetir_sena()

        elif event.key() == Qt.Key.Key_Space:

            self.siguiente_sena()

        elif event.key() == Qt.Key.Key_Escape:

            self.detener_practica()

        else:

            super().keyPressEvent(event)

    # ======================================================
    # LIMPIEZA
    # ======================================================

    def closeEvent(self, event):

        self.detener_practica()

        super().closeEvent(event)


# ==========================================================
# PRUEBA INDIVIDUAL
# ==========================================================

if __name__ == "__main__":

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = ModoPracticaWidget()
    ventana.resize(1100, 700)
    ventana.setWindowTitle("GESTOSVISION - Modo práctica")
    ventana.show()

    sys.exit(app.exec())
