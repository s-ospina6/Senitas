
import cv2
import numpy as np

from pathlib import Path
from collections import deque

from config import MODEL_DIR, CONFIDENCE_THRESHOLD

from model import (
    create_holistic,
    open_camera,
    extract_features,
    draw_hands,
)


# ============================================================
# CONFIGURACION DE RUTAS
# ============================================================

MODEL_DIR = Path(MODEL_DIR).resolve()

MODEL_FILE = MODEL_DIR / "gestos_lstm.keras"
LABELS_FILE = MODEL_DIR / "gestos_lstm_labels.npz"


# ============================================================
# CONFIGURACION DEL RECONOCIMIENTO
# ============================================================

SEQUENCE_LENGTH = 30
FEATURE_COUNT = 126

MIN_FRAMES = 8
DELAY_FRAMES = 5

CONFIDENCE_THRESHOLD_LOCAL = CONFIDENCE_THRESHOLD

WINDOW_NAME = "SENITAS - RECONOCIMIENTO"


# ============================================================
# CARGAR MODELO Y ETIQUETAS
# ============================================================

def load_classifier():

    print("\n========== CARGANDO SENITAS ==========")

    print("Directorio:", MODEL_DIR)
    print("Modelo:", MODEL_FILE)
    print("Etiquetas:", LABELS_FILE)

    if not MODEL_FILE.is_file():
        raise FileNotFoundError(
            f"No existe el modelo: {MODEL_FILE}"
        )

    if not LABELS_FILE.is_file():
        raise FileNotFoundError(
            f"No existen las etiquetas: {LABELS_FILE}"
        )

    # El archivo .keras es un ZIP de Keras.
    # NO comprobar con h5py.is_hdf5().

    from tensorflow.keras.models import load_model

    print("\nCargando modelo LSTM...")

    classifier = load_model(
        str(MODEL_FILE),
        compile=False
    )

    print("Modelo cargado correctamente.")

    print("Entrada:", classifier.input_shape)
    print("Salida:", classifier.output_shape)

    # --------------------------------------------------------
    # CARGAR ETIQUETAS
    # --------------------------------------------------------

    with np.load(
        LABELS_FILE,
        allow_pickle=False
    ) as data:

        if "class_names" not in data.files:
            raise ValueError(
                "No se encontró class_names en el archivo NPZ. "
                f"Claves: {data.files}"
            )

        class_names = (
            data["class_names"]
            .astype(str)
            .tolist()
        )

    print("\nEtiquetas cargadas:")

    for index, name in enumerate(class_names):
        print(f"{index}: {name}")

    # --------------------------------------------------------
    # VALIDAR DIMENSIONES
    # --------------------------------------------------------

    expected_shape = (
        None,
        SEQUENCE_LENGTH,
        FEATURE_COUNT
    )

    if classifier.input_shape != expected_shape:
        raise ValueError(
            f"Entrada incorrecta: {classifier.input_shape}. "
            f"Se esperaba: {expected_shape}"
        )

    if classifier.output_shape[-1] != len(class_names):
        raise ValueError(
            "La cantidad de salidas del modelo "
            "no coincide con las etiquetas."
        )

    print("\n======================================")
    print("SENITAS: MODELO LISTO")
    print("Clases:", len(class_names))
    print("======================================")

    return classifier, class_names


# ============================================================
# MOSTRAR TEXTO
# ============================================================

def put_text(
    frame,
    text,
    y,
    color=(255, 255, 255),
    scale=0.7
):

    cv2.putText(
        frame,
        str(text),
        (10, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        2,
        cv2.LINE_AA
    )


# ============================================================
# NORMALIZAR SECUENCIA
# ============================================================

def normalize_sequence(
    frames,
    target_length=SEQUENCE_LENGTH
):

    sequence = np.asarray(
        frames,
        dtype=np.float32
    )

    if sequence.ndim != 2:
        raise ValueError(
            f"Dimensiones incorrectas: {sequence.shape}"
        )

    if sequence.shape[1] != FEATURE_COUNT:
        raise ValueError(
            f"Se esperaban {FEATURE_COUNT} características, "
            f"se recibieron {sequence.shape[1]}"
        )

    if len(sequence) == 0:
        raise ValueError(
            "La secuencia está vacía."
        )

    # Distribuir los fotogramas a lo largo del movimiento.

    indices = np.linspace(
        0,
        len(sequence) - 1,
        target_length
    ).astype(int)

    normalized = sequence[indices]

    return normalized


# ============================================================
# PREDECIR SEÑA
# ============================================================

def predict_sign(
    classifier,
    class_names,
    sequence
):

    normalized = normalize_sequence(sequence)

    input_data = np.expand_dims(
        normalized,
        axis=0
    )

    prediction = classifier.predict(
        input_data,
        verbose=0
    )[0]

    index = int(np.argmax(prediction))

    confidence = float(prediction[index])

    predicted_label = class_names[index]

    return predicted_label, confidence


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    # --------------------------------------------------------
    # CARGAR MODELO
    # --------------------------------------------------------

    try:

        classifier, class_names = load_classifier()

    except Exception as error:

        print("\nERROR AL CARGAR EL MODELO:")
        print(error)

        return

    # --------------------------------------------------------
    # ABRIR CAMARA
    # --------------------------------------------------------

    camera = None

    try:

        camera = open_camera()

    except RuntimeError as error:

        print("\nERROR ABRIENDO LA CAMARA:")
        print(error)

        return

    # --------------------------------------------------------
    # VARIABLES
    # --------------------------------------------------------

    sequence = []

    sentence = deque(maxlen=8)

    recording = False

    empty_frames = 0

    total_frames = 0

    label = "ESPERANDO UNA SENA"

    confidence = 0.0

    left_detected = False

    right_detected = False

    # --------------------------------------------------------
    # RECONOCIMIENTO EN TIEMPO REAL
    # --------------------------------------------------------

    try:

        with create_holistic() as holistic:

            print("\n======================================")
            print("SENITAS - RECONOCIMIENTO DE SENAS")
            print("======================================")

            print("Realiza una seña y deja de mover las manos.")
            print("Q / ESC: salir")
            print("C: limpiar historial")

            while True:

                # ============================================
                # LEER CAMARA
                # ============================================

                success, frame = camera.read()

                if not success:

                    print("Error leyendo la cámara.")

                    break

                frame = cv2.flip(
                    frame,
                    1
                )

                processing_frame = cv2.resize(
                    frame,
                    (320, 240),
                    interpolation=cv2.INTER_AREA
                )

                rgb = cv2.cvtColor(
                    processing_frame,
                    cv2.COLOR_BGR2RGB
                )

                rgb.flags.writeable = False

                results = holistic.process(rgb)

                rgb.flags.writeable = True

                # ============================================
                # DETECTAR MANOS
                # ============================================

                left_detected = (
                    results.left_hand_landmarks is not None
                )

                right_detected = (
                    results.right_hand_landmarks is not None
                )

                any_hand_detected = (
                    left_detected or right_detected
                )

                draw_hands(
                    frame,
                    results
                )

                # ============================================
                # CAPTURAR MOVIMIENTO
                # ============================================

                if any_hand_detected:

                    empty_frames = 0

                    features = np.asarray(
                        extract_features(results),
                        dtype=np.float32
                    ).reshape(-1)

                    if features.size == FEATURE_COUNT:

                        if not recording:

                            recording = True

                            sequence = []

                            total_frames = 0

                            label = "CAPTURANDO SENA"

                        total_frames += 1

                        sequence.append(features)

                # ============================================
                # DETECTAR FINAL DE SEÑA
                # ============================================

                elif recording:

                    empty_frames += 1

                    if empty_frames >= DELAY_FRAMES:

                        recording = False

                        if (
                            total_frames >= MIN_FRAMES
                            and sequence
                        ):

                            try:

                                predicted_label, confidence = predict_sign(
                                    classifier,
                                    class_names,
                                    sequence
                                )

                                print(
                                    f"\nPredicción: {predicted_label}"
                                    f" ({confidence:.1%})"
                                )

                                if confidence >= CONFIDENCE_THRESHOLD_LOCAL:

                                    label = predicted_label.upper()

                                    # Evitar palabras repetidas
                                    # consecutivamente.

                                    if (
                                        not sentence
                                        or sentence[-1] != predicted_label
                                    ):

                                        sentence.append(
                                            predicted_label
                                        )

                                else:

                                    label = "SENA NO RECONOCIDA"

                                    print(
                                        "Confianza insuficiente."
                                    )

                            except Exception as error:

                                label = "ERROR EN PREDICCION"

                                print(
                                    "Error procesando la seña:",
                                    error
                                )

                        else:

                            label = "SENA DEMASIADO CORTA"

                        sequence = []

                        total_frames = 0

                        empty_frames = 0

                # ============================================
                # INTERFAZ VISUAL
                # ============================================

                if recording:

                    display_label = "CAPTURANDO SENA..."

                    color = (0, 200, 255)

                elif label == "ESPERANDO UNA SENA":

                    display_label = label

                    color = (180, 180, 180)

                elif label in (
                    "SENA NO RECONOCIDA",
                    "SENA DEMASIADO CORTA",
                    "ERROR EN PREDICCION"
                ):

                    display_label = label

                    color = (0, 165, 255)

                else:

                    display_label = label

                    color = (0, 255, 0)

                # TITULO

                put_text(
                    frame,
                    "SENITAS - RECONOCIMIENTO",
                    30,
                    (0, 255, 255)
                )

                # SEÑA DETECTADA

                put_text(
                    frame,
                    f"Sena: {display_label}",
                    70,
                    color,
                    0.85
                )

                # CONFIANZA

                put_text(
                    frame,
                    f"Confianza: {confidence:.0%}",
                    105
                )

                # FOTOGRAMAS

                put_text(
                    frame,
                    f"Fotogramas: {total_frames}",
                    135
                )

                # MANO IZQUIERDA

                put_text(
                    frame,
                    f"Mano izquierda: {'SI' if left_detected else 'NO'}",
                    165
                )

                # MANO DERECHA

                put_text(
                    frame,
                    f"Mano derecha: {'SI' if right_detected else 'NO'}",
                    195
                )

                # HISTORIAL

                history_text = " - ".join(sentence)

                put_text(
                    frame,
                    f"Historial: {history_text}"[-80:],
                    230,
                    (0, 255, 0),
                    0.55
                )

                # INSTRUCCIONES

                put_text(
                    frame,
                    "Q/ESC: salir | C: limpiar",
                    frame.shape[0] - 15,
                    (255, 255, 255),
                    0.55
                )

                # MOSTRAR VENTANA

                cv2.imshow(
                    WINDOW_NAME,
                    frame
                )

                # ============================================
                # CONTROLES
                # ============================================

                key = cv2.waitKey(1) & 0xFF

                if key in (ord("q"), 27):

                    break

                if key == ord("c"):

                    sentence.clear()

                    label = "ESPERANDO UNA SENA"

                    confidence = 0.0

                    print("\nHistorial limpiado.")

    except KeyboardInterrupt:

        print("\nReconocimiento interrumpido.")

    except Exception as error:

        print("\nERROR DURANTE EL RECONOCIMIENTO:")
        print(error)

    finally:

        if camera is not None:

            camera.release()

        cv2.destroyAllWindows()

    print("\nReconocimiento finalizado.")


# ============================================================
# EJECUCION
# ============================================================

if __name__ == "__main__":

    main()
