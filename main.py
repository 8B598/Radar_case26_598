"""!
@file main.py
@brief Основной файл службы контроля хранилища изображений.
@details Использует бинарный поиск для нахождения оптимального
         качества сжатия, обеспечивая максимальную эффективность.
@author Кристина
"""

import configparser
import os
import time
import io
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- Глобальные переменные ---
TARGET_DIRECTORY = ""
MAX_SIZE_KB = 0
MAX_SIZE_BYTES = 0

def load_config(file_path='config.ini'):
    """!
    @brief Загружает и проверяет конфигурацию из ini-файла.
    @param file_path: Путь к файлу конфигурации.
    @return: True, если конфигурация загружена успешно, иначе False.
    """
    global TARGET_DIRECTORY, MAX_SIZE_KB, MAX_SIZE_BYTES
    
    config = configparser.ConfigParser()
    if not os.path.exists(file_path):
        print(f"Ошибка: Файл конфигурации '{file_path}' не найден.")
        return False
        
    config.read(file_path)
    
    try:
        TARGET_DIRECTORY = config.get('Settings', 'Directory')
        MAX_SIZE_KB = config.getint('Settings', 'MaxSizeKB')
        MAX_SIZE_BYTES = MAX_SIZE_KB * 1024
        
        if not os.path.isdir(TARGET_DIRECTORY):
            print(f"Ошибка: Указанная в config.ini директория '{TARGET_DIRECTORY}' не существует.")
            return False
            
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Ошибка в файле конфигурации: {e}")
        return False
        
    return True

def find_optimal_quality(img, original_format):
    """!
    @brief Находит максимальное качество сжатия с помощью бинарного поиска.
    @param img: Объект изображения PIL.
    @param original_format: Формат исходного изображения (JPEG, PNG).
    @return: Оптимальное качество (int) и бинарный объект изображения (bytes).
    """
    low = 1
    high = 95  # Максимальное осмысленное качество для JPEG
    best_quality = -1
    best_image_bytes = None

    while low <= high:
        mid = (low + high) // 2
        buffer = io.BytesIO()
        img.save(buffer, format=original_format, quality=mid, optimize=True)
        
        if buffer.tell() <= MAX_SIZE_BYTES:
            best_quality = mid
            best_image_bytes = buffer.getvalue()
            low = mid + 1  # Попробуем найти качество получше
        else:
            high = mid - 1 # Качество слишком высокое, ищем в нижней половине
            
    return best_quality, best_image_bytes

def process_image(image_path):
    """!
    @brief Обрабатывает изображение, гарантированно приводя его к нужному размеру.
    @param image_path: Путь к новому изображению.
    """
    try:
        time.sleep(1) # Даем файлу полностью записаться на диск
        print(f"\nОбнаружен новый файл: {os.path.basename(image_path)}")
        
        with Image.open(image_path) as img:
            original_format = img.format
            
            # 1. Преобразование в оттенки серого
            if img.mode != 'L':
                print("  -> Преобразование в оттенки серого...")
                img = img.convert('L')
            
            # 2. Проверка размера и запуск сжатия, если необходимо
            buffer = io.BytesIO()
            img.save(buffer, format=original_format)
            
            if buffer.tell() <= MAX_SIZE_BYTES:
                print(f"  -> Размер ({buffer.tell()/1024:.2f} КБ) уже соответствует лимиту. Сохранение.")
                with open(image_path, 'wb') as f:
                    f.write(buffer.getvalue())
                return

            print(f"  -> Размер ({buffer.tell()/1024:.2f} КБ) превышает лимит. Поиск оптимального сжатия...")
            
            # 3. Бинарный поиск оптимального качества
            quality, image_bytes = find_optimal_quality(img, original_format)
            if quality != -1:
                print(f"  -> Успех! Найдено оптимальное качество ({quality}%). Файл сохранен.")
                with open(image_path, 'wb') as f:
                    f.write(image_bytes)
                return

            # 4. Если сжатия недостаточно, уменьшаем разрешение
            print("  -> Сжатия недостаточно. Уменьшение разрешения...")
            while True:
                new_width = int(img.width * 0.9)
                new_height = int(img.height * 0.9)
                if new_width < 10 or new_height < 10:
                    print("Ошибка: Невозможно уменьшить разрешение дальше.")
                    break
                
                img = img.resize((new_width, new_height), Image.LANCZOS)
                quality, image_bytes = find_optimal_quality(img, original_format)
                
                if quality != -1:
                    print(f"  -> Успех! Файл сохранен с разрешением {new_width}x{new_height} и качеством {quality}%.")
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    return

    except (IOError, SyntaxError) as e:
        print(f"Ошибка: Файл {os.path.basename(image_path)} не является изображением или поврежден: {e}")
    except Exception as e:
        print(f"Ошибка: Произошла непредвиденная ошибка при обработке файла: {e}")


class NewImageHandler(FileSystemEventHandler):
    """! @brief Обработчик событий, реагирующий на создание новых файлов. """
    def on_created(self, event):
        if not event.is_directory:
            valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')
            if event.src_path.lower().endswith(valid_extensions):
                process_image(event.src_path)

if __name__ == "__main__":
    if load_config():
        print("="*50)
        print("Служба контроля хранилища изображений запущена")
        print(f"Отслеживаемая директория: {TARGET_DIRECTORY}")
        print(f"Максимальный размер файла: {MAX_SIZE_KB} КБ")
        print("="*50)
        print("Ожидание новых файлов... (Для остановки нажмите Ctrl+C)")

        event_handler = NewImageHandler()
        observer = Observer()
        observer.schedule(event_handler, TARGET_DIRECTORY, recursive=False)
        observer.start()

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            observer.stop()
            print("\nСлужба остановлена.")
        observer.join()