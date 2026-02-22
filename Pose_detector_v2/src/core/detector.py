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
    """Rileva la posa umana in un frame video usando MediaPipe PoseLandmarker.

    NOTA: Questa classe NON è thread-safe. Deve essere creata e usata
    sullo stesso thread. Il VideoProcessor la crea dentro run().
    """

    def __init__(self, model_path: str | None = None):
        model = model_path or _DEFAULT_MODEL_PATH
        self._model_path = os.path.abspath(model)
        self._landmarker: PoseLandmarker | None = None
        self._frame_timestamp_ms = 0

    def _ensure_initialized(self) -> None:
        """Inizializza il PoseLandmarker la prima volta che viene usato."""
        if self._landmarker is not None:
            return

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=self._model_path),
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

    def process_frame(self, frame: np.ndarray, fps: float = 30.0) -> tuple[np.ndarray, object]:
        """Elabora un frame BGR e restituisce (frame_annotato, results).

        Args:
            frame: immagine BGR (OpenCV).
            fps: framerate del video, usato per calcolare il timestamp.

        Returns:
            frame_out: copia del frame con i landmark disegnati.
            results: PoseLandmarkerResult.
        """
        self._ensure_initialized()

        # Converti BGR → RGB e crea un mp.Image
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Incrementa il timestamp in base al vero FPS del video
        self._frame_timestamp_ms += int(1000.0 / fps)
        results = self._landmarker.detect_for_video(mp_image, self._frame_timestamp_ms)

        # Disegna i landmark sul frame originale (BGR)
        frame_out = frame.copy()
        if results.pose_landmarks:
            for pose_landmarks in results.pose_landmarks:
                drawing_utils.draw_landmarks(
                    image=frame_out,
                    landmark_list=pose_landmarks,
                    connections=PoseLandmarksConnections.POSE_LANDMARKS,
                    landmark_drawing_spec=drawing_utils.DrawingSpec(
                        color=(0, 255, 0), thickness=2, circle_radius=2
                    ),
                    connection_drawing_spec=drawing_utils.DrawingSpec(
                        color=(255, 255, 0), thickness=2
                    ),
                )

        return frame_out, results

    def reset(self) -> None:
        """Chiude e ricrea il landmarker per una nuova sessione video."""
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
        self._frame_timestamp_ms = 0

    def release(self) -> None:
        """Rilascia le risorse di MediaPipe."""
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
