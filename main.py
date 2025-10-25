import configparser
import os

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
if __name__ == "__main__":
    if load_config():
        print("="*50)
        print("Служба контроля хранилища изображений запущена")
        print(f"Отслеживаемая директория: {TARGET_DIRECTORY}")
        print(f"Максимальный размер файла: {MAX_SIZE_KB} КБ")
        print("="*50)