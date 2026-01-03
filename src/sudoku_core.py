import os
import sys
import platform
import random
import subprocess
import time

import keyboard
import mouse
import torch
import torch.nn.functional as F
from PIL import ImageGrab
from torchvision import models, transforms
from ultralytics import YOLO

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Корень проекта

YOLO_PATH = os.path.join(BASE_DIR, "models", "yolo.pt")
OCR_PATH = os.path.join(BASE_DIR, "models", "ocr.pth")
CPP_WIN = os.path.join(BASE_DIR, "solver", "a.exe")
CPP_LINUX = os.path.join(BASE_DIR, "solver", "a.out") # will be soon

class SudokuBackend:
    """
    Класс, реализующий логику работы с нейросетями и внешним решателем.
    Осуществляет поиск поля, распознавание цифр и эмуляцию ввода.
    """

    def __init__(self):
        """Инициализация устройства, моделей и предобработки изображений."""
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.yolo_model = None
        self.ocr_model = None
        self.idx2label = {}
        self.last_coords = None  # Сохраняет координаты (x1, y1, x2, y2) последнего найденного поля
        
        # Трансформации для OCR (ResNet)
        self.transform = transforms.Compose([
            transforms.Resize((128, 128)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        self._load_models()

    def _load_models(self):
        """Загрузка весов моделей YOLO и OCR (ResNet) в память."""
        # 1. Загрузка детектора объектов (YOLO)
        try:
            self.yolo_model = YOLO(YOLO_PATH)
        except Exception as e:
            print(f"[Error] Не удалось загрузить YOLO: {e}")

        # 2. Загрузка классификатора цифр (OCR)
        if os.path.exists(OCR_PATH):
            try:
                # weights_only=False необходимо для загрузки старых словарей данных
                ckpt = torch.load(OCR_PATH, map_location=self.device, weights_only=False)
                
                label2idx = ckpt['label2idx']
                self.idx2label = {str(v): k for k, v in label2idx.items()}
                
                # Инициализация архитектуры ResNet18
                self.ocr_model = models.resnet18(weights=None)
                self.ocr_model.fc = torch.nn.Linear(self.ocr_model.fc.in_features, len(label2idx))
                self.ocr_model.load_state_dict(ckpt['model_state'])
                self.ocr_model.to(self.device)
                self.ocr_model.eval()
            except Exception as e:
                print(f"[Error] Не удалось загрузить OCR модель: {e}")
        else:
            print(f"[Warning] Файл весов OCR не найден: {OCR_PATH}")

    def detect_and_recognize(self):
        """
        Делает скриншот, ищет на нем судоку с помощью YOLO и распознает цифры.
        
        Returns:
            tuple: (grid, coords), где grid - матрица 9x9, coords - (x1, y1, x2, y2).
        Raises:
            ValueError: Если судоку не найдено.
        """
        screenshot = ImageGrab.grab(include_layered_windows=True)
        
        try:
            results = self.yolo_model(screenshot, verbose=False)
            if not results or not results[0].boxes:
                raise ValueError("YOLO не обнаружила судоку на экране.")
                
            # Берем первый найденный объект с самой высокой уверенностью
            x1, y1, x2, y2 = results[0].boxes[0].xyxy[0]
            coords = (int(x1), int(y1), int(x2), int(y2))
        except Exception:
            raise ValueError("Не удалось найти судоку автоматически.")

        return self.process_grid_by_coords(screenshot, coords)

    def recognize_from_manual(self, coords):
        """
        Распознает цифры в области, заданной вручную пользователем.
        
        Args:
            coords (tuple): Координаты области (x1, y1, x2, y2).
        Returns:
            tuple: (grid, coords).
        """
        screenshot = ImageGrab.grab(include_layered_windows=True)
        return self.process_grid_by_coords(screenshot, coords)

    def process_grid_by_coords(self, screenshot, coords):
        """
        Нарезает изображение на 81 ячейку и классифицирует каждую.
        
        Args:
            screenshot (PIL.Image): Исходное изображение экрана.
            coords (tuple): Координаты области судоку.
        Returns:
            tuple: (grid, coords).
        """
        self.last_coords = coords
        x1, y1, x2, y2 = coords
        
        # Защита от выхода координат за границы изображения
        w, h = screenshot.size
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        # Вычисляем шаг сетки
        step_x = (x2 - x1) / 9
        step_y = (y2 - y1) / 9
        
        grid = []
        for j in range(9):
            row = []
            for i in range(9):
                # Вырезаем отдельную ячейку
                cell_img = screenshot.crop((
                    x1 + i * step_x, 
                    y1 + j * step_y, 
                    x1 + (i + 1) * step_x, 
                    y1 + (j + 1) * step_y
                ))
                
                digit = self._predict_digit(cell_img)
                row.append(digit)
            grid.append(row)
            
        return grid, coords

    def _predict_digit(self, pil_img):
        """
        Определяет цифру на изображении ячейки с помощью ResNet.
        
        Args:
            pil_img (PIL.Image): Изображение одной ячейки.
        Returns:
            int: Распознанная цифра или 0, если ячейка пуста.
        """
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        x = self.transform(pil_img).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.ocr_model(x)
            probs = F.softmax(logits, dim=1)
            _, pred_idx = torch.max(probs, dim=1)
            
            idx_str = str(int(pred_idx.item()))
            label = self.idx2label.get(idx_str, "empty")
            
            # Фильтрация меток
            if label in ["empty", "#"]: 
                return 0
            try:
                return int(label)
            except ValueError:
                return 0

    def solve_cpp(self, initial_grid):
        """
        Запускает C++ решатель как внешний процесс.
        
        Args:
            initial_grid (list): Матрица 9x9 с исходными цифрами.
        Returns:
            list: Решенная матрица 9x9 или None в случае ошибки.
        """
        # Преобразование сетки в плоский список аргументов
        args_list = []
        for row in initial_grid:
            for val in row:
                args_list.append(str(val) if val != 0 else "#")
        
        exe = CPP_WIN if platform.system() == "Windows" else CPP_LINUX
        
        if not os.path.exists(exe):
            print(f"[Error] Исполняемый файл решателя не найден: {exe}")
            return None

        # Запуск процесса
        cmd = [exe] + args_list
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"[Error] C++ Solver failed: {result.stderr}")
            return None

        # Чтение результата из CSV
        csv_file = "out.csv"
        if not os.path.exists(csv_file):
            return None
            
        try:
            # Читаем файл вручную, чтобы избежать зависимостей от pandas
            # и проблем с заголовками
            with open(csv_file, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
            
            # Берем последние 9 строк (на случай, если файл дописывался)
            lines = lines[-9:]
            
            solved_grid = []
            for line in lines:
                parts = line.split(',')
                row = [int(p) for p in parts if p.isdigit()]
                if len(row) == 9:
                    solved_grid.append(row)
            
            return solved_grid
        except Exception as e:
            print(f"[Error] Ошибка парсинга CSV: {e}")
            return None

    def fill_sudoku(self, solved_grid, random_mode=False):
        """
        Эмулирует ввод решения в интерфейс игры.
        
        Args:
            solved_grid (list): Решенная матрица 9x9.
            random_mode (bool): Если True, вводит цифры в случайном порядке (анти-чит).
        """
        if not self.last_coords:
            raise ValueError("Координаты потеряны. Сначала выполните поиск поля.")
            
        x1, y1, x2, y2 = self.last_coords
        step_x = (x2 - x1) / 9
        step_y = (y2 - y1) / 9
        
        if random_mode:
            # Режим "Анти-чит": случайный порядок кликов
            cells_to_fill = [(i, j) for i in range(9) for j in range(9)]
            random.shuffle(cells_to_fill)
            
            for i, j in cells_to_fill:
                val = solved_grid[i][j]
                
                # Клик в центр ячейки
                center_x = x1 + (j + 0.5) * step_x
                center_y = y1 + (i + 0.5) * step_y
                
                mouse.move(center_x, center_y, duration=0.01)
                mouse.click()
                keyboard.send(str(val))
        else:
            # Классический режим "Змейка": использование клавиатурных стрелок
            start_x = x1 + step_x / 2
            start_y = y1 + step_y / 2
            
            # Клик в первую ячейку для фокуса
            mouse.move(start_x, start_y)
            mouse.click()
            time.sleep(0.2)
            
            for i in range(9):
                for j in range(9):
                    time.sleep(0.02)
                    if i % 2 == 0:
                        # Четные ряды: слева направо
                        val = solved_grid[i][j]
                        keyboard.send(str(val))
                        keyboard.send('right')
                    else:
                        # Нечетные ряды: справа налево
                        # Инвертируем индекс столбца (8 -> 0)
                        curr_j = 8 - j
                        val = solved_grid[i][curr_j]
                        keyboard.send(str(val))
                        keyboard.send('left')
                
                # Переход на строку ниже
                keyboard.send('down')