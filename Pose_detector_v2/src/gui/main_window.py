"""
Main Window - Finestra principale dell'applicazione Pose Detector V2.
Contiene il VideoWidget, i controlli di riproduzione e uno stile dark moderno.
"""

import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QStatusBar,
)

from gui.widgets.video_widget import VideoWidget
from core.video_processor import VideoProcessor


# ---------------------------------------------------------------------------
# Stile QSS Dark Theme
# ---------------------------------------------------------------------------
DARK_STYLE = """
QMainWindow {
    background-color: #121212;
}

QWidget#centralWidget {
    background-color: #121212;
}

QPushButton {
    background-color: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 10px 22px;
    font-size: 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3a3a3a;
    border-color: #5a9cf5;
}

QPushButton:pressed {
    background-color: #1a5bbd;
}

QPushButton:disabled {
    background-color: #1e1e1e;
    color: #555555;
    border-color: #2a2a2a;
}

QPushButton#btnLoad {
    background-color: #1a5bbd;
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton#btnLoad:hover {
    background-color: #2b6cd4;
}

QPushButton#btnPlayPause {
    background-color: #1b8c3a;
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton#btnPlayPause:hover {
    background-color: #24a84a;
}

QPushButton#btnStop {
    background-color: #c0392b;
    color: #ffffff;
    border: none;
    font-weight: 600;
}

QPushButton#btnStop:hover {
    background-color: #e74c3c;
}

QLabel {
    color: #b0b0b0;
    font-size: 13px;
}

QLabel#lblTitle {
    color: #ffffff;
    font-size: 20px;
    font-weight: 700;
    padding: 4px 0;
}

QLabel#lblFile {
    color: #8ab4f8;
    font-size: 13px;
}

QStatusBar {
    background-color: #1a1a1a;
    color: #888888;
    font-size: 12px;
}
"""

VIDEO_FILTERS = "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"


class MainWindow(QMainWindow):
    """Finestra principale con video player e pose estimation."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pose Detector V2")
        self.resize(1000, 720)
        self.setStyleSheet(DARK_STYLE)

        # --- State ---
        self._video_loaded = False
        self._is_playing = False

        # --- Core ---
        self._processor = VideoProcessor()
        self._processor.frame_ready.connect(self._on_frame_ready)
        self._processor.playback_finished.connect(self._on_playback_finished)
        self._processor.fps_updated.connect(self._on_fps_updated)

        # --- UI ---
        self._build_ui()
        self._update_button_states()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(16, 12, 16, 12)
        root_layout.setSpacing(12)

        # --- Title ---
        lbl_title = QLabel("Pose Detector V2")
        lbl_title.setObjectName("lblTitle")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(lbl_title)

        # --- Video Widget ---
        self._video_widget = VideoWidget()
        root_layout.addWidget(self._video_widget, stretch=1)

        # --- File info ---
        self._lbl_file = QLabel("Nessun file selezionato")
        self._lbl_file.setObjectName("lblFile")
        self._lbl_file.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(self._lbl_file)

        # --- Control bar ---
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        self._btn_load = QPushButton("📂  Carica Video")
        self._btn_load.setObjectName("btnLoad")
        self._btn_load.clicked.connect(self._on_load_clicked)

        self._btn_play_pause = QPushButton("▶  Play")
        self._btn_play_pause.setObjectName("btnPlayPause")
        self._btn_play_pause.clicked.connect(self._on_play_pause_clicked)

        self._btn_stop = QPushButton("⏹  Stop")
        self._btn_stop.setObjectName("btnStop")
        self._btn_stop.clicked.connect(self._on_stop_clicked)

        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self._btn_load)
        ctrl_layout.addWidget(self._btn_play_pause)
        ctrl_layout.addWidget(self._btn_stop)
        ctrl_layout.addStretch()

        root_layout.addLayout(ctrl_layout)

        # --- Status bar ---
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Pronto")

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_load_clicked(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleziona un video", "", VIDEO_FILTERS
        )
        if not path:
            return

        # Se un video era in riproduzione, fermalo
        if self._is_playing:
            self._processor.stop_playback()
            self._is_playing = False

        ok, w, h, fps = self._processor.load_video(path)
        if ok:
            self._video_loaded = True
            self._video_widget.clear_display()
            filename = os.path.basename(path)
            self._lbl_file.setText(f"📎 {filename}   ({w}×{h}, {fps:.1f} FPS)")
            self._status_bar.showMessage(f"Video caricato: {filename}")
            self._btn_play_pause.setText("▶  Play")
        else:
            self._video_loaded = False
            self._status_bar.showMessage("Errore: impossibile aprire il video.")

        self._update_button_states()

    def _on_play_pause_clicked(self) -> None:
        if not self._video_loaded:
            return

        if self._is_playing:
            # Pausa
            self._processor.pause()
            self._is_playing = False
            self._btn_play_pause.setText("▶  Play")
            self._status_bar.showMessage("In pausa")
        else:
            # Play
            self._processor.play()
            self._is_playing = True
            self._btn_play_pause.setText("⏸  Pausa")
            self._status_bar.showMessage("Riproduzione in corso…")

        self._update_button_states()

    def _on_stop_clicked(self) -> None:
        self._processor.stop_playback()
        self._is_playing = False
        self._video_widget.clear_display()
        self._btn_play_pause.setText("▶  Play")
        self._video_loaded = False
        self._lbl_file.setText("Nessun file selezionato")
        self._status_bar.showMessage("Riproduzione fermata")
        self._update_button_states()

    def _on_frame_ready(self, frame) -> None:
        self._video_widget.update_frame(frame)

    def _on_playback_finished(self) -> None:
        self._is_playing = False
        self._btn_play_pause.setText("▶  Play")
        self._video_loaded = False
        self._status_bar.showMessage("Riproduzione terminata")
        self._update_button_states()

    def _on_fps_updated(self, fps: float) -> None:
        self._status_bar.showMessage(f"Riproduzione in corso… | {fps:.1f} FPS")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_button_states(self) -> None:
        self._btn_play_pause.setEnabled(self._video_loaded)
        self._btn_stop.setEnabled(self._is_playing)

    def closeEvent(self, event) -> None:  # noqa: N802
        """Rilascia le risorse quando la finestra viene chiusa."""
        self._processor.release()
        event.accept()
