
import random
from collections import deque

import cv2
import numpy as np

from config import MODEL_DIR, CONFIDENCE_THRESHOLD
from model import (
    create_holistic,
    open_camera,
    extract_features,
    draw_hands,
)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

MODEL_FILE = MODEL_DIR / "gestos_lstm.keras"
LABELS_FILE = MODEL_DIR / "gestos_lstm_labels.npz"

SEQUENCE_LENGTH = 30
FEATURE_COUNT = 126

MIN_FRAMES = 8
DELAY_FRAMES = 5

CONFIDENCE_THRESHOLD_LOCAL = CONFIDENCE_THRESHOLD


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def put_text(frame, text, y, color=(255, 255, 255),
             scale=0.7):
    """Escribe texto en la ventana de la cámara."""
    cv2.putText(
        frame,
        text,
        (10, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        scale,
        color,
        2,
        cv2.LINE_AA,
    )


def normalize_sequence(frames, target_length=SEQUENCE_LENGTH):
    """Adapta una secuencia al formato que necesita el LSTM."""
    sequence = np.asarray(frames, dtype=np.float32)

    if sequence.ndim != 2 or sequence.shape[1] != FEATURE_COUNT:
        raise ValueError(
            f"Secuencia inválida: {sequence.shape}. "
            f"Se esperaba (N, {FEATURE_COUNT})."
        )

    if len(sequence) == 0:
        raise ValueError("La secuencia está vacía.")

    indices = np.linspace(
        0,
        len(sequence) - 1,
        target_length,
    ).astype(int)

    return sequence[indices]


def choose_target(class_names, previous_target=None):
    """Escoge una seña aleatoria, evitando repetir la anterior."""
    options = [
        name for name in class_names
        if name != previous_target
    ]

    if not options:
        options = class_names

    return random.choice(options)


def format_label(label):
    """Convierte el nombre de la clase a texto legible."""
    return str(label).replace("_", " ").upper()


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():

    # ------------------------------------------------------
    # 1. Comprobar los archivos
    # ------------------------------------------------------

    if not MODEL_FILE.exists():
        print(f"Error: no existe el modelo: {MODEL_FILE}")
        print("Ejecuta entrenar_modelo.py primero.")
        return

    if not LABELS_FILE.exists():
        print(f"Error: no existe el archivo: {LABELS_FILE}")
        return

    # ------------------------------------------------------
    # 2. Cargar el modelo
    # ------------------------------------------------------

    try:
        from tensorflow.keras.models import load_model
        classifier = load_model(MODEL_FILE)
    except Exception as error:
        print(f"Error cargando el modelo: {error}")
        return

    # ------------------------------------------------------
    # 3. Cargar las señas reconocidas por el modelo
    # ------------------------------------------------------

    try:
        with np.load(LABELS_FILE, allow_pickle=False) as data:
            class_names = data["class_names"].astype(str).tolist()
    except Exception as error:
        print(f"Error cargando las etiquetas: {error}")
        return

    if not class_names:
        print("Error: el modelo no tiene señas registradas.")
        return

    if len(set(class_names)) != len(class_names):
        print("Error: hay etiquetas duplicadas en el archivo.")
        return

    if classifier.input_shape[1:] != (
        SEQUENCE_LENGTH,
        FEATURE_COUNT,
    ):
        print(f"Entrada inesperada del modelo: {classifier.input_shape}")
        print("Se esperaba (None, 30, 126).")
        return

    if classifier.output_shape[-1] != len(class_names):
        print("Error: las salidas del modelo no coinciden "
              "con las etiquetas.")
        return

    # ------------------------------------------------------
    # 4. Abrir la cámara
    # ------------------------------------------------------

    try:
        camera = open_camera()
    except RuntimeError as error:
        print(f"Error abriendo la cámara: {error}")
        return

    # ------------------------------------------------------
    # 5. Variables de la práctica
    # ------------------------------------------------------

    target = choose_target(class_names)

    # Estados: esperando, grabando, resultado
    phase = "esperando"

    sequence = []
    total_frames = 0
    empty_frames = 0

    last_prediction = ""
    confidence = 0.0

    correct = 0
    incorrect = 0
    attempts = 0

    history = deque(maxlen=6)

    print("\n========================================")
    print("       GESTOSVISION - MODO PRÁCTICA")
    print("========================================")
    print(f"Señas disponibles: {len(class_names)}")
    print("Señas:", ", ".join(class_names))
    print(f"\nPrimera seña: {format_label(target)}")
    print("\nControles:")
    print("  ESPACIO: siguiente seña después del resultado")
    print("  R: repetir la seña actual")
    print("  Q / ESC: salir")
    print("========================================\n")

    # ------------------------------------------------------
    # 6. Procesamiento de la cámara
    # ------------------------------------------------------

    try:
        with create_holistic() as holistic:

            while True:
                success, frame = camera.read()

                if not success:
                    print("Error leyendo la cámara.")
                    break

                frame = cv2.flip(frame, 1)

                processing_frame = cv2.resize(
                    frame,
                    (320, 240),
                    interpolation=cv2.INTER_AREA,
                )

                rgb = cv2.cvtColor(
                    processing_frame,
                    cv2.COLOR_BGR2RGB,
                )

                rgb.flags.writeable = False
                results = holistic.process(rgb)
                rgb.flags.writeable = True

                left_detected = (
                    results.left_hand_landmarks is not None
                )
                right_detected = (
                    results.right_hand_landmarks is not None
                )

                any_hand_detected = (
                    left_detected or right_detected
                )

                draw_hands(frame, results)

                # ------------------------------------------
                # A. Capturar el movimiento del usuario
                # ------------------------------------------

                if phase in ("esperando", "grabando"):

                    if any_hand_detected:
                        empty_frames = 0

                        features = np.asarray(
                            extract_features(results),
                            dtype=np.float32,
                        ).reshape(-1)

                        if features.size == FEATURE_COUNT:

                            if phase == "esperando":
                                phase = "grabando"
                                sequence = []
                                total_frames = 0

                                print(
                                    "Capturando: "
                                    f"{format_label(target)}"
                                )

                            sequence.append(features)
                            total_frames += 1

                    elif phase == "grabando":
                        empty_frames += 1

                        # Confirmar que el movimiento terminó.
                        if empty_frames >= DELAY_FRAMES:

                            phase = "resultado"

                            if total_frames >= MIN_FRAMES:
                                try:
                                    normalized = normalize_sequence(
                                        sequence
                                    )

                                    prediction = classifier.predict(
                                        np.expand_dims(
                                            normalized,
                                            axis=0,
                                        ),
                                        verbose=0,
                                    )[0]

                                    index = int(np.argmax(prediction))
                                    confidence = float(prediction[index])

                                    last_prediction = class_names[index]

                                    attempts += 1

                                    recognized = (
                                        confidence
                                        >= CONFIDENCE_THRESHOLD_LOCAL
                                    )

                                    # Comparación de la predicción
                                    # con el objetivo solicitado.
                                    if (
                                        recognized
                                        and last_prediction == target
                                    ):
                                        correct += 1
                                        result_text = "CORRECTO"
                                        result_color = (0, 255, 0)

                                        history.append(
                                            f"OK: {format_label(target)}"
                                        )

                                    else:
                                        incorrect += 1

                                        if recognized:
                                            result_text = "INCORRECTO"
                                        else:
                                            result_text = "NO RECONOCIDA"

                                        result_color = (0, 0, 255)

                                        history.append(
                                            f"X: {format_label(target)}"
                                        )

                                    print(
                                        f"Objetivo: {target} | "
                                        f"Predicción: {last_prediction} | "
                                        f"Confianza: {confidence:.1%} | "
                                        f"{result_text}"
                                    )

                                except Exception as error:
                                    last_prediction = ""
                                    confidence = 0.0
                                    result_text = "ERROR AL EVALUAR"
                                    result_color = (0, 0, 255)

                                    print(
                                        f"Error procesando la seña: {error}"
                                    )

                            else:
                                last_prediction = ""
                                confidence = 0.0
                                result_text = "SEÑA MUY CORTA"
                                result_color = (0, 165, 255)

                                print(
                                    "Seña demasiado corta. "
                                    "Presiona R para intentarlo de nuevo."
                                )

                            sequence = []
                            total_frames = 0
                            empty_frames = 0

                # ------------------------------------------
                # B. Preparar textos de la interfaz
                # ------------------------------------------

                if phase == "esperando":
                    status = "HAZ LA SENA"
                    status_color = (0, 255, 255)

                elif phase == "grabando":
                    status = "CAPTURANDO MOVIMIENTO..."
                    status_color = (0, 200, 255)

                else:
                    status = result_text
                    status_color = result_color

                put_text(
                    frame,
                    "GESTOSVISION - MODO PRACTICA",
                    30,
                    (255, 255, 0),
                    0.7,
                )

                put_text(
                    frame,
                    f"OBJETIVO: {format_label(target)}",
                    75,
                    (0, 255, 255),
                    0.9,
                )

                put_text(
                    frame,
                    status,
                    115,
                    status_color,
                    0.85,
                )

                if phase == "resultado" and last_prediction:
                    put_text(
                        frame,
                        f"Tu sena: {format_label(last_prediction)}",
                        150,
                        (255, 255, 255),
                        0.65,
                    )

                    put_text(
                        frame,
                        f"Confianza: {confidence:.1%}",
                        180,
                        (255, 255, 255),
                        0.65,
                    )

                elif phase == "grabando":
                    put_text(
                        frame,
                        f"Fotogramas: {total_frames}",
                        150,
                        (255, 255, 255),
                        0.65,
                    )

                # Marcador
                put_text(
                    frame,
                    f"Aciertos: {correct}  Errores: {incorrect}",
                    220,
                    (0, 255, 0),
                    0.65,
                )

                accuracy = (
                    correct / attempts * 100
                    if attempts > 0
                    else 0.0
                )

                put_text(
                    frame,
                    f"Efectividad: {accuracy:.1f}%",
                    250,
                    (255, 255, 255),
                    0.65,
                )

                # Historial reciente
                history_text = " | ".join(history)

                put_text(
                    frame,
                    history_text[-85:],
                    280,
                    (200, 255, 200),
                    0.45,
                )

                put_text(
                    frame,
                    "R: repetir | ESPACIO: siguiente | Q: salir",
                    frame.shape[0] - 15,
                    (255, 255, 255),
                    0.48,
                )

                cv2.imshow(
                    "GESTOSVISION - Modo practica",
                    frame,
                )

                # ------------------------------------------
                # C. Controles
                # ------------------------------------------

                key = cv2.waitKey(1) & 0xFF

                if key in (ord("q"), 27):
                    break

                # Repetir el mismo objetivo.
                if key == ord("r"):
                    phase = "esperando"
                    sequence = []
                    total_frames = 0
                    empty_frames = 0

                    last_prediction = ""
                    confidence = 0.0

                    print(
                        f"\nRepite la seña: {format_label(target)}"
                    )

                # Elegir un nuevo objetivo después de evaluar.
                if key == ord(" ") and phase == "resultado":
                    previous_target = target

                    target = choose_target(
                        class_names,
                        previous_target,
                    )

                    phase = "esperando"
                    sequence = []
                    total_frames = 0
                    empty_frames = 0

                    last_prediction = ""
                    confidence = 0.0

                    print(
                        f"\nSiguiente objetivo: "
                        f"{format_label(target)}"
                    )

    except KeyboardInterrupt:
        print("\nPráctica interrumpida.")

    finally:
        camera.release()
        cv2.destroyAllWindows()

    # ------------------------------------------------------
    # 7. Resumen final
    # ------------------------------------------------------

    accuracy = (
        correct / attempts * 100
        if attempts > 0
        else 0.0
    )

    print("\n========================================")
    print("          RESUMEN DE PRÁCTICA")
    print("========================================")
    print(f"Intentos evaluados: {attempts}")
    print(f"Aciertos:           {correct}")
    print(f"Errores:            {incorrect}")
    print(f"Efectividad:        {accuracy:.1f}%")
    print("========================================")
    print("Práctica finalizada.")


if __name__ == "__main__":
    main()
