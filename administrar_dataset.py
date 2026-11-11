
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

MAX_LENGTH_FRAMES = 30
FEATURE_COUNT = 126
MIN_FRAMES = 5


# ==========================================================
# DETECTAR CLASES
# ==========================================================

def detectar_clases():
    if not SEQUENCES_DIR.exists():
        return []

    clases = []

    for carpeta in sorted(SEQUENCES_DIR.iterdir()):
        if not carpeta.is_dir():
            continue

        if any(carpeta.rglob("frames.npy")):
            clases.append(carpeta.name)

    return clases


def contar_secuencias(carpeta):
    return sum(1 for _ in carpeta.rglob("frames.npy"))


# ==========================================================
# PROCESAMIENTO DE MEDIA PIPE
# ==========================================================

def procesar_fotograma(frame, holistic):
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
    sequence = np.asarray(sequence, dtype=np.float32)

    if len(sequence) == 0:
        return None

    indices = np.linspace(
        0,
        len(sequence) - 1,
        MAX_LENGTH_FRAMES
    ).astype(int)

    return sequence[indices]


def procesar_secuencia(archivo, holistic):
    frames = np.load(archivo, allow_pickle=False)

    if (
        frames.ndim != 4
        or frames.shape[-1] != 3
        or len(frames) < MIN_FRAMES
    ):
        raise ValueError(
            "Formato incorrecto o menos de "
            f"{MIN_FRAMES} fotogramas."
        )

    caracteristicas = []

    for frame in frames:
        caracteristicas.append(
            procesar_fotograma(frame, holistic)
        )

    sequence = ajustar_longitud(caracteristicas)

    if sequence is None:
        raise ValueError("Secuencia vacía.")

    return sequence


# ==========================================================
# GUARDAR DATASET DE FORMA SEGURA
# ==========================================================

def guardar_dataset(X, y, class_names):
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    temporal = OUTPUT_FILE.with_name(
        OUTPUT_FILE.stem + "_temporal.npz"
    )

    try:
        np.savez_compressed(
            temporal,
            X=np.asarray(
                X,
                dtype=np.float32
            ).reshape(-1, MAX_LENGTH_FRAMES, FEATURE_COUNT),
            y=np.asarray(y, dtype=np.int64),
            class_names=np.asarray(class_names, dtype=str)
        )

        # Reemplazar el dataset anterior solo después
        # de generar correctamente el archivo nuevo.
        temporal.replace(OUTPUT_FILE)

    finally:
        if temporal.exists():
            temporal.unlink()


# ==========================================================
# ACTUALIZAR TODO EL DATASET
# ==========================================================

def actualizar_dataset():
    print("\n" + "=" * 50)
    print("ACTUALIZACIÓN COMPLETA DEL DATASET")
    print("=" * 50)

    if not SEQUENCES_DIR.exists():
        print(f"[ERROR] No existe:\n{SEQUENCES_DIR}")
        return

    class_names = detectar_clases()

    print(f"Clases encontradas: {len(class_names)}")

    for class_name in class_names:
        carpeta = SEQUENCES_DIR / class_name
        print(
            f"  - {class_name}: "
            f"{contar_secuencias(carpeta)} secuencias"
        )

    X = []
    y = []
    rechazadas = 0

    # Reconstruir desde cero: no reutilizar datos anteriores.
    try:
        with create_holistic() as holistic:

            for class_id, class_name in enumerate(class_names):
                carpeta = SEQUENCES_DIR / class_name
                archivos = sorted(
                    carpeta.rglob("frames.npy")
                )

                print(
                    f"\nProcesando '{class_name}' "
                    f"({len(archivos)} secuencias)"
                )

                muestras_clase = 0

                for archivo in archivos:
                    try:
                        sequence = procesar_secuencia(
                            archivo,
                            holistic
                        )

                        X.append(sequence)
                        y.append(class_id)
                        muestras_clase += 1

                        print(
                            f"  [OK] {archivo.parent.name}"
                        )

                    except Exception as error:
                        rechazadas += 1
                        print(
                            f"  [ERROR] {archivo}: {error}"
                        )

                print(
                    f"Muestras válidas de '{class_name}': "
                    f"{muestras_clase}"
                )

    except Exception as error:
        print(f"\n[ERROR] Falló MediaPipe: {error}")
        print("El dataset anterior se conserva.")
        return

    # Si existen clases pero todas sus muestras fallaron,
    # evitar borrar un dataset anterior por accidente.
    if class_names and not X:
        print(
            "\n[ERROR] No se generaron muestras válidas."
        )
        print("El dataset anterior se conserva.")
        return

    try:
        guardar_dataset(X, y, class_names)
    except Exception as error:
        print(f"\n[ERROR] No se pudo guardar el dataset: {error}")
        print("Revisa el espacio disponible y los permisos.")
        return

    print("\n" + "=" * 50)
    print("DATASET ACTUALIZADO CORRECTAMENTE")
    print("=" * 50)

    print(f"Archivo: {OUTPUT_FILE}")
    print(f"Clases: {len(class_names)}")
    print(f"Muestras válidas: {len(X)}")
    print(f"Muestras rechazadas: {rechazadas}")
    print(
        f"Forma de X: "
        f"{(len(X), MAX_LENGTH_FRAMES, FEATURE_COUNT)}"
    )
    print(f"Forma de y: {(len(y),)}")

    print("\nEtiquetas:")

    for class_id, class_name in enumerate(class_names):
        total = int(np.sum(np.asarray(y) == class_id))
        print(f"  {class_id}: {class_name} ({total} muestras)")

    print("=" * 50)


# ==========================================================
# VER CLASES DEL DATASET ACTUAL
# ==========================================================

def ver_clases():
    if not OUTPUT_FILE.exists():
        print("\nTodavía no existe dataset.npz.")
        print("Primero selecciona actualizar el dataset.")
        return

    try:
        with np.load(OUTPUT_FILE, allow_pickle=False) as data:
            X = data["X"]
            y = data["y"]
            class_names = data["class_names"].astype(str)

        print("\nCLASES DEL DATASET ACTUAL")

        for class_id, name in enumerate(class_names):
            total = int(np.sum(y == class_id))
            print(f"  {class_id}: {name} — {total} muestras")

        print(f"\nTotal de muestras: {len(X)}")

    except Exception as error:
        print(f"No se pudo leer el dataset: {error}")


# ==========================================================
# ELIMINAR UNA CLASE Y SUS SECUENCIAS ORIGINALES
# ==========================================================


def eliminar_clase():
    if not SEQUENCES_DIR.exists():
        print("\nNo existe la carpeta de secuencias.")
        return

    clases = sorted(
        carpeta.name
        for carpeta in SEQUENCES_DIR.iterdir()
        if carpeta.is_dir()
    )

    if not clases:
        print("\nNo hay clases para eliminar.")
        return

    print("\nCLASES DISPONIBLES")

    for indice, nombre in enumerate(clases, start=1):
        print(f"  {indice}: {nombre}")

    opcion = input(
        "\nNúmero de la clase que quieres eliminar "
        "(Enter para cancelar): "
    ).strip()

    if not opcion:
        print("Operación cancelada.")
        return

    if not opcion.isdigit():
        print("Selección inválida.")
        return

    indice = int(opcion) - 1

    if indice < 0 or indice >= len(clases):
        print("Selección fuera de rango.")
        return

    nombre = clases[indice]
    carpeta = SEQUENCES_DIR / nombre

    print(f"\nVas a eliminar la clase: {nombre}")
    print(f"Se borrará únicamente esta carpeta:\n{carpeta}")
    print("Se eliminarán todas las secuencias de esta clase.")
    print("Las demás clases se conservarán.")

    confirmacion = input(
        f"\nEscribe ELIMINAR {nombre} para confirmar: "
    ).strip()

    if confirmacion != f"ELIMINAR {nombre}":
        print("Operación cancelada.")
        return

    import shutil

    try:
        if not carpeta.exists() or not carpeta.is_dir():
            print("La carpeta de la clase ya no existe.")
            return

        shutil.rmtree(carpeta)

    except OSError as error:
        print(f"No se pudo eliminar la clase: {error}")
        return

    print(f"\nClase '{nombre}' eliminada correctamente.")

    # Reconstruir el dataset sin la clase eliminada.
    actualizar_dataset()

def eliminar_clase():
    import shutil

    if not SEQUENCES_DIR.exists():
        print("\nNo existe la carpeta de secuencias.")
        return

    clases = sorted(
        carpeta.name
        for carpeta in SEQUENCES_DIR.iterdir()
        if carpeta.is_dir()
    )

    if not clases:
        print("\nNo hay clases para eliminar.")
        return

    print("\nCLASES DISPONIBLES")

    for indice, nombre in enumerate(clases, start=1):
        print(f"  {indice}: {nombre}")

    print("\nPuedes seleccionar varias clases separando")
    print("los números con comas. Ejemplo: 1,3,5")
    print("Presiona Enter para cancelar.")

    opcion = input(
        "\nNúmeros de las clases que quieres eliminar: "
    ).strip()

    if not opcion:
        print("Operación cancelada.")
        return

    # Convertir la selección en una lista de índices.
    try:
        indices = [
            int(numero.strip())
            for numero in opcion.split(",")
        ]
    except ValueError:
        print("Selección inválida. Usa números separados por comas.")
        return

    # Evitar entradas vacías, números repetidos o fuera de rango.
    if len(indices) != len(set(indices)):
        print("Hay números repetidos en la selección.")
        return

    if any(indice < 1 or indice > len(clases) for indice in indices):
        print("Uno o más números están fuera de rango.")
        return

    # Obtener los nombres de las clases seleccionadas.
    clases_eliminar = [clases[indice - 1] for indice in indices]

    print("\nCLASES QUE SE ELIMINARÁN")

    for nombre in clases_eliminar:
        print(f"  - {nombre}")

    print("\nSe eliminarán sus carpetas y todas sus secuencias.")
    print("Las demás clases se conservarán.")
    print("El dataset se actualizará una sola vez al finalizar.")

    confirmacion = input(
        "\nEscribe ELIMINAR para confirmar: "
    ).strip()

    if confirmacion != "ELIMINAR":
        print("Operación cancelada.")
        return

    # Eliminar las clases seleccionadas.
    eliminadas = []
    errores = []

    for nombre in clases_eliminar:
        carpeta = SEQUENCES_DIR / nombre

        try:
            if not carpeta.exists() or not carpeta.is_dir():
                print(f"\nNo se encontró la carpeta: {nombre}")
                errores.append(nombre)
                continue

            shutil.rmtree(carpeta)
            eliminadas.append(nombre)
            print(f"Clase '{nombre}' eliminada correctamente.")

        except OSError as error:
            print(f"\nError al eliminar '{nombre}': {error}")
            errores.append(nombre)

    # Actualizar el dataset una sola vez si hubo eliminaciones.
    if eliminadas:
        print("\nClases eliminadas:")
        for nombre in eliminadas:
            print(f"  - {nombre}")

        print("\nActualizando el dataset...")
        actualizar_dataset()

    else:
        print("\nNo se eliminó ninguna clase.")
        return

    if errores:
        print("\nNo se pudieron eliminar estas clases:")
        for nombre in errores:
            print(f"  - {nombre}")



# ==========================================================
# MENÚ PRINCIPAL
# ==========================================================

def main():
    while True:
        print("\n" + "=" * 50)
        print("GESTOSVISION - ADMINISTRADOR DEL DATASET")
        print("=" * 50)
        print("1. Actualizar todo el dataset")
        print("2. Ver clases del dataset")
        print("3. Eliminar una seña")
        print("4. Salir")

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            actualizar_dataset()

        elif opcion == "2":
            ver_clases()

        elif opcion == "3":
            eliminar_clase()

        elif opcion == "4":
            print("Programa finalizado.")
            break

        else:
            print("Opción inválida. Selecciona del 1 al 4.")


if __name__ == "__main__":
    main()
