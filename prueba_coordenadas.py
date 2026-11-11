
import cv2
from mediapipe.python.solutions.holistic import Holistic

def extraer_mano(landmarks):
    if landmarks is None:
        return None

    return [
        valor
        for punto in landmarks.landmark
        for valor in (punto.x, punto.y, punto.z)
    ]


def main():
    camara = cv2.VideoCapture(0)

    if not camara.isOpened():
        print("No se pudo abrir la cámara.")
        return

    with Holistic(
        static_image_mode=False,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    ) as holistic:

        while True:
            ok, imagen = camara.read()

            if not ok:
                break

            imagen = cv2.flip(imagen, 1)
            rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
            resultados = holistic.process(rgb)

            izquierda = extraer_mano(
                resultados.left_hand_landmarks
            )
            derecha = extraer_mano(
                resultados.right_hand_landmarks
            )

            if izquierda is not None:
                print(
                    "Mano izquierda:",
                    len(izquierda),
                    "valores;",
                    "primer punto:",
                    izquierda[:3],
                )

            if derecha is not None:
                print(
                    "Mano derecha:",
                    len(derecha),
                    "valores;",
                    "primer punto:",
                    derecha[:3],
                )

            cv2.putText(
                imagen,
                "Muestra las manos - Q para salir",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
            )

            cv2.imshow("GESTOSVISION - Coordenadas", imagen)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    camara.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
