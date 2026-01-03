import sys
import time
from PIL import ImageGrab

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTabWidget, QGridLayout, QLineEdit, 
    QMessageBox, QFrame, QDialog, QCheckBox, QTextEdit
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QRect, QPoint
)
from PyQt6.QtGui import (
    QImage, QPixmap, QFont, QIntValidator, QPainter, QPen, QColor
)

from sudoku_core import SudokuBackend

# Константы конфигурации
PREVIEW_SCALE = 0.5  # Масштаб уменьшения превью экрана для производительности


class ScreenStreamThread(QThread):
    """
    Фоновый поток для захвата экрана и отправки изображений в GUI.
    """
    image_signal = pyqtSignal(QImage)
    
    def run(self):
        while True:
            try:
                # Захват экрана (без учета прозрачных слоев ОС для скорости)
                screen = ImageGrab.grab(bbox=None, include_layered_windows=False)
                w, h = screen.size
                
                # Масштабирование
                new_w, new_h = int(w * PREVIEW_SCALE), int(h * PREVIEW_SCALE)
                screen = screen.resize((new_w, new_h))
                
                # Конвертация в QImage
                data = screen.tobytes("raw", "RGB")
                qimg = QImage(data, new_w, new_h, QImage.Format.Format_RGB888)
                self.image_signal.emit(qimg)
                
                time.sleep(0.04)  # Ограничение ~25 FPS
            except Exception:
                pass


class SnippingWidget(QWidget):
    """
    Полупрозрачный полноэкранный виджет для ручного выделения прямоугольной области.
    Поддерживает коррекцию координат для экранов с High DPI (масштабированием).
    """
    selection_finished = pyqtSignal(tuple)  # Сигнал возвращает (x1, y1, x2, y2)

    def __init__(self):
        super().__init__()
        # Настройка окна: без рамок, поверх всех окон, инструмент (без иконки в таскбаре)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.3) 
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.begin = QPoint()
        self.end = QPoint()
        self.is_selecting = False
        
        # Охват всех мониторов
        total_rect = QRect()
        for screen in QApplication.screens():
            total_rect = total_rect.united(screen.geometry())
            
        self.setGeometry(total_rect)
        self.show()

    def paintEvent(self, event):
        """Отрисовка зеленой рамки выделения."""
        if self.is_selecting:
            painter = QPainter(self)
            pen = QPen(QColor(0, 255, 0), 2)
            painter.setPen(pen)
            painter.setBrush(QColor(0, 0, 0, 0))
            
            rect = QRect(self.begin, self.end).normalized()
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.is_selecting = True
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        self.is_selecting = False
        self.close()
        
        # 1. Логические координаты внутри окна PyQt
        start_x = min(self.begin.x(), self.end.x())
        start_y = min(self.begin.y(), self.end.y())
        end_x = max(self.begin.x(), self.end.x())
        end_y = max(self.begin.y(), self.end.y())

        # 2. Глобальные координаты (учет смещения мониторов)
        global_pos = self.mapToGlobal(QPoint(0, 0))
        x1 = start_x + global_pos.x()
        y1 = start_y + global_pos.y()
        x2 = end_x + global_pos.x()
        y2 = end_y + global_pos.y()

        # 3. Коррекция DPI (перевод логических пикселей в физические)
        ratio = self.devicePixelRatio() 
        
        final_x1 = int(x1 * ratio)
        final_y1 = int(y1 * ratio)
        final_x2 = int(x2 * ratio)
        final_y2 = int(y2 * ratio)

        # Защита от случайных кликов (минимальный размер области)
        if abs(final_x2 - final_x1) > 10 and abs(final_y2 - final_y1) > 10:
            self.selection_finished.emit((final_x1, final_y1, final_x2, final_y2))


class WorkerThread(QThread):
    """
    Универсальный рабочий поток для выполнения "тяжелых" задач 
    (ML инференс, C++ solver), чтобы не блокировать GUI.
    """
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args):
        super().__init__()
        self.func = func
        self.args = args

    def run(self):
        try:
            res = self.func(*self.args)
            self.finished.emit(res)
        except Exception as e:
            self.error.emit(str(e))


class CountdownDialog(QDialog):
    """Модальное окно с обратным отсчетом перед автоматическим вводом."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Внимание!")
        self.setModal(True)
        self.layout = QVBoxLayout()
        
        lbl = QLabel("НЕ ТРОГАЙТЕ МЫШЬ И КЛАВИАТУРУ!\nЗаполнение начнется через:")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
        self.layout.addWidget(lbl)
        
        self.timer_lbl = QLabel("5")
        self.timer_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_lbl.setStyleSheet("font-size: 48px; font-weight: bold;")
        self.layout.addWidget(self.timer_lbl)
        
        self.setLayout(self.layout)
        
        self.counter = 5
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(1000)

    def tick(self):
        self.counter -= 1
        self.timer_lbl.setText(str(self.counter))
        if self.counter <= 0:
            self.timer.stop()
            self.accept()


class SudokuCell(QLineEdit):
    """
    Виджет одной ячейки судоку. 
    Поддерживает валидацию (1-9) и цветовое кодирование состояний.
    """
    def __init__(self):
        super().__init__()
        self.setFixedSize(40, 40)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(QFont("Arial", 16))
        self.setMaxLength(1)
        # Разрешаем ввод только цифр 1-9
        self.setValidator(QIntValidator(1, 9, self))
        self.setReadOnly(True)
        
        self.default_style = "border: 1px solid gray; background-color: white;"
        self.origin_style = "border: 1px solid gray; background-color: #e0f7fa; color: black; font-weight: bold;"
        self.solved_style = "border: 1px solid gray; background-color: #f1f8e9; color: #2e7d32; font-weight: bold;"
        
        self.setStyleSheet(self.default_style)

    def set_value(self, val, is_origin=False):
        """Устанавливает значение и стиль ячейки."""
        if val == 0:
            self.setText("")
            self.setStyleSheet(self.default_style)
        else:
            self.setText(str(val))
            if is_origin:
                self.setStyleSheet(self.origin_style)
            else:
                self.setStyleSheet(self.solved_style)

    def get_value(self):
        """Возвращает числовое значение ячейки (0 если пусто)."""
        txt = self.text()
        return int(txt) if txt.isdigit() else 0


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TS9S-AI") 
        self.resize(1100, 750)
        
        # Инициализация бэкенда
        self.backend = SudokuBackend()
        
        # Состояние приложения
        self.current_grid = [[0]*9 for _ in range(9)]
        self.solved_grid = None
        self.detected_coords = None 
        
        # Настройка UI
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        self.setup_solver_tab()
        self.setup_instructions_tab()
        
        # Вкладка "О программе"
        info_tab = QLabel("TS9S-AI v2.2\nManual Selection + Visual Feedback\nPowered by YOLOv8 & PyTorch")
        info_tab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabs.addTab(info_tab, "О программе")
        
        # Запуск потока трансляции
        self.stream_thread = ScreenStreamThread()
        self.stream_thread.image_signal.connect(self.update_screen_preview)
        self.stream_thread.start()

    def setup_solver_tab(self):
        """Сборка вкладки 'Главная'."""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # --- Левая панель: Видео ---
        left_panel = QVBoxLayout()
        self.screen_label = QLabel("Загрузка экрана...")
        self.screen_label.setMinimumSize(480, 270)
        self.screen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.screen_label.setStyleSheet("background-color: black; color: white;")
        self.screen_label.setScaledContents(True) 
        
        left_panel.addWidget(QLabel("Трансляция экрана (с зоной поиска):"))
        left_panel.addWidget(self.screen_label, stretch=1)
        layout.addLayout(left_panel, stretch=3)
        
        # --- Правая панель: Сетка и Управление ---
        right_panel = QVBoxLayout()
        
        # Сетка 9x9
        grid_frame = QFrame()
        grid_frame.setStyleSheet("background-color: #333;")
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(2)
        grid_layout.setContentsMargins(2,2,2,2)
        
        self.cells = []
        for i in range(9):
            row_cells = []
            for j in range(9):
                cell = SudokuCell()
                grid_layout.addWidget(cell, i, j)
                row_cells.append(cell)
            self.cells.append(row_cells)
        right_panel.addWidget(grid_frame)
        
        # Кнопки
        btn_layout = QVBoxLayout()
        
        # Блок 1: Поиск
        row1 = QHBoxLayout()
        self.btn_detect = QPushButton("1. Авто-поиск (AI)")
        self.btn_detect.setFixedHeight(40)
        self.btn_detect.clicked.connect(self.on_detect_click)
        
        self.btn_snipping = QPushButton("🔍 Выбрать область")
        self.btn_snipping.setFixedHeight(40)
        self.btn_snipping.clicked.connect(self.start_snipping)
        
        row1.addWidget(self.btn_detect)
        row1.addWidget(self.btn_snipping)
        btn_layout.addLayout(row1)
        
        self.btn_manual_edit = QPushButton("Включить ручное редактирование")
        self.btn_manual_edit.clicked.connect(self.on_manual_edit_click)
        btn_layout.addWidget(self.btn_manual_edit)
        
        # Блок 2: Решение
        self.btn_solve = QPushButton("2. Решить судоку")
        self.btn_solve.setFixedHeight(40)
        self.btn_solve.setEnabled(False)
        self.btn_solve.clicked.connect(self.on_solve_click)
        btn_layout.addWidget(self.btn_solve)
        
        # Блок 3: Ввод
        row3 = QHBoxLayout()
        self.btn_fill = QPushButton("3. Заполнить")
        self.btn_fill.setFixedHeight(40)
        self.btn_fill.setEnabled(False)
        self.btn_fill.setStyleSheet("background-color: #ffccbc; color: black;")
        self.btn_fill.clicked.connect(self.on_fill_click)
        
        self.chk_random = QCheckBox("Случ. порядок")
        row3.addWidget(self.btn_fill)
        row3.addWidget(self.chk_random)
        btn_layout.addLayout(row3)
        
        btn_layout.addStretch()
        right_panel.addLayout(btn_layout)
        layout.addLayout(right_panel, stretch=2)
        
        self.tabs.addTab(tab, "Главная")

    def setup_instructions_tab(self):
        """Сборка вкладки 'Инструкция'."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        
        html_content = """
        <h2 style="color: #2e7d32;">🧩 TS9S-AI — Полное руководство</h2>
        
        <p style="font-size: 14px;"><b>TS9S-AI</b> позволяет автоматически находить, решать и вводить решения для судоку прямо на экране вашего компьютера.</p>
        <hr>
        
        <h3>1️⃣ Шаг 1: Поиск судоку</h3>
        <p>Откройте сайт или приложение с игрой. Убедитесь, что сетка видна полностью.</p>
        <ul>
            <li><b>Вариант А: Авто-поиск (AI)</b><br>
            Нажмите кнопку <b>"1. Авто-поиск (AI)"</b>. Нейросеть попытается сама найти поле на экране.</li>
            <li><b>Вариант Б: Ручное выделение</b><br>
            Нажмите <b>"🔍 Выбрать область"</b>. Экран затемнится. Выделите прямоугольник строго по границам поля.</li>
        </ul>
        <p><i>✅ <b>Проверка:</b> На трансляции слева должна появиться <b>красная рамка</b>.</i></p>

        <h3>2️⃣ Шаг 2: Проверка цифр</h3>
        <ul>
            <li>Если цифры определились неверно, нажмите <b>"Включить ручное редактирование"</b>.</li>
            <li>Исправьте ошибки, кликая по ячейкам и вводя цифры.</li>
        </ul>

        <h3>3️⃣ Шаг 3: Решение</h3>
        <p>Нажмите <b>"2. Решить судоку"</b>. Пустые клетки заполнятся <span style="color: green; font-weight: bold;">зелеными цифрами</span>.</p>

        <h3>4️⃣ Шаг 4: Заполнение</h3>
        <ul>
            <li><b>Опция "Случ. порядок":</b> Рекомендуется включить. Вводит цифры хаотично (Анти-чит).</li>
            <li>Нажмите <b>"3. Заполнить"</b>.</li>
            <li><b>⚠️ ВАЖНО:</b> Когда исчезнет таймер — <b>УБЕРИТЕ РУКИ ОТ МЫШИ И КЛАВИАТУРЫ!</b></li>
        </ul>
        """
        
        text_area.setHtml(html_content)
        layout.addWidget(text_area)
        self.tabs.addTab(tab, "Инструкция")

    def update_screen_preview(self, qimg):
        """Слот обновления превью экрана. Рисует красную рамку, если координаты найдены."""
        if self.detected_coords:
            painter = QPainter(qimg)
            
            # Красная рамка толщиной 6px
            painter.setPen(QPen(QColor(255, 0, 0), 6)) 
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            x1, y1, x2, y2 = self.detected_coords
            
            # Масштабируем координаты под уменьшенное изображение
            sx1 = int(x1 * PREVIEW_SCALE)
            sy1 = int(y1 * PREVIEW_SCALE)
            w = int((x2 - x1) * PREVIEW_SCALE)
            h = int((y2 - y1) * PREVIEW_SCALE)
            
            painter.drawRect(sx1, sy1, w, h)
            painter.end()

        pixmap = QPixmap.fromImage(qimg)
        self.screen_label.setPixmap(pixmap)
    
    # --- СЛОТЫ (Обработчики событий) ---
    
    def start_snipping(self):
        """Запуск инструмента выделения области."""
        self.showMinimized() 
        self.snipper = SnippingWidget()
        self.snipper.selection_finished.connect(self.handle_snipping_finished)
    
    def handle_snipping_finished(self, coords):
        """Обработка координат после ручного выделения."""
        self.showNormal()
        self.activateWindow()
        
        self.detected_coords = coords 
        
        self.btn_detect.setText("Обработка...")
        self.btn_detect.setEnabled(False)
        self.btn_snipping.setEnabled(False)
        
        self.worker = WorkerThread(self.backend.recognize_from_manual, coords)
        self.worker.finished.connect(self.handle_detect_result)
        self.worker.error.connect(lambda e: self.show_error(f"Ошибка OCR: {e}"))
        self.worker.start()

    def on_detect_click(self):
        """Запуск авто-поиска через YOLO."""
        self.btn_detect.setEnabled(False)
        self.btn_detect.setText("Поиск...")
        self.worker = WorkerThread(self.backend.detect_and_recognize)
        self.worker.finished.connect(self.handle_detect_result)
        self.worker.error.connect(lambda e: self.show_error(f"Ошибка AI: {e}"))
        self.worker.start()

    def handle_detect_result(self, result):
        """Обработка результата распознавания (Grid + Coords)."""
        grid, coords = result
        self.current_grid = grid
        self.detected_coords = coords
        self.solved_grid = None
        
        # Обновление UI сетки
        for i in range(9):
            for j in range(9):
                val = grid[i][j]
                self.cells[i][j].set_value(val, is_origin=(val != 0))
                self.cells[i][j].setReadOnly(True)
        
        # Обновление состояния кнопок
        self.btn_detect.setText("1. Авто-поиск (AI)")
        self.btn_detect.setEnabled(True)
        self.btn_snipping.setEnabled(True)
        self.btn_solve.setEnabled(True)
        self.btn_fill.setEnabled(False)
        QMessageBox.information(self, "Успех", "Судоку обработано!")

    def on_manual_edit_click(self):
        """Включение режима редактирования ячеек."""
        for i in range(9):
            for j in range(9):
                self.cells[i][j].setReadOnly(False)
                if self.cells[i][j].text() == "":
                    self.cells[i][j].setStyleSheet("border: 1px solid gray; background-color: white;")
        self.btn_solve.setEnabled(True)

    def on_solve_click(self):
        """Запуск решателя (C++)."""
        # 1. Синхронизация UI -> Данные (на случай ручных правок)
        new_grid = []
        for i in range(9):
            row = []
            for j in range(9):
                row.append(self.cells[i][j].get_value())
            new_grid.append(row)
        self.current_grid = new_grid

        # 2. Запуск потока
        self.btn_solve.setEnabled(False)
        self.btn_solve.setText("Решение...")
        
        self.worker = WorkerThread(self.backend.solve_cpp, self.current_grid)
        self.worker.finished.connect(self.handle_solve_result)
        self.worker.error.connect(lambda e: self.show_error(f"Ошибка C++: {e}"))
        self.worker.start()

    def handle_solve_result(self, result_grid):
        """Отображение решения."""
        self.btn_solve.setText("2. Решить судоку")
        self.btn_solve.setEnabled(True)
        
        if result_grid is None:
            self.show_error("Решение не найдено.")
            return
            
        self.solved_grid = result_grid
        
        for i in range(9):
            for j in range(9):
                orig_val = self.current_grid[i][j]
                new_val = self.solved_grid[i][j]
                if orig_val == 0:
                    self.cells[i][j].set_value(new_val, is_origin=False)
                else:
                    self.cells[i][j].set_value(new_val, is_origin=True)
                self.cells[i][j].setReadOnly(True)
        
        self.btn_fill.setEnabled(True)

    def on_fill_click(self):
        """Запуск автоматического заполнения."""
        dlg = CountdownDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.btn_fill.setEnabled(False)
            random_mode = self.chk_random.isChecked()
            self.worker = WorkerThread(self.backend.fill_sudoku, self.solved_grid, random_mode)
            self.worker.finished.connect(lambda: self.btn_fill.setEnabled(True))
            self.worker.start()

    def show_error(self, msg):
        """Вывод сообщения об ошибке."""
        QMessageBox.critical(self, "Ошибка", msg)
        self.btn_detect.setEnabled(True)
        self.btn_snipping.setEnabled(True)
        self.btn_detect.setText("1. Авто-поиск (AI)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())