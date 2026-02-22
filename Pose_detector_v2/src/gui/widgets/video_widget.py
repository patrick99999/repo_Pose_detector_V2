"""
Video Widget - QLabel personalizzato per mostrare i frame video.
Riceve un QImage e lo scala mantenendo l'aspect ratio.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel

import numpy as np


class VideoWidget(QLabel):
    """Widget che mostra un frame video (numpy BGR) scalato al contenitore."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(320, 240)
        self.setStyleSheet("background-color: #1e1e1e; border-radius: 8px;")
        self.setText("Nessun video caricato")

    def update_frame(self, frame: np.ndarray) -> None:
        """Converte un frame BGR (numpy) in QPixmap e lo mostra."""
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        # BGR → RGB per Qt
        qt_image = QImage(
            frame.data, w, h, bytes_per_line, QImage.Format.Format_BGR888
        )
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.setPixmap(scaled)

    def clear_display(self) -> None:
        """Resetta il widget allo stato iniziale."""
        self.clear()
        self.setText("Nessun video caricato")
