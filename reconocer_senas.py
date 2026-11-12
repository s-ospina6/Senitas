
import cv2
import numpy as np

from collections import deque

from config import MODEL_DIR, CONFIDENCE_THRESHOLD
from model import (
    create_holistic,
    open_camera,
    extract_features,
    draw_hands,
)


MODEL_FILE = MODEL_DIR / "gestos_lstm.keras"
LABELS_FILE = MODEL_DIR / "gestos_lstm_labels.npz"

SEQUENCE_LENGTH = 30
FEATURE_COUNT = 126

# Ajustes para detectar el final de una seña
MIN_FRAMES = 8
MARGIN_FRAMES = 1
DELAY_FRAMES = 5
CONFIDENCE_THRESHOLD_LOCAL = CONFIDENCE_THRESHOLD


def put_text(frame, text, y, color=(255, 255, 255), scale=0.7):
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
    """
    Ajusta una secuencia de cualquier longitud a los 30 fotogramas
    que espera el modelo LSTM.
    """
    sequence = np.asarray(frames, dtype=np.float32)

    if sequence.ndim != 2 or sequence.shape[1] != FEATURE_COUNT:
        raise ValueError(
            f"Secuencia inválida: se esperaba (N, {FEATURE_COUNT}), "
            f"se recibió {sequence.shape}"
        )

    if len(sequence) == 0:
        raise ValueError("La secuencia está vacía.")

    # Seleccionar índices distribuidos por todo el movimiento.
    indices = np.linspace(
        0,
        len(sequence) - 1,
        target_length,
    ).astype(int)

    return sequence[indices]


def main():
    if not MODEL_FILE.exists():
        print(f"Error: no existe el modelo: {MODEL_FILE}")
        print("Ejecuta entrenar_modelo.py primero.")
        return

    if not LABELS_FILE.exists():
        print(f"Error: no se encuentran las etiquetas: {LABELS_FILE}")
        return

    try:
        from tensorflow.keras.models import load_model
        classifier = load_model(MODEL_FILE)
    except Exception as error:
        print(f"Error cargando el modelo: {error}")
        return

    try:
        with np.load(LABELS_FILE, allow_pickle=False) as data:
            class_names = data["class_names"].astype(str).tolist()
    except Exception as error:
        print(f"Error cargando las etiquetas: {error}")
        return

    if classifier.input_shape[1:] != (SEQUENCE_LENGTH, FEATURE_COUNT):
        print(f"Entrada inesperada del modelo: {classifier.input_shape}")
        print("Se esperaba (None, 30, 126).")
        return

    if classifier.output_shape[-1] != len(class_names):
        print("Error: las salidas no coinciden con las etiquetas.")
        return

    try:
        camera = open_camera()
    except RuntimeError as error:
        print(f"Error abriendo la cámara: {error}")
        return

    sequence = []
    sentence = deque(maxlen=8)

    recording = False
    empty_frames = 0
    total_frames = 0

    label = "ESPERANDO UNA SEÑA"
    confidence = 0.0

    try:
        with create_holistic() as holistic:
            print("GESTOSVISION: reconocimiento por movimiento.")
            print("Realiza una seña y deja de mover las manos al terminar.")
            print("Q/ESC: salir | C: limpiar el historial")

            while True:
                success, frame = camera.read()

                if not success:
                    print("Error leyendo la cámara.")
                    break

                frame = cv2.flip(frame, 1)

                # MediaPipe procesa una imagen reducida para mayor velocidad.
                processing_frame = cv2.resize(
                    frame,
                    (320, 240),
                    interpolation=cv2.INTER_AREA,
                )

                rgb = cv2.cvtColor(processing_frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = holistic.process(rgb)
                rgb.flags.writeable = True

                left_detected = results.left_hand_landmarks is not None
                right_detected = results.right_hand_landmarks is not None
                any_hand_detected = left_detected or right_detected

                draw_hands(frame, results)

                if any_hand_detected:
                    empty_frames = 0

                    features = np.asarray(
                        extract_features(results),
                        dtype=np.float32,
                    ).reshape(-1)

                    if features.size == FEATURE_COUNT:
                        if not recording:
                            recording = True
                            sequence = []
                            total_frames = 0
                            label = "CAPTURANDO SEÑA"

                        total_frames += 1
                        sequence.append(features)

                elif recording:
                    empty_frames += 1

                    # Esperar unos fotogramas para confirmar que terminó
                    # el gesto y no fue una pérdida momentánea de detección.
                    if empty_frames >= DELAY_FRAMES:
                        recording = False

                        if total_frames >= MIN_FRAMES and sequence:
                            try:
                                normalized = normalize_sequence(sequence)

                                prediction = classifier.predict(
                                    np.expand_dims(normalized, axis=0),
                                    verbose=0,
                                )[0]

                                index = int(np.argmax(prediction))
                                confidence = float(prediction[index])
                                predicted_label = class_names[index]

                                if confidence >= CONFIDENCE_THRESHOLD_LOCAL:
                                    label = predicted_label.upper()

                                    # Evitar duplicar la misma palabra
                                    # de manera consecutiva.
                                    if not sentence or sentence[-1] != predicted_label:
                                        sentence.append(predicted_label)

                                    print(
                                        f"Predicción: {predicted_label} "
                                        f"({confidence:.1%})"
                                    )
                                else:
                                    label = "SEÑA NO RECONOCIDA"
                                    print(
                                        f"Confianza insuficiente: "
                                        f"{confidence:.1%}"
                                    )

                            except Exception as error:
                                label = "ERROR EN LA PREDICCIÓN"
                                print(f"Error procesando la seña: {error}")

                        else:
                            label = "SEÑA DEMASIADO CORTA"

                        sequence = []
                        total_frames = 0
                        empty_frames = 0

                # Mostrar el estado de captura y la última predicción.
                if recording:
                    display_label = "CAPTURANDO SEÑA..."
                    color = (0, 200, 255)
                elif label == "ESPERANDO UNA SEÑA":
                    display_label = label
                    color = (180, 180, 180)
                elif label in ("SEÑA NO RECONOCIDA", "SEÑA DEMASIADO CORTA"):
                    display_label = label
                    color = (0, 165, 255)
                else:
                    display_label = label
                    color = (0, 255, 0)

                put_text(
                    frame,
                    "GESTOSVISION - RECONOCIMIENTO",
                    30,
                    (0, 255, 255),
                )

                put_text(
                    frame,
                    f"Sena: {display_label}",
                    70,
                    color,
                    0.85,
                )

                put_text(
                    frame,
                    f"Confianza: {confidence:.0%}",
                    105,
                )

                put_text(
                    frame,
                    f"Fotogramas capturados: {total_frames}",
                    135,
                )

                put_text(
                    frame,
                    f"Mano izquierda: {'SI' if left_detected else 'NO'}",
                    165,
                )

                put_text(
                    frame,
                    f"Mano derecha: {'SI' if right_detected else 'NO'}",
                    195,
                )

                history_text = " - ".join(sentence)
                put_text(
                    frame,
                    f"Historial: {history_text}"[-80:],
                    230,
                    (0, 255, 0),
                    0.55,
                )

                put_text(
                    frame,
                    "Q/ESC: salir | C: limpiar",
                    frame.shape[0] - 15,
                    (255, 255, 255),
                    0.55,
                )

                cv2.imshow("GESTOSVISION - Reconocimiento", frame)

                key = cv2.waitKey(1) & 0xFF

                if key in (ord("q"), 27):
                    break

                if key == ord("c"):
                    sentence.clear()
                    label = "ESPERANDO UNA SEÑA"
                    confidence = 0.0

    except KeyboardInterrupt:
        print("\nReconocimiento interrumpido.")

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print("Reconocimiento finalizado.")


if __name__ == "__main__":
    main()
