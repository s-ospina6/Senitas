
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
import re

from config import DATA_DIR
from model import create_holistic, open_camera, draw_hands


print("Python utilizado:", sys.executable)
print("OpenCV:", cv2.__file__)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

FRAME_ACTIONS_PATH = Path(DATA_DIR) / "secuencias_originales"

MIN_CANT_FRAMES = 5
DELAY_FRAMES = 10
MAX_EMPTY_FRAMES = 30
MAX_FRAMES = 300


# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def create_folder(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def mediapipe_detection(frame, holistic_model):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image.flags.writeable = False
    results = holistic_model.process(image)
    image.flags.writeable = True
    return results


def there_hand(results):
    return (
        results.left_hand_landmarks is not None
        or results.right_hand_landmarks is not None
    )


def put_text(frame, text, position, color=(255, 255, 255)):
    cv2.putText(
        frame,
        text,
        position,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        color,
        2,
        cv2.LINE_AA,
    )


def save_frames(frames, output_folder):
    output_folder = Path(output_folder)
    create_folder(output_folder)

    saved_count = 0

    for index, frame in enumerate(frames):
        filename = output_folder / f"frame_{index:04d}.jpg"

        if cv2.imwrite(str(filename), frame):
            saved_count += 1

    np.save(
        output_folder / "frames.npy",
        np.asarray(frames, dtype=np.uint8),
    )

    print(
        f"\nMuestra guardada: {output_folder}"
        f"\nFotogramas: {len(frames)}"
        f"\nImágenes JPG guardadas: {saved_count}"
    )


def get_sample_folder(label_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return label_path / f"sample_{timestamp}"


# ==========================================================
# CAPTURA DE SECUENCIAS
# ==========================================================

def capture_samples(label):
    label_path = FRAME_ACTIONS_PATH / label
    create_folder(label_path)

    frames = []
    empty_frames = 0
    sample_count = 0

    try:
        video = open_camera()
    except RuntimeError as error:
        print(f"Error al abrir la cámara: {error}")
        return

    try:
        with create_holistic() as holistic_model:

            print(f"\nCLASE SELECCIONADA: {label}")
            print(f"Carpeta: {label_path}")
            print("\nInstrucciones:")
            print("1. Haz el gesto frente a la cámara.")
            print("2. Mantén las manos visibles mientras haces el gesto.")
            print("3. Retira las manos para guardar la muestra.")
            print("4. Repite para registrar más muestras.")
            print("Q: salir de la captura.\n")

            while video.isOpened():
                ret, frame = video.read()

                if not ret:
                    print("No se pudo leer un fotograma.")
                    break

                frame = cv2.flip(frame, 1)

                results = mediapipe_detection(
                    frame,
                    holistic_model
                )

                hand_detected = there_hand(results)
                display = frame.copy()

                if hand_detected:
                    frames.append(frame.copy())
                    empty_frames = 0

                    put_text(
                        display,
                        f"CLASE: {label}",
                        (10, 30),
                        (0, 255, 0),
                    )

                    put_text(
                        display,
                        f"CAPTURANDO: {len(frames)}",
                        (10, 60),
                        (0, 0, 255),
                    )

                elif len(frames) > 0:
                    empty_frames += 1

                    put_text(
                        display,
                        f"RETIRA LAS MANOS: "
                        f"{empty_frames}/{DELAY_FRAMES}",
                        (10, 30),
                        (0, 220, 255),
                    )

                    if empty_frames >= DELAY_FRAMES:

                        if len(frames) >= MIN_CANT_FRAMES:
                            output_folder = get_sample_folder(label_path)

                            save_frames(frames, output_folder)
                            sample_count += 1

                        else:
                            print(
                                f"Muestra descartada: "
                                f"{len(frames)} fotogramas."
                            )

                        frames = []
                        empty_frames = 0

                else:
                    put_text(
                        display,
                        f"CLASE: {label}",
                        (10, 30),
                        (0, 255, 0),
                    )

                    put_text(
                        display,
                        f"MUESTRAS GUARDADAS: {sample_count}",
                        (10, 60),
                        (255, 255, 255),
                    )

                draw_hands(display, results)

                put_text(
                    display,
                    "Retira las manos para guardar | Q: salir",
                    (10, display.shape[0] - 20),
                )

                cv2.imshow(f"Captura: {label}", display)

                # Guardar automáticamente si se alcanza el máximo.
                if len(frames) >= MAX_FRAMES:
                    output_folder = get_sample_folder(label_path)
                    save_frames(frames, output_folder)
                    sample_count += 1

                    frames = []
                    empty_frames = 0

                if cv2.waitKey(10) & 0xFF == ord("q"):

                    # Guardar cualquier muestra pendiente.
                    if len(frames) >= MIN_CANT_FRAMES:
                        output_folder = get_sample_folder(label_path)
                        save_frames(frames, output_folder)
                        sample_count += 1

                    break

    except KeyboardInterrupt:
        print("\nCaptura interrumpida.")

    finally:
        video.release()
        cv2.destroyAllWindows()

    print("\nCAPTURA FINALIZADA")
    print(f"Palabra o letra: {label}")
    print(f"Muestras guardadas: {sample_count}")
    print(f"Directorio: {label_path}")


# ==========================================================
# MENÚ PRINCIPAL
# ==========================================================

def main():
    create_folder(FRAME_ACTIONS_PATH)

    print("\n====================================")
    print(" GESTOSVISION - CAPTURA DE SEÑAS")
    print("====================================")
    print("Escribe la letra o palabra que quieras registrar.")
    print("Ejemplos: hola, gracias, a, b, buenos_dias")
    print("Escribe SALIR para terminar.")

    while True:
        label = input("\nLetra o palabra: ").strip().lower()

        if label == "salir":
            print("Programa finalizado.")
            break

        # Permitir letras, números, guiones y guiones bajos.
        # Evitar espacios y caracteres que puedan crear rutas inválidas.
        if not label or not re.fullmatch(
            r"[a-záéíóúüñ0-9_-]+",
            label
        ):
            print(
                "Nombre inválido. Usa letras, números, "
                "guiones o guiones bajos."
            )
            continue

        label_path = FRAME_ACTIONS_PATH / label

        if label_path.exists() and any(label_path.iterdir()):
            print(
                f"Ya existen datos para '{label}'. "
                "Se agregarán nuevas muestras a esa clase."
            )

        capture_samples(label)


if __name__ == "__main__":
    main()
