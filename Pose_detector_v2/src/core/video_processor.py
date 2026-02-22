"""
Video Processor - QThread che legge un file video con OpenCV,
elabora ogni frame con il PoseDetector e lo invia alla GUI.
"""

import time

import cv2
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

from core.detector import PoseDetector


class VideoProcessor(QThread):
    """Thread che elabora un video frame-per-frame.

    Signals:
        frame_ready (np.ndarray): emesso con il frame BGR annotato.
        playback_finished (): emesso quando il video finisce.
        fps_updated (float): emesso con il valore FPS corrente.
    """

    frame_ready = pyqtSignal(np.ndarray)
    playback_finished = pyqtSignal()
    fps_updated = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._video_path: str | None = None
        self._is_playing = False
        self._stop_requested = False
        self._detector = PoseDetector()

    # ------------------------------------------------------------------
    # Public API (chiamato dal thread GUI)
    # ------------------------------------------------------------------

    def load_video(self, path: str) -> tuple[bool, int, int, float]:
        """Carica un video e restituisce (ok, width, height, fps).

        Non avvia la riproduzione: usare play() dopo.
        """
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return False, 0, 0, 0.0

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        cap.release()

        with QMutexLocker(self._mutex):
            self._video_path = path

        return True, w, h, fps

    def play(self) -> None:
        """Avvia o riprende la riproduzione."""
        with QMutexLocker(self._mutex):
            self._is_playing = True
            self._stop_requested = False

        if not self.isRunning():
            self.start()

    def pause(self) -> None:
        """Mette in pausa la riproduzione (il thread resta attivo)."""
        with QMutexLocker(self._mutex):
            self._is_playing = False

    def stop_playback(self) -> None:
        """Ferma completamente la riproduzione e il thread."""
        with QMutexLocker(self._mutex):
            self._is_playing = False
            self._stop_requested = True

        self.wait(3000)  # attesa massima 3 secondi per la fine del thread

    # ------------------------------------------------------------------
    # Thread run
    # ------------------------------------------------------------------

    def run(self) -> None:  # noqa: C901 – complessità gestita per chiarezza
        with QMutexLocker(self._mutex):
            path = self._video_path

        if path is None:
            return

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        frame_delay = 1.0 / fps

        while cap.isOpened():
            # Controlla stop
            with QMutexLocker(self._mutex):
                if self._stop_requested:
                    break
                playing = self._is_playing

            if not playing:
                # In pausa: dormi un po' e ricontrolla
                time.sleep(0.05)
                continue

            t_start = time.perf_counter()

            ret, frame = cap.read()
            if not ret:
                # Il video è finito
                self.playback_finished.emit()
                break

            # Elabora il frame con il PoseDetector
            annotated, _ = self._detector.process_frame(frame)
            self.frame_ready.emit(annotated)

            # Mantieni il framerate originale
            elapsed = time.perf_counter() - t_start
            sleep_time = frame_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Emetti FPS effettivo
            real_elapsed = time.perf_counter() - t_start
            if real_elapsed > 0:
                self.fps_updated.emit(1.0 / real_elapsed)

        cap.release()

        # Resetta i flag per una eventuale nuova riproduzione
        with QMutexLocker(self._mutex):
            self._is_playing = False
            self._stop_requested = False

    def release(self) -> None:
        """Rilascia tutte le risorse."""
        self.stop_playback()
        self._detector.release()
