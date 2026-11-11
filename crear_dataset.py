
from pathlib import Path

import cv2
import numpy as np

from config import DATA_DIR
from model import create_holistic, extract_features


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

SEQUENCES_DIR = Path(DATA_DIR) / "secuencias_originales"
OUTPUT_FILE = Path(DATA_DIR) / "dataset.npz"

CLASSES_FILE = Path(DATA_DIR) / "clases_procesadas.txt"
PROCESSED_FILE = Path(DATA_DIR) / "secuencias_procesadas.txt"

MAX_LENGTH_FRAMES = 30
FEATURE_COUNT = 126
MIN_FRAMES = 5


# ==========================================================
# DETECTAR CLASES DISPONIBLES
# ==========================================================

def detectar_clases():
    """Detecta las carpetas que contienen al menos un frames.npy."""

    if not SEQUENCES_DIR.exists():
        return []

    classes = []

    for folder in sorted(SEQUENCES_DIR.iterdir()):
        if not folder.is_dir():
            continue

        if any(folder.rglob("frames.npy")):
            classes.append(folder.name)
        else:
            print(
                f"[AVISO] '{folder.name}' no tiene secuencias."
            )

    return classes


# ==========================================================
# PROCESAMIENTO DE FOTOGRAMAS
# ==========================================================

def procesar_fotograma(frame, holistic):
    """Extrae las 126 características de las manos."""

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb.flags.writeable = False

    results = holistic.process(rgb)

    features = np.asarray(
        extract_features(results),
        dtype=np.float32
    ).reshape(-1)

    if features.size != FEATURE_COUNT:
        raise ValueError(
            f"Se esperaban {FEATURE_COUNT} características, "
            f"pero se obtuvieron {features.size}."
        )

    return features


def ajustar_longitud(sequence):
    """Reduce o amplía la secuencia a 30 fotogramas."""

    sequence = np.asarray(sequence, dtype=np.float32)

    if len(sequence) == 0:
        return None

    indices = np.linspace(
        0,
        len(sequence) - 1,
        MAX_LENGTH_FRAMES
    ).astype(int)

    return sequence[indices]


# ==========================================================
# CARGAR REGISTRO DE SECUENCIAS
# ==========================================================

def cargar_secuencias_procesadas():
    if not PROCESSED_FILE.exists():
        return set()

    with open(PROCESSED_FILE, "r", encoding="utf-8") as file:
        return {
            line.strip()
            for line in file
            if line.strip()
        }


def guardar_registros(class_names, processed_sequences):
    """Guarda los registros de clases y secuencias."""

    CLASSES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CLASSES_FILE, "w", encoding="utf-8") as file:
        for name in class_names:
            file.write(name + "\n")

    with open(PROCESSED_FILE, "w", encoding="utf-8") as file:
        for sequence_path in sorted(processed_sequences):
            file.write(sequence_path + "\n")


# ==========================================================
# CARGAR DATASET EXISTENTE
# ==========================================================

def cargar_dataset():
    if not OUTPUT_FILE.exists():
        return (
            np.empty((0, MAX_LENGTH_FRAMES, FEATURE_COUNT),
                     dtype=np.float32),
            np.empty((0,), dtype=np.int64),
            []
        )

    with np.load(OUTPUT_FILE, allow_pickle=False) as data:
        X = data["X"].astype(np.float32)
        y = data["y"].astype(np.int64)
        class_names = data["class_names"].astype(str).tolist()

    if X.ndim != 3 or X.shape[1:] != (
        MAX_LENGTH_FRAMES,
        FEATURE_COUNT
    ):
        raise ValueError(
            "El dataset existente tiene una forma incompatible."
        )

    if len(X) != len(y):
        raise ValueError(
            "El dataset tiene cantidades distintas de X e y."
        )

    if len(y) and (y.min() < 0 or y.max() >= len(class_names)):
        raise ValueError(
            "El dataset contiene etiquetas que no corresponden "
            "a class_names."
        )

    return X, y, class_names


# ==========================================================
# PROCESAR UNA SECUENCIA NUEVA
# ==========================================================

def procesar_secuencia(file, holistic):
    frames = np.load(file, allow_pickle=False)

    if (
        frames.ndim != 4
        or frames.shape[-1] != 3
        or len(frames) < MIN_FRAMES
    ):
        raise ValueError(
            "Formato incorrecto o menos de "
            f"{MIN_FRAMES} fotogramas."
        )

    features_sequence = []

    for frame in frames:
        features_sequence.append(
            procesar_fotograma(frame, holistic)
        )

    sequence = ajustar_longitud(features_sequence)

    if sequence is None:
        raise ValueError("La secuencia está vacía.")

    return sequence, len(frames)


# ==========================================================
# CREAR O ACTUALIZAR DATASET
# ==========================================================

def main():
    print("\n" + "=" * 55)
    print("GESTOSVISION - ACTUALIZACIÓN INCREMENTAL DEL DATASET")
    print("=" * 55)

    if not SEQUENCES_DIR.exists():
        print(f"[ERROR] No existe la carpeta:\n{SEQUENCES_DIR}")
        return

    detected_classes = detectar_clases()

    if not detected_classes:
        print("[ERROR] No hay clases con secuencias.")
        return

    # Si hay un dataset antiguo sin registro de secuencias,
    # no podemos saber qué muestras contiene. Se reconstruye
    # una sola vez para crear un registro fiable.
    rebuild = (
        OUTPUT_FILE.exists()
        and not PROCESSED_FILE.exists()
    )

    if rebuild:
        print(
            "\n[AVISO] Existe un dataset, pero no el registro "
            "de secuencias."
        )
        print(
            "Se reconstruirá una vez para evitar duplicados "
            "y crear el registro incremental."
        )

    if rebuild:
        X = np.empty(
            (0, MAX_LENGTH_FRAMES, FEATURE_COUNT),
            dtype=np.float32
        )
        y = np.empty((0,), dtype=np.int64)
        class_names = []
        processed_sequences = set()
    else:
        try:
            X, y, class_names = cargar_dataset()
        except Exception as error:
            print(f"[ERROR] No se pudo cargar el dataset: {error}")
            print("No se modificaron los archivos.")
            return

        processed_sequences = cargar_secuencias_procesadas()

        if not OUTPUT_FILE.exists():
            # No hay dataset que corresponda al registro anterior.
            processed_sequences.clear()
            class_names = []

    # Mantener los IDs existentes. Las clases nuevas se agregan
    # al final; nunca se reordenan las clases anteriores.
    new_classes = [
        name for name in detected_classes
        if name not in class_names
    ]

    if new_classes:
        print("\nClases nuevas detectadas:")

        for name in new_classes:
            print(f"  + {name}")

        class_names.extend(new_classes)
    else:
        print("\nNo se detectaron clases nuevas.")

    class_to_id = {
        name: index
        for index, name in enumerate(class_names)
    }

    # Buscar muestras aún no procesadas.
    pending = []

    for class_name in class_names:
        class_dir = SEQUENCES_DIR / class_name

        if not class_dir.exists():
            continue

        for file in sorted(class_dir.rglob("frames.npy")):
            relative_path = file.relative_to(
                SEQUENCES_DIR
            ).as_posix()

            if relative_path not in processed_sequences:
                pending.append(
                    (class_name, file, relative_path)
                )

    print(f"\nClases registradas: {len(class_names)}")
    print(f"Secuencias nuevas por procesar: {len(pending)}")
    print(f"Secuencias ya registradas: {len(processed_sequences)}")

    if not pending:
        guardar_registros(class_names, processed_sequences)
        print("\nEl dataset ya está actualizado.")
        print(f"Registro de clases: {CLASSES_FILE}")
        print(f"Registro de secuencias: {PROCESSED_FILE}")
        return

    new_X = []
    new_y = []
    successfully_processed = []
    rejected_count = 0

    try:
        with create_holistic() as holistic:
            for class_name, file, relative_path in pending:
                print(f"\n[{class_name}] {file.parent.name}")

                try:
                    sequence, original_frames = procesar_secuencia(
                        file,
                        holistic
                    )

                    new_X.append(sequence)
                    new_y.append(class_to_id[class_name])
                    successfully_processed.append(relative_path)

                    print(
                        f"  [OK] {original_frames} fotogramas "
                        "convertidos a 30."
                    )

                except Exception as error:
                    rejected_count += 1
                    print(f"  [ERROR] {error}")

    except Exception as error:
        print(f"\n[ERROR] No se pudo iniciar MediaPipe: {error}")
        return

    if not new_X:
        print("\nNo se procesaron secuencias nuevas válidas.")
        print("El dataset anterior se conserva.")
        return

    # Incorporar las secuencias nuevas a las anteriores.
    new_X = np.asarray(new_X, dtype=np.float32)
    new_y = np.asarray(new_y, dtype=np.int64)

    updated_X = np.concatenate((X, new_X), axis=0)
    updated_y = np.concatenate((y, new_y), axis=0)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Guardar primero el dataset completo actualizado.
    temporary_file = OUTPUT_FILE.with_name(
        OUTPUT_FILE.stem + "_temporal.npz"
    )

    try:
        np.savez_compressed(
            temporary_file,
            X=updated_X,
            y=updated_y,
            class_names=np.asarray(class_names)
        )

        temporary_file.replace(OUTPUT_FILE)

    except Exception as error:
        if temporary_file.exists():
            temporary_file.unlink()

        print(f"\n[ERROR] No se pudo guardar el dataset: {error}")
        print("El registro no se actualizará.")
        return

    # Registrar solo las secuencias incorporadas correctamente.
    processed_sequences.update(successfully_processed)

    guardar_registros(class_names, processed_sequences)

    # ======================================================
    # RESUMEN
    # ======================================================

    print("\n" + "=" * 55)
    print("DATASET ACTUALIZADO")
    print("=" * 55)

    print(f"Archivo: {OUTPUT_FILE}")
    print(f"Nuevas muestras incorporadas: {len(new_X)}")
    print(f"Muestras rechazadas: {rejected_count}")
    print(f"Total de muestras: {len(updated_X)}")
    print(f"Forma de X: {updated_X.shape}")
    print(f"Forma de y: {updated_y.shape}")

    print("\nClases y cantidad total de muestras:")

    for class_id, class_name in enumerate(class_names):
        count = int(np.sum(updated_y == class_id))
        print(f"  {class_id}: {class_name} = {count}")

    print(f"\nRegistro de clases: {CLASSES_FILE}")
    print(f"Registro de secuencias: {PROCESSED_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    main()
