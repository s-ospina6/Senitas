
import numpy as np
from pathlib import Path
from collections import Counter

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

from config import DATA_DIR, MODEL_DIR
from model import get_model


# Configuración del entrenamiento.
DATASET_FILE = DATA_DIR / "dataset.npz"
MODEL_FILE = MODEL_DIR / "gestos_lstm.keras"

EPOCHS = 100
BATCH_SIZE = 8
RANDOM_STATE = 42


def main():
    if not DATASET_FILE.exists():
        print("ERROR: no existe el dataset.")
        print("Ejecuta primero crear_dataset.py.")
        return

    with np.load(DATASET_FILE, allow_pickle=False) as data:
        X = data["X"].astype(np.float32)
        y = data["y"].astype(np.int64)
        class_names = (
            data["class_names"].astype(str).tolist()
            if "class_names" in data.files
            else sorted(set(y.tolist()))
        )

    # Validar la forma esperada por la LSTM.
    if X.ndim != 3 or X.shape[1:] != (30, 126):
        print("ERROR: dimensiones incorrectas para la LSTM.")
        print("Forma recibida:", X.shape)
        print("Forma esperada: (muestras, 30, 126)")
        return

    if len(X) != len(y) or len(X) == 0:
        print("ERROR: X e y están vacíos o no coinciden.")
        return

    if not np.isfinite(X).all():
        print("ERROR: el dataset contiene NaN o valores infinitos.")
        return

    counts = Counter(y.tolist())
    classes = sorted(counts)

    print("\nGESTOSVISION - ENTRENAMIENTO LSTM")
    print("-" * 40)
    print("Muestras:", len(X))
    print("Forma de X:", X.shape)
    print("Clases:", class_names)

    for class_id in classes:
        name = (
            class_names[class_id]
            if 0 <= class_id < len(class_names)
            else str(class_id)
        )
        print(f"  {name}: {counts[class_id]} muestras")

    if len(classes) < 2:
        print("ERROR: necesitas al menos dos clases distintas.")
        return

    # Una división estratificada necesita al menos dos ejemplos
    # por clase, y más ejemplos mejoran la evaluación.
    if min(counts.values()) < 2:
        print("ERROR: cada clase necesita al menos 2 muestras.")
        print("Es recomendable reunir bastantes más.")
        return

    test_fraction = max(0.20, len(classes) / len(y))

    if test_fraction >= 0.5:
        print("ERROR: hay muy pocas muestras para separar")
        print("entrenamiento y prueba de forma fiable.")
        return

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_fraction,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print("\nMuestras para entrenar:", len(X_train))
    print("Muestras para evaluar:", len(X_test))

    # Crear modelo LSTM compatible con secuencias temporales.
    classifier = get_model(
        max_length_frames=X.shape[1],
        output_length=len(class_names),
    )

    classifier.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    print("\nEntrenando modelo...")

    classifier.fit(
        X_train,
        y_train,
        validation_data=(X_test, y_test),
        epochs=EPOCHS,
        batch_size=min(BATCH_SIZE, len(X_train)),
        verbose=1,
        shuffle=True,
    )

    # Evaluar el modelo con las muestras separadas.
    probabilities = classifier.predict(X_test, verbose=0)
    predictions = np.argmax(probabilities, axis=1)

    accuracy = accuracy_score(y_test, predictions)

    print(f"\nExactitud de prueba: {accuracy:.2%}")
    print("\nReporte de clasificación:")

    print(
        classification_report(
            y_test,
            predictions,
            labels=classes,
            target_names=[
                class_names[i]
                if 0 <= i < len(class_names)
                else str(i)
                for i in classes
            ],
            zero_division=0,
        )
    )

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    classifier.save(MODEL_FILE)

    # Guardar metadatos para que el reconocedor sepa
    # qué significa cada índice de salida.
    metadata_file = MODEL_DIR / "gestos_lstm_labels.npz"

    np.savez(
        metadata_file,
        class_names=np.asarray(class_names),
        feature_count=np.asarray([X.shape[2]]),
        sequence_length=np.asarray([X.shape[1]]),
    )

    print("\nENTRENAMIENTO FINALIZADO")
    print("Modelo guardado en:", MODEL_FILE)
    print("Clases guardadas en:", metadata_file)
    print(
        "\nNota: la exactitud se calcula con una partición "
        "pequeña del dataset; no garantiza el mismo resultado "
        "con personas, cámaras o condiciones diferentes."
    )


if __name__ == "__main__":
    main()
