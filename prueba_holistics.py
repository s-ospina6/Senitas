
import cv2
import mediapipe as mp
import sys

from mediapipe.python.solutions.holistic import Holistic
from mediapipe.python.solutions.drawing_utils import (
    draw_landmarks,
    DrawingSpec,
)
from mediapipe.python.solutions.holistic import (
    POSE_CONNECTIONS,
    HAND_CONNECTIONS,
    FACEMESH_CONTOURS,
)


def main():
    print("Python:", sys.version.split()[0])
    print("MediaPipe:", mp.__version__)
    print("Iniciando cámara...")

    # Abrir cámara principal
    camera = cv2.VideoCapture(0)

    if not camera.isOpened():
        print("Error: no se pudo abrir la cámara.")
        print("Prueba cambiar VideoCapture(0) por VideoCapture(1).")
        return

    # Solicitar una resolución reducida
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 30)

    # Consultar la configuración real de la cámara
    width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = camera.get(cv2.CAP_PROP_FPS)

    print(f"Resolución real: {width}x{height}")
    print(f"FPS reportados por la cámara: {fps:.1f}")
    print("Presiona Q o ESC para salir.")

    try:
        with Holistic(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            refine_face_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        ) as holistic:

            while True:
                success, frame = camera.read()

                if not success:
                    print("No se pudo leer la imagen de la cámara.")
                    break

                # Espejo para que el movimiento resulte natural
                frame = cv2.flip(frame, 1)

                # MediaPipe espera RGB en lugar de BGR
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                results = holistic.process(rgb)
                rgb.flags.writeable = True

                # Dibujar pose corporal
                if results.pose_landmarks:
                    draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        POSE_CONNECTIONS,
                    )

                # Dibujar mano izquierda
                if results.left_hand_landmarks:
                    draw_landmarks(
                        frame,
                        results.left_hand_landmarks,
                        HAND_CONNECTIONS,
                        DrawingSpec(
                            color=(255, 0, 0),
                            thickness=2,
                            circle_radius=3,
                        ),
                        DrawingSpec(
                            color=(255, 255, 255),
                            thickness=2,
                        ),
                    )

                # Dibujar mano derecha
                if results.right_hand_landmarks:
                    draw_landmarks(
                        frame,
                        results.right_hand_landmarks,
                        HAND_CONNECTIONS,
                        DrawingSpec(
                            color=(0, 255, 0),
                            thickness=2,
                            circle_radius=3,
                        ),
                        DrawingSpec(
                            color=(255, 255, 255),
                            thickness=2,
                        ),
                    )

                # Dibujar contornos del rostro
                if results.face_landmarks:
                    draw_landmarks(
                        frame,
                        results.face_landmarks,
                        FACEMESH_CONTOURS,
                        landmark_drawing_spec=None,
                        connection_drawing_spec=DrawingSpec(
                            color=(180, 180, 180),
                            thickness=1,
                        ),
                    )

                # Estado de detección de las manos
                left_detected = results.left_hand_landmarks is not None
                right_detected = results.right_hand_landmarks is not None

                status_left = (
                    f"Mano izquierda: {'SI' if left_detected else 'NO'}"
                )
                cv2.putText(
                    frame,
                    status_left,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 0, 0),
                    2,
                )

                status_right = (
                    f"Mano derecha: {'SI' if right_detected else 'NO'}"
                )
                cv2.putText(
                    frame,
                    status_right,
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 180, 0),
                    2,
                )

                # Mostrar resolución de captura
                cv2.putText(
                    frame,
                    f"Resolucion: {width}x{height}",
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                )

                cv2.putText(
                    frame,
                    "Presiona Q o ESC para salir",
                    (10, frame.shape[0] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 255, 255),
                    1,
                )

                cv2.imshow("GESTOSVISION - Prueba Holistic", frame)

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q") or key == 27:
                    break

    finally:
        camera.release()
        cv2.destroyAllWindows()

    print("Prueba finalizada.")


if __name__ == "__main__":
    main()
