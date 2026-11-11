
import subprocess
import sys
from pathlib import Path


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent


# ==========================================================
# OPCIONES DEL MENÚ
# ==========================================================

OPCIONES = {
    "1": ("Reconocer señas", "reconocer_senas.py"),
    "2": ("Capturar datos", "capturar_datos.py"),
    "3": ("Crear dataset", "crear_dataset.py"),
    "4": ("Entrenar modelo", "entrenar_modelo.py"),
    "5": ("Administrar dataset", "administrar_dataset.py"),
    "6": ("Modo práctica", "modo_practica.py"),
    "7": ("Modo aprendizaje", "modo_aprendizaje.py"),
}


# ==========================================================
# MOSTRAR MENÚ
# ==========================================================

def mostrar_menu():

    while True:
        print("\n" + "=" * 45)
        print("          GESTOSVISION")
        print("=" * 45)

        for numero, (nombre, _) in OPCIONES.items():
            print(f"  {numero}. {nombre}")

        print("  0. Salir")
        print("=" * 45)

        opcion = input("Selecciona una opción: ").strip()

        # --------------------------------------------------
        # Salir
        # --------------------------------------------------

        if opcion == "0":
            print("\nCerrando GESTOSVISION...")
            break

        # --------------------------------------------------
        # Validar opción
        # --------------------------------------------------

        if opcion not in OPCIONES:
            print("\nOpción no válida. Intenta nuevamente.")
            continue

        nombre, archivo = OPCIONES[opcion]
        ruta = BASE_DIR / archivo

        # --------------------------------------------------
        # Verificar existencia del archivo
        # --------------------------------------------------

        if not ruta.is_file():
            print(f"\nError: no se encontró el archivo:")
            print(f"  {ruta}")

            input("\nPresiona Enter para volver al menú...")
            continue

        # --------------------------------------------------
        # Ejecutar programa seleccionado
        # --------------------------------------------------

        print("\n" + "-" * 45)
        print(f"Iniciando: {nombre}")
        print("-" * 45 + "\n")

        try:
            resultado = subprocess.run(
                [sys.executable, str(ruta)],
                cwd=BASE_DIR,
            )

            if resultado.returncode != 0:
                print(
                    f"\nEl programa terminó con código "
                    f"{resultado.returncode}."
                )

        except KeyboardInterrupt:
            print("\nPrograma interrumpido.")

        except Exception as error:
            print(f"\nError al ejecutar el programa: {error}")

        # --------------------------------------------------
        # Regresar al menú
        # --------------------------------------------------

        input("\nPresiona Enter para volver al menú...")


# ==========================================================
# INICIO
# ==========================================================

if __name__ == "__main__":
    try:
        mostrar_menu()
    except KeyboardInterrupt:
        print("\n\nGESTOSVISION cerrado.")

