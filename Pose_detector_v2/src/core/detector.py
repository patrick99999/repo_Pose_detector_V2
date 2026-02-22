"""
Pose Detector - Wrapper attorno a MediaPipe PoseLandmarker (Tasks API).
Elabora singoli frame BGR (OpenCV) e restituisce il frame
con i landmark disegnati + i risultati raw di MediaPipe.
"""

import os

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    PoseLandmarker,
    PoseLandmarkerOptions,
    PoseLandmarksConnections,
    RunningMode,
    drawing_utils,
    drawing_styles,
)


# Percorso di default del modello (relativo alla root del progetto)
_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "assets", "models", "pose_landmarker_lite.task"
)


class PoseDetector:
    """Rileva la posa umana in un frame video usando MediaPipe PoseLandmarker."""

    def __init__(self, model_path: str | None = None):
        model = model_path or _DEFAULT_MODEL_PATH
        model = os.path.abspath(model)

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model),
            running_mode=RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = PoseLandmarker.create_from_options(options)
        self._frame_timestamp_ms = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_frame(self, frame: np.ndarray) -> tuple[np.ndarray, object]:
        """Elabora un frame BGR e restituisce (frame_annotato, results).

        Args:
            frame: immagine BGR (OpenCV).

        Returns:
            frame_out: copia del frame con i landmark disegnati.
            results: PoseLandmarkerResult.
        """
        # Converti BGR → RGB e crea un mp.Image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Incrementa il timestamp per la modalità VIDEO
        self._frame_timestamp_ms += 33  # ~30 FPS
        results = self._landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

        # Disegna i landmark sul frame originale (BGR)
        frame_out = frame.copy()
        if results.pose_landmarks:
            for pose_landmarks in results.pose_landmarks:
                # draw_landmarks accetta direttamente list[NormalizedLandmark]
                drawing_utils.draw_landmarks(
                    image=frame_out,
                    landmark_list=pose_landmarks,
                    connections=PoseLandmarksConnections.POSE_LANDMARKS,
                    landmark_drawing_spec=drawing_styles.DrawingSpec(
                        color=(0, 255, 0), thickness=2, circle_radius=2
                    ),
                    connection_drawing_spec=drawing_styles.DrawingSpec(
                        color=(255, 255, 0), thickness=2
                    ),
                )

        return frame_out, results

    def release(self) -> None:
        """Rilascia le risorse di MediaPipe."""
        self._landmarker.close()
