"""Visual screen-region magnifier. No game APIs or memory access."""
import json
import sys
from pathlib import Path
from PySide6.QtCore import Qt, QRect, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                              QPushButton, QComboBox, QMessageBox, QRubberBand)

SETTINGS = Path(__file__).with_name('settings.json')


class Selector(QWidget):
    selected = Signal(object, object)
    cancelled = Signal()

    def __init__(self, screen):
        super().__init__()
        self.screen_source = screen
        self.background = screen.grabWindow(0)
        self.start = None
        self.band = QRubberBand(QRubberBand.Shape.Rectangle, self)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CursorShape.CrossCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(self.rect(), self.background)
        painter.fillRect(12, 12, min(650, self.width()-24), 48, QColor('#101923'))
        painter.setPen(QPen(QColor('#f0e4ba')))
        painter.drawText(QRect(24, 12, self.width()-48, 48), Qt.AlignmentFlag.AlignVCenter,
                         'Arrastra sobre el minimapa · Esc para cancelar')

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start = event.position().toPoint()
            self.band.setGeometry(QRect(self.start, self.start))
            self.band.show()

    def mouseMoveEvent(self, event):
        if self.start is not None:
            self.band.setGeometry(QRect(self.start, event.position().toPoint()).normalized().intersected(self.rect()))

    def mouseReleaseEvent(self, event):
        if self.start is None or event.button() != Qt.MouseButton.LeftButton:
            return
        region = QRect(self.start, event.position().toPoint()).normalized().intersected(self.rect())
        if region.width() >= 16 and region.height() >= 16:
            self.selected.emit(self.screen_source, region)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.cancelled.emit()


class Viewer(QLabel):
    closed = Signal()

    def __init__(self, source, region, destination):
        super().__init__()
        self.source, self.region = source, region
        self.paused = False
        self.frames = 0
        self.setStyleSheet('background: black; color: white;')
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWindowTitle('LoL Minimap · F11 pantalla completa · Espacio pausa')
        g = destination.availableGeometry()
        self.setGeometry(g.x(), g.y(), min(720, g.width()), min(760, g.height()))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(33)

    def update_frame(self):
        if self.paused or self.isMinimized():
            return
        r = self.region
        image = self.source.grabWindow(0, r.x(), r.y(), r.width(), r.height())
        if image.isNull():
            self.setText('No se pudo capturar el área. Prueba el juego en ventana sin bordes.')
            self.timer.stop()
            return
        self.frames += 1
        scaled = image.scaled(self.size() * self.devicePixelRatioF(),
                              Qt.AspectRatioMode.KeepAspectRatio,
                              Qt.TransformationMode.SmoothTransformation)
        scaled.setDevicePixelRatio(self.devicePixelRatioF())
        self.setPixmap(scaled)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            self.showNormal() if self.isFullScreen() else self.showFullScreen()
        elif event.key() == Qt.Key.Key_Escape:
            self.showNormal()
        elif event.key() == Qt.Key.Key_Space:
            self.paused = not self.paused
            self.setWindowTitle('LoL Minimap · ' + ('PAUSADO · Espacio para continuar' if self.paused else 'F11 pantalla completa · Espacio pausa'))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.close()

    def closeEvent(self, event):
        self.timer.stop()
        self.closed.emit()
        event.accept()


class Minimap(QWidget):
    def __init__(self):
        super().__init__()
        self.screens = QApplication.screens()
        self.source = self.region = self.viewer = None
        self.selectors = []
        self.setWindowTitle('LoL Minimap · 0.1')
        self.resize(540, 420)
        self.setMinimumSize(490, 400)
        self.setStyleSheet('''
            QWidget { background: #101923; color: #e5edf5; font: 11pt "Segoe UI"; }
            QPushButton { background: #234450; border: 1px solid #497b86; border-radius: 6px; padding: 12px; }
            QPushButton:hover { background: #305b68; }
            QComboBox { padding: 8px; background: #1b2a39; }
        ''')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        title = QLabel('Tu minimapa, a lo grande')
        title.setStyleSheet('font-size: 21pt; font-weight: bold; color: #dfc891;')
        layout.addWidget(title)
        subtitle = QLabel('Selecciona el área y llévala a tu segunda pantalla.')
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        select = QPushButton('1. Seleccionar área del minimapa')
        select.clicked.connect(self.select_region)
        layout.addWidget(select)
        self.status = QLabel('Todavía no has seleccionado un área.')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addWidget(QLabel('Monitor de destino'))
        self.monitor_choice = QComboBox()
        for i, screen in enumerate(self.screens):
            g = screen.geometry()
            self.monitor_choice.addItem(f'Monitor {i+1} · {screen.name()} · {g.width()} × {g.height()}')
        self.monitor_choice.setCurrentIndex(1 if len(self.screens)>1 else 0)
        layout.addWidget(self.monitor_choice)
        button = QPushButton('2. Abrir vista ampliada')
        button.clicked.connect(self.open_viewer)
        layout.addWidget(button)
        help_text = QLabel('F11 pantalla completa · Espacio pausa\nEsc sale de pantalla completa · Clic derecho cierra la vista')
        help_text.setWordWrap(True)
        help_text.setStyleSheet('font-size: 9pt; color: #aebdca;')
        layout.addWidget(help_text)
        self.load_settings()
        QApplication.instance().screenRemoved.connect(self.screen_removed)

    def screen_removed(self, screen):
        self.stop_viewer()
        self.cancel_selection()
        self.source = self.region = None
        self.status.setText('Cambió la conexión de pantallas. Reinicia la aplicación.')
        self.monitor_choice.setEnabled(False)

    def load_settings(self):
        try:
            data = json.loads(SETTINGS.read_text(encoding='utf-8'))
            values = data['region']
            if len(values) != 4 or not all(type(v) is int for v in values):
                return
            region = QRect(*values)
            source = next((s for s in self.screens if s.name() == data['screen']), None)
            if source and region.width() >= 16 and region.height() >= 16 and QRect(0, 0, source.size().width(), source.size().height()).contains(region):
                self.source, self.region = source, region
                self.describe_region()
        except (OSError, ValueError, KeyError, TypeError):
            pass

    def describe_region(self):
        self.status.setText(f'Área: {self.region.width()} × {self.region.height()} · {self.source.name()}')

    def select_region(self):
        self.stop_viewer()
        self.hide()
        QTimer.singleShot(250, self.show_selectors)

    def show_selectors(self):
        for screen in self.screens:
            selector = Selector(screen)
            selector.selected.connect(self.accept_region)
            selector.cancelled.connect(self.cancel_selection)
            self.selectors.append(selector)
            selector.show()
        if self.selectors:
            self.selectors[0].activateWindow()

    def cancel_selection(self):
        for selector in self.selectors:
            selector.close()
            selector.deleteLater()
        self.selectors.clear()
        self.show()
        self.activateWindow()

    def accept_region(self, source, region):
        self.source, self.region = source, region
        self.describe_region()
        self.cancel_selection()
        try:
            SETTINGS.write_text(json.dumps({'screen': source.name(), 'region': [region.x(), region.y(), region.width(), region.height()]}, indent=2), encoding='utf-8')
        except OSError:
            self.status.setText(self.status.text() + ' · No se pudo guardar el área.')

    def open_viewer(self):
        if self.source is None or self.region is None:
            QMessageBox.information(self, 'Selecciona un área', 'Primero selecciona el minimapa en tu pantalla.')
            return
        destination = self.screens[self.monitor_choice.currentIndex()]
        if destination == self.source and len(self.screens)>1:
            QMessageBox.information(self, 'Elige otro monitor', 'Elige un monitor distinto al del minimapa para evitar capturar la propia vista.')
            return
        self.stop_viewer()
        self.viewer = Viewer(self.source, self.region, destination)
        self.viewer.show()
        self.viewer.activateWindow()

    def stop_viewer(self):
        if self.viewer:
            self.viewer.close()
            self.viewer.deleteLater()
            self.viewer = None

    def closeEvent(self, event):
        self.stop_viewer()
        for selector in self.selectors:
            selector.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Minimap()
    window.show()
    sys.exit(app.exec())
