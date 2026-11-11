from collections import deque
from pathlib import Path

import cv2
import numpy as np

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QImage, QPixmap
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
# PALETA (alineada con el estilo global de la app)
# ==========================================================

CREMA = "#FFF3DD"
NAVY = "#2B3A67"
MORADO = "#6C4DC4"
MORADO_OSCURO = "#5B3A9E"
NARANJA = "#F7941D"
AMARILLO = "#FFC93C"
ROSA = "#F0527A"
VERDE = "#4CAF50"


def _oscuro(color, factor=135):
    return QColor(color).darker(factor).name()


def _claro(color, factor=110):
    return QColor(color).lighter(factor).name()


# ==========================================================
# WIDGET
# ==========================================================

class ReconocerSenasWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Recursos pesados (carga diferida).
        self.classifier = None
        self.class_names = []
        self.camera = None
        self.holistic = None

        # Estado del reconocimiento.
        self.recording = False
        self.sequence = []
        self.empty_frames = 0
        self.total_frames = 0
        self.label = "ESPERANDO UNA SEÑA"
        self.confidence = 0.0
        self.sentence = deque(maxlen=8)
        self.left_detected = False
        self.right_detected = False

        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self._procesar_frame)

        self.crear_interfaz()

    # ------------------------------------------------------
    # INTERFAZ
    # ------------------------------------------------------

    def crear_interfaz(self):

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(22, 20, 22, 20)
        layout_principal.setSpacing(14)

        # ---------- Visor de cámara ----------
        panel_camara = QFrame()
        panel_camara.setObjectName("panelCamara")

        layout_camara = QVBoxLayout(panel_camara)
        layout_camara.setContentsMargins(10, 10, 10, 10)

        self.vista_camara = QLabel(
            "🎥  Pulsa «¡Empezar a jugar!» para abrir la cámara."
        )
        self.vista_camara.setObjectName("visorCamara")
        self.vista_camara.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.vista_camara.setMinimumSize(480, 360)
        self.vista_camara.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        layout_camara.addWidget(self.vista_camara)

        layout_principal.addWidget(panel_camara, 1)

        # ---------- Estado ----------
        self.lbl_estado = QLabel("¡Listo para empezar! 🎉")
        self.lbl_estado.setObjectName("valorEstado")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setWordWrap(True)

        layout_principal.addWidget(self.lbl_estado)

        # ---------- Historial ----------
        self.lbl_historial = QLabel("—")
        self.lbl_historial.setObjectName("valorHistorial")
        self.lbl_historial.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_historial.setWordWrap(True)

        layout_principal.addWidget(self.lbl_historial)

        # ---------- Botones ----------
        layout_botones = QHBoxLayout()
        layout_botones.setSpacing(12)

        self.boton_iniciar = QPushButton("🚀  ¡Empezar a jugar!")
        self.boton_iniciar.setObjectName("principal")
        self.boton_iniciar.setMinimumHeight(58)
        self.boton_iniciar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_iniciar.clicked.connect(self.iniciar_reconocimiento)

        self.boton_limpiar = QPushButton("🧹  Borrar historial (C)")
        self.boton_limpiar.setObjectName("limpiar")
        self.boton_limpiar.setMinimumHeight(58)
        self.boton_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_limpiar.setEnabled(False)
        self.boton_limpiar.clicked.connect(self.limpiar_historial)

        self.boton_detener = QPushButton("🛑  Detener")
        self.boton_detener.setObjectName("detener")
        self.boton_detener.setMinimumHeight(58)
        self.boton_detener.setCursor(Qt.CursorShape.PointingHandCursor)
        self.boton_detener.setEnabled(False)
        self.boton_detener.clicked.connect(self.detener_reconocimiento)

        layout_botones.addWidget(self.boton_iniciar, 2)
        layout_botones.addWidget(self.boton_limpiar, 1)
        layout_botones.addStretch()
        layout_botones.addWidget(self.boton_detener, 1)

        layout_principal.addLayout(layout_botones)

        # --------------------------------------------------
        # ESTILOS (alineados con el estilo global de la app)
        # --------------------------------------------------

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {CREMA};
                color: {NAVY};
                font-family: "Comic Sans MS", "Verdana", "Sans Serif";
                font-size: 14px;
            }}

            /* ---------- Panel de cámara ---------- */
            QFrame#panelCamara {{
                background-color: #FFFFFF;
                border: 5px solid {AMARILLO};
                border-radius: 32px;
            }}

            /* ---------- Visor de cámara ---------- */
            QLabel#visorCamara {{
                background-color: {CREMA};
                color: {MORADO};
                border: 4px dashed {MORADO};
                border-radius: 26px;
                padding: 16px;
                font-size: 15px;
                font-weight: 700;
            }}

            /* ---------- Estado ---------- */
            QLabel#valorEstado {{
                color: {MORADO};
                font-size: 22px;
                font-weight: 900;
                padding: 8px;
            }}

            /* ---------- Historial ---------- */
            QLabel#valorHistorial {{
                color: {VERDE};
                font-size: 16px;
                font-weight: 900;
                padding: 2px 8px 8px 8px;
            }}

            /* ---------- Botones tipo pastilla 3D ---------- */
            QPushButton {{
                background-color: {MORADO};
                color: white;
                border: none;
                border-bottom: 7px solid {MORADO_OSCURO};
                border-radius: 28px;
                padding: 12px 22px;
                font-size: 17px;
                font-weight: 900;
            }}

            QPushButton:hover:enabled {{
                background-color: {_claro(MORADO)};
            }}

            QPushButton:pressed:enabled {{
                border-bottom: 3px solid {MORADO_OSCURO};
                padding-top: 16px;
                padding-bottom: 8px;
            }}

            QPushButton:disabled {{
                background-color: #E6DDF7;
                color: #B7A9D6;
                border-bottom: 7px solid #D3C6EC;
            }}

            /* Botón principal (rosa) */
            QPushButton#principal {{
                background-color: {ROSA};
                border-bottom: 7px solid {_oscuro(ROSA)};
                font-size: 19px;
            }}

            QPushButton#principal:hover:enabled {{
                background-color: {_claro(ROSA)};
            }}

            QPushButton#principal:pressed:enabled {{
                border-bottom: 3px solid {_oscuro(ROSA)};
            }}

            QPushButton#principal:disabled {{
                background-color: #F7CFD9;
                color: #FFFFFF;
                border-bottom: 7px solid #EBB6C3;
            }}

            /* Botón limpiar (verde) */
            QPushButton#limpiar {{
                background-color: {VERDE};
                border-bottom: 7px solid {_oscuro(VERDE)};
            }}

            QPushButton#limpiar:hover:enabled {{
                background-color: {_claro(VERDE)};
            }}

            QPushButton#limpiar:pressed:enabled {{
                border-bottom: 3px solid {_oscuro(VERDE)};
            }}

            QPushButton#limpiar:disabled {{
                background-color: #D6ECD7;
                color: #A9C7AB;
                border-bottom: 7px solid #BFDCB1;
            }}

            /* Botón detener (naranja) */
            QPushButton#detener {{
                background-color: {NARANJA};
                border-bottom: 7px solid {_oscuro(NARANJA)};
            }}

            QPushButton#detener:hover:enabled {{
                background-color: {_claro(NARANJA)};
            }}

            QPushButton#detener:pressed:enabled {{
                border-bottom: 3px solid {_oscuro(NARANJA)};
            }}

            QPushButton#detener:disabled {{
                background-color: #FCE4C7;
                color: #E6C79A;
                border-bottom: 7px solid #F0CFA0;
            }}
        """)

    # ------------------------------------------------------
    # INICIAR
    # ------------------------------------------------------

    def iniciar_reconocimiento(self):
        if self.timer.isActive():
            return

        if not self._cargar_modelo():
            return

        if not self._abrir_camara():
            return

        self.recording = False
        self.sequence = []
        self.empty_frames = 0
        self.total_frames = 0
        self.label = "ESPERANDO UNA SEÑA"
        self.confidence = 0.0
        self.sentence.clear()

        self.lbl_estado.setText("¡Esperando una seña! 👀")
        self.lbl_historial.setText("—")

        self.boton_iniciar.setEnabled(False)
        self.boton_detener.setEnabled(True)
        self.boton_limpiar.setEnabled(True)

        self.timer.start()

    # ------------------------------------------------------
    # CARGAR MODELO
    # ------------------------------------------------------

    def _cargar_modelo(self):
        if self.classifier is not None and self.class_names:
            return True

        if not MODEL_FILE.exists():
            QMessageBox.warning(
                self,
                "¡Ups! 🙈",
                f"No encontramos el modelo:\n{MODEL_FILE}\n\n"
                "Pídele a un adulto que entrene el modelo primero.",
            )
            return False

        if not LABELS_FILE.exists():
            QMessageBox.warning(
                self,
                "¡Falta un archivo! 📁",
                f"No encontramos:\n{LABELS_FILE}\n\n"
                "Pídele ayuda a un adulto. 🙏",
            )
            return False

        try:
            from tensorflow.keras.models import load_model
            self.classifier = load_model(MODEL_FILE)
        except Exception as error:
            QMessageBox.critical(
                self,
                "¡Algo salió mal! 😢",
                f"No pudimos cargar el modelo:\n\n{error}",
            )
            return False

        try:
            with np.load(LABELS_FILE, allow_pickle=False) as data:
                self.class_names = data["class_names"].astype(str).tolist()
        except Exception as error:
            QMessageBox.critical(
                self,
                "¡Algo salió mal! 😢",
                f"No pudimos cargar las etiquetas:\n\n{error}",
            )
            return False

        if self.classifier.input_shape[1:] != (
            SEQUENCE_LENGTH,
            FEATURE_COUNT,
        ):
            QMessageBox.critical(
                self,
                "¡Modelo incompatible! 🤖",
                f"El modelo no encaja con esta versión.\n"
                f"Entrada: {self.classifier.input_shape}",
            )
            return False

        if self.classifier.output_shape[-1] != len(self.class_names):
            QMessageBox.critical(
                self,
                "¡Modelo incompatible! 🤖",
                "Las respuestas del modelo no coinciden con las etiquetas.",
            )
            return False

        return True

    # ------------------------------------------------------
    # CÁMARA
    # ------------------------------------------------------

    def _abrir_camara(self):
        if self.camera is not None and self.camera.isOpened():
            return True

        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            QMessageBox.critical(
                self,
                "¡Cámara ocupada! 📷",
                "No pudimos abrir la cámara.\n"
                "Pídele a un adulto que la revise. 🙏",
            )
            self.camera = None
            return False

        self.holistic = self._crear_holistic()
        return True

    def _importar_modelo_utils(self):
        import sys
        if str(BASE_DIR) not in sys.path:
            sys.path.insert(0, str(BASE_DIR))

        from model import (  # noqa: WPS433
            create_holistic,
            extract_features,
            draw_hands,
        )
        return create_holistic, extract_features, draw_hands

    def _crear_holistic(self):
        create_holistic, _, _ = self._importar_modelo_utils()
        return create_holistic()

    # ------------------------------------------------------
    # BUCLE DE PROCESAMIENTO
    # ------------------------------------------------------

    def _procesar_frame(self):
        if self.camera is None:
            return

        ok, frame = self.camera.read()
        if not ok:
            self.detener_reconocimiento()
            return

        frame = cv2.flip(frame, 1)

        _, extract_features, draw_hands = self._importar_modelo_utils()

        processing = cv2.resize(
            frame, (320, 240), interpolation=cv2.INTER_AREA
        )
        rgb = cv2.cvtColor(processing, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.holistic.process(rgb)
        rgb.flags.writeable = True

        self.left_detected = results.left_hand_landmarks is not None
        self.right_detected = results.right_hand_landmarks is not None
        any_hand = self.left_detected or self.right_detected

        draw_hands(frame, results)

        if any_hand:
            self.empty_frames = 0
            features = np.asarray(
                extract_features(results), dtype=np.float32
            ).reshape(-1)

            if features.size == FEATURE_COUNT:
                if not self.recording:
                    self.recording = True
                    self.sequence = []
                    self.total_frames = 0
                    self.label = "CAPTURANDO SEÑA"

                self.total_frames += 1
                self.sequence.append(features)

        elif self.recording:
            self.empty_frames += 1
            if self.empty_frames >= DELAY_FRAMES:
                self.recording = False
                self._evaluar_secuencia()

        self._actualizar_estado()
        self._dibujar_hud(frame)
        self._mostrar_frame(frame)

    # ------------------------------------------------------
    # EVALUAR SECUENCIA
    # ------------------------------------------------------

    def _evaluar_secuencia(self):
        if self.total_frames >= MIN_FRAMES and self.sequence:
            try:
                normalized = self._normalizar_secuencia(self.sequence)
                prediction = self.classifier.predict(
                    np.expand_dims(normalized, axis=0), verbose=0
                )[0]

                index = int(np.argmax(prediction))
                self.confidence = float(prediction[index])
                predicted_label = self.class_names[index]

                if self.confidence >= CONFIDENCE_THRESHOLD:
                    self.label = predicted_label.upper()

                    if (
                        not self.sentence
                        or self.sentence[-1] != predicted_label
                    ):
                        self.sentence.append(predicted_label)

                else:
                    self.label = "SEÑA NO RECONOCIDA"

            except Exception:
                self.label = "ERROR EN LA PREDICCIÓN"

        else:
            self.label = "SEÑA DEMASIADO CORTA"

        self.sequence = []
        self.total_frames = 0
        self.empty_frames = 0

    def _normalizar_secuencia(self, frames, target_length=SEQUENCE_LENGTH):
        sequence = np.asarray(frames, dtype=np.float32)
        indices = np.linspace(
            0, len(sequence) - 1, target_length
        ).astype(int)
        return sequence[indices]

    # ------------------------------------------------------
    # ACTUALIZAR ESTADO
    # ------------------------------------------------------

    def _actualizar_estado(self):
        if self.recording:
            self.lbl_estado.setText("¡Capturando tu seña! 📸")
        elif self.label == "ESPERANDO UNA SEÑA":
            self.lbl_estado.setText("¡Esperando una seña! 👀")
        elif self.label == "SEÑA NO RECONOCIDA":
            self.lbl_estado.setText("¡No la reconozco! 😅")
        elif self.label == "SEÑA DEMASIADO CORTA":
            self.lbl_estado.setText("¡Más despacio! ⏱️")
        elif self.label == "ERROR EN LA PREDICCIÓN":
            self.lbl_estado.setText("¡Ups, algo falló! 😢")
        else:
            self.lbl_estado.setText(f"¡Es {self.label}! 🎉")

        if self.sentence:
            self.lbl_historial.setText(" · ".join(self.sentence))
        else:
            self.lbl_historial.setText("—")

    # ------------------------------------------------------
    # HUD EN EL FRAME
    # ------------------------------------------------------

    def _dibujar_hud(self, frame):
        def texto(txt, y, color=(255, 255, 255), scale=0.6):
            cv2.putText(
                frame, txt, (10, y),
                cv2.FONT_HERSHEY_SIMPLEX, scale, color, 2, cv2.LINE_AA,
            )

        if self.recording:
            display = "CAPTURANDO SEÑA..."
            color = (0, 200, 255)
        elif self.label == "ESPERANDO UNA SEÑA":
            display = self.label
            color = (180, 180, 180)
        elif self.label in (
            "SEÑA NO RECONOCIDA",
            "SEÑA DEMASIADO CORTA",
            "ERROR EN LA PREDICCIÓN",
        ):
            display = self.label
            color = (0, 165, 255)
        else:
            display = self.label
            color = (0, 255, 0)

        texto("GESTOSVISION - RECONOCIMIENTO", 28, (0, 255, 255), 0.6)
        texto(f"Seña: {display}", 65, color, 0.8)

        hist = " - ".join(self.sentence)
        if hist:
            texto(f"Historial: {hist}"[-80:], 95, (0, 255, 0), 0.5)

    # ------------------------------------------------------
    # MOSTRAR FRAME EN EL QLABEL
    # ------------------------------------------------------

    def _mostrar_frame(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        imagen = QImage(
            rgb.data, w, h, ch * w, QImage.Format.Format_RGB888
        ).copy()

        pixmap = QPixmap.fromImage(imagen)
        self.vista_camara.setPixmap(
            pixmap.scaled(
                self.vista_camara.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    # ------------------------------------------------------
    # CONTROLES
    # ------------------------------------------------------

    def limpiar_historial(self):
        self.sentence.clear()
        self.label = "ESPERANDO UNA SEÑA"
        self.confidence = 0.0
        self.lbl_estado.setText("¡Esperando una seña! 👀")
        self.lbl_historial.setText("—")

    def detener_reconocimiento(self):
        self.timer.stop()

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
            "🎥  Pulsa «¡Empezar a jugar!» para abrir la cámara."
        )

        self.boton_iniciar.setEnabled(True)
        self.boton_detener.setEnabled(False)
        self.boton_limpiar.setEnabled(False)

        self.lbl_estado.setText("¡Juego detenido! 💤")
        self.lbl_historial.setText("—")

    # ------------------------------------------------------
    # ATAJOS
    # ------------------------------------------------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_C:
            self.limpiar_historial()
        elif event.key() == Qt.Key.Key_Escape:
            self.detener_reconocimiento()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.detener_reconocimiento()
        super().closeEvent(event)


# ==========================================================
# PRUEBA INDIVIDUAL
# ==========================================================

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    ventana = ReconocerSenasWidget()
    ventana.resize(1150, 740)
    ventana.setWindowTitle("Reconocer señas · GESTOSVISION")
    ventana.show()

    sys.exit(app.exec())