
from pathlib import Path

# Directorio principal del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Carpetas de datos y modelos
DATA_DIR = BASE_DIR / "datos"
MODEL_DIR = BASE_DIR / "modelos"

# Archivos generados
RAW_DATA_FILE = DATA_DIR / "muestras.csv"
DATASET_FILE = DATA_DIR / "dataset.npz"
MODEL_FILE = MODEL_DIR / "clasificador.joblib"

# Crear carpetas si todavía no existen
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Clases disponibles
LABELS = {
    "1": "hola",
    "2": "gracias",
    "3": "si",
    "4": "no",
    "5": "ninguna",
}

# Configuración de la cámara
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Configuración de MediaPipe Holistic
MODEL_COMPLEXITY = 1
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Cada mano tiene 21 puntos, con coordenadas x, y, z.
LANDMARKS_PER_HAND = 21
COORDINATES_PER_LANDMARK = 3
FEATURES_PER_HAND = LANDMARKS_PER_HAND * COORDINATES_PER_LANDMARK

# Dos manos: 63 características por mano, 126 en total.
FEATURE_COUNT = FEATURES_PER_HAND * 2

# Confianza mínima para mostrar una predicción.
CONFIDENCE_THRESHOLD = 0.55
