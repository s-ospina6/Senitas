
import cv2
import numpy as np

from keras.models import Sequential
from keras.layers import Input, LSTM, Dense, Dropout
from keras.regularizers import l2

from config import (
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    MODEL_COMPLEXITY,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    FEATURE_COUNT,
)


def get_model(max_length_frames: int, output_length: int):
    model = Sequential([
        Input(shape=(max_length_frames, FEATURE_COUNT)),
        LSTM(64, return_sequences=True, kernel_regularizer=l2(0.01)),
        Dropout(0.5),
        LSTM(128, return_sequences=False, kernel_regularizer=l2(0.001)),
        Dropout(0.5),
        Dense(64, activation="relu", kernel_regularizer=l2(0.001)),
        Dense(64, activation="relu", kernel_regularizer=l2(0.001)),
        Dense(output_length, activation="softmax"),
    ])

    model.compile(
        optimizer="adam",
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def create_holistic():
    from mediapipe.python.solutions.holistic import Holistic

    return Holistic(
        static_image_mode=False,
        model_complexity=MODEL_COMPLEXITY,
        smooth_landmarks=True,
        enable_segmentation=False,
        refine_face_landmarks=False,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
        min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
    )


def open_camera():
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)

    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        camera.release()
        raise RuntimeError("No se pudo abrir la cámara.")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    camera.set(
        cv2.CAP_PROP_FOURCC,
        cv2.VideoWriter_fourcc(*"MJPG"),
    )
    return camera


def _hand_features(hand_landmarks):
    if hand_landmarks is None:
        return np.zeros(63, dtype=np.float32)

    points = np.array(
        [[p.x, p.y, p.z] for p in hand_landmarks.landmark],
        dtype=np.float32,
    )

    points -= points[0].copy()

    scale = np.max(np.abs(points))
    if scale > 1e-6:
        points /= scale

    return points.flatten().astype(np.float32)


def extract_features(results):
    left = _hand_features(results.left_hand_landmarks)
    right = _hand_features(results.right_hand_landmarks)

    return np.concatenate([left, right]).astype(np.float32)


def draw_hands(frame, results):
    from mediapipe.python.solutions import drawing_utils
    from mediapipe.python.solutions.holistic import HAND_CONNECTIONS

    if results.left_hand_landmarks:
        drawing_utils.draw_landmarks(
            frame,
            results.left_hand_landmarks,
            HAND_CONNECTIONS,
        )

    if results.right_hand_landmarks:
        drawing_utils.draw_landmarks(
            frame,
            results.right_hand_landmarks,
            HAND_CONNECTIONS,
        )
