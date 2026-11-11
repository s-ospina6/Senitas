
from pathlib import Path

import cv2


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "imagenes_aprendizaje"

EXTENSIONS = (".jpg", ".jpeg", ".png")


# ==========================================================
# FUNCIONES
# ==========================================================

def buscar_imagen(nombre):
    """Busca una imagen por letra o palabra."""

    nombre = nombre.strip()

    if not nombre:
        return None

    nombre = Path(nombre).stem.casefold()

    if not IMAGE_DIR.exists():
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    for archivo in IMAGE_DIR.iterdir():
        if (
            archivo.is_file()
            and archivo.suffix.lower() in EXTENSIONS
            and archivo.stem.casefold() == nombre
        ):
            return archivo

    return None


def mostrar_imagen(nombre):
    """Muestra la imagen y permite cerrarla con ESC."""

    archivo = buscar_imagen(nombre)

    if archivo is None:
        print(f"No se encontró la imagen de '{nombre}'.")
        return

    imagen = cv2.imread(str(archivo))

    if imagen is None:
        print(f"No se pudo abrir: {archivo.name}")
        return

    ventana = "GESTOSVISION - APRENDIZAJE"

    try:
        cv2.namedWindow(ventana, cv2.WINDOW_NORMAL)
        cv2.imshow(ventana, imagen)

        print("Imagen mostrada. Presiona ESC o Q en la ventana para continuar.")

        while True:
            tecla = cv2.waitKey(30) & 0xFF

            # Cerrar la imagen con ESC o Q.
            if tecla in (27, ord("q")):
                break

            # Detectar si la ventana fue cerrada con la X.
            try:
                if cv2.getWindowProperty(
                    ventana,
                    cv2.WND_PROP_VISIBLE,
                ) < 1:
                    break
            except cv2.error:
                break

    finally:
        cv2.destroyAllWindows()

        # Permitir que OpenCV procese el cierre de ventanas.
        cv2.waitKey(1)


def mostrar_lista():
    """Lista las imágenes que existen actualmente."""

    if not IMAGE_DIR.exists():
        IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    imagenes = sorted(
        [
            archivo.stem
            for archivo in IMAGE_DIR.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower() in EXTENSIONS
        ],
        key=str.casefold,
    )

    if imagenes:
        print("Señas disponibles:", ", ".join(imagenes))
    else:
        print("No hay imágenes en imagenes_aprendizaje.")


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    print("\n========================================")
    print("    GESTOSVISION - MODO APRENDIZAJE")
    print("========================================")

    mostrar_lista()

    print("\nEscribe una letra o palabra.")
    print("Comandos: lista | salir")

    while True:
        try:
            comando = input("\n¿Qué seña deseas aprender?: ").strip()

            if comando.casefold() in ("salir", "exit"):
                break

            if comando.casefold() in ("lista", "listar"):
                mostrar_lista()
                continue

            if not comando:
                continue

            mostrar_imagen(comando)

        except KeyboardInterrupt:
            print("\nSaliendo del modo aprendizaje.")
            break

    cv2.destroyAllWindows()
    print("Modo aprendizaje finalizado.")


if __name__ == "__main__":
    main()
