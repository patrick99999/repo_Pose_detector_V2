"""
Video Processor - QThread che legge un file video con OpenCV,
elabora ogni frame con il PoseDetector e lo invia alla GUI.
"""

import time
import traceback

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
        error_occurred (str): emesso con il messaggio di errore.
    """

    frame_ready = pyqtSignal(np.ndarray)
    playback_finished = pyqtSignal()
    fps_updated = pyqtSignal(float)
    error_occurred = pyqtSignal(str)
    position_changed = pyqtSignal(int)  # Emesso con l'indice del frame corrente
    angles_updated = pyqtSignal(dict)   # Emesso con gli angoli {nome: valore_gradi}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mutex = QMutex()
        self._video_path: str | None = None
        self._is_playing = False
        self._stop_requested = False
        self._seek_requested = False
        self._seek_target = 0
        self._total_frames = 0
        self._detector: PoseDetector | None = None

    # ------------------------------------------------------------------
    # Public API (chiamato dal thread GUI)
    # ------------------------------------------------------------------

    def load_video(self, path: str) -> tuple[bool, int, int, float, int]:
        """Carica un video e restituisce (ok, width, height, fps, total_frames)."""
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return False, 0, 0, 0.0, 0

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        with QMutexLocker(self._mutex):
            self._video_path = path
            self._total_frames = total_frames

        return True, w, h, fps, total_frames

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

    def set_position(self, frame_idx: int) -> None:
        """Richiede di saltare a un frame specifico."""
        with QMutexLocker(self._mutex):
            self._seek_requested = True
            self._seek_target = frame_idx

    def stop_playback(self) -> None:
        """Ferma completamente la riproduzione e il thread."""
        with QMutexLocker(self._mutex):
            self._is_playing = False
            self._stop_requested = True

        self.wait(3000)

    # ------------------------------------------------------------------
    # Thread run
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Loop principale del thread. Legge i frame e li elabora."""
        try:
            self._run_internal()
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"
            print(f"[VideoProcessor] ERRORE: {error_msg}")
            self.error_occurred.emit(str(e))

    def _run_internal(self) -> None:
        with QMutexLocker(self._mutex):
            path = self._video_path

        if path is None:
            return

        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            self.error_occurred.emit("Impossibile aprire il video.")
            return

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        target_fps = min(fps, 30.0)
        frame_delay = 1.0 / target_fps
        frame_skip_ratio = fps / target_fps if fps > target_fps else 1.0
        
        detector = PoseDetector()

        try:
            frame_count = 0
            while cap.isOpened():
                # Controlla stop e seek
                with QMutexLocker(self._mutex):
                    if self._stop_requested:
                        break
                    playing = self._is_playing
                    seek_req = self._seek_requested
                    seek_tgt = self._seek_target
                    self._seek_requested = False

                if seek_req:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, seek_tgt)
                    frame_count = seek_tgt
                    # Dobbiamo resettare il MediaPipe landmarker perché
                    # c'è stato un salto temporale brusco
                    detector.reset()

                if not playing and not seek_req:
                    # In pausa: dormi un po' e ricontrolla
                    time.sleep(0.05)
                    continue

                t_start = time.perf_counter()

                # Saltiamo i frame in eccesso solo se NON stiamo facendo seek manuale
                if not seek_req and fps > target_fps:
                    frames_to_read = max(1, int(frame_count * frame_skip_ratio) - int((frame_count - 1) * frame_skip_ratio))
                    for _ in range(frames_to_read - 1):
                        cap.read()
                
                ret, frame = cap.read()
                if not ret:
                    self.playback_finished.emit()
                    break

                frame_count = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
                self.position_changed.emit(frame_count)

                # --- 1. OTTIMIZZAZIONE: Riduzione Risoluzione ---
                # Ridimensioniamo il frame a una larghezza massima di 640px
                # Questo migliora enormemente le performance di MediaPipe Lite 
                # e la stabilità dei landmark
                MAX_WIDTH = 640
                h, w = frame.shape[:2]
                if w > MAX_WIDTH:
                    ratio = MAX_WIDTH / w
                    new_h = int(h * ratio)
                    frame = cv2.resize(frame, (MAX_WIDTH, new_h), interpolation=cv2.INTER_AREA)

                # Elabora il frame con il PoseDetector passando il target_fps
                annotated, _, angles = detector.process_frame(frame, fps=target_fps)
                self.frame_ready.emit(annotated)
                if angles:
                    self.angles_updated.emit(angles)

                # Mantieni il framerate originale target
                elapsed = time.perf_counter() - t_start
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

                # Emetti FPS effettivo
                real_elapsed = time.perf_counter() - t_start
                if real_elapsed > 0:
                    self.fps_updated.emit(1.0 / real_elapsed)

        finally:
            cap.release()
            detector.release()

        # Resetta i flag per una eventuale nuova riproduzione
        with QMutexLocker(self._mutex):
            self._is_playing = False
            self._stop_requested = False

    def release(self) -> None:
        """Rilascia tutte le risorse."""
        self.stop_playback()
