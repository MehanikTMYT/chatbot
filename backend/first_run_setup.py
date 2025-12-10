import os
import secrets
import hashlib
from pathlib import Path

def generate_secret_key():
    """Генерация секретного ключа для JWT"""
    return secrets.token_urlsafe(32)

def ensure_config_files():
    """Проверка и создание необходимых конфигурационных файлов"""
    # Проверяем .env файл
    env_file = Path('.env')
    if not env_file.exists():
        # Создаем .env из .env.universal сгенерированными значениями
        env_content = f"""
# Сгенерированные настройки для первого запуска
VDS_DOMAIN={os.getenv('VDS_DOMAIN', 'chat.mehhost.ru')}
API_GATEWAY_PORT={os.getenv('API_GATEWAY_PORT', '8000')}
LOCAL_INFERENCE_IP={os.getenv('LOCAL_INFERENCE_IP', 'auto_detect')}
LOCAL_INFERENCE_PORT={os.getenv('LOCAL_INFERENCE_PORT', '8001')}
INFERENCE_TIMEOUT={os.getenv('INFERENCE_TIMEOUT', '120')}
RUST_ACCELERATION={os.getenv('RUST_ACCELERATION', 'true')}
RUST_CUDA_ARCH={os.getenv('RUST_CUDA_ARCH', 'auto')}
RUST_FALLBACK_ON_ERROR={os.getenv('RUST_FALLBACK_ON_ERROR', 'true')}
CONNECTION_MODE={os.getenv('CONNECTION_MODE', 'auto')}
MAX_RECONNECT_ATTEMPTS={os.getenv('MAX_RECONNECT_ATTEMPTS', '10')}
RECONNECT_DELAY={os.getenv('RECONNECT_DELAY', '5')}
JWT_SECRET={generate_secret_key()}
ALLOW_OFFLINE_MODE={os.getenv('ALLOW_OFFLINE_MODE', 'true')}
"""
        with open('.env', 'w') as f:
            f.write(env_content.strip())
        print("Created .env file with generated settings")

def setup_directories():
    """Создание необходимых директорий"""
    directories = [
        'logs',
        'data',
        'uploads',
        'models'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Ensured directory exists: {directory}")

def initialize_database():
    """Инициализация базы данных"""
    # Здесь будет логика инициализации базы данных
    print("Database initialization would happen here")
    # В реальной реализации здесь будет создание таблиц и т.д.

def detect_hardware():
    """Определение характеристик оборудования"""
    import platform
    import psutil
    
    hardware_info = {
        'system': platform.system(),
        'node': platform.node(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'cpu_count': psutil.cpu_count(),
        'memory_total': psutil.virtual_memory().total,
        'memory_available': psutil.virtual_memory().available
    }
    
    # Сохраняем информацию об оборудовании
    with open('hardware_info.json', 'w') as f:
        import json
        json.dump(hardware_info, f, indent=2)
    
    print(f"Detected hardware: {hardware_info['system']} {hardware_info['machine']}")
    print(f"CPU cores: {hardware_info['cpu_count']}")
    print(f"Total memory: {hardware_info['memory_total'] / (1024**3):.2f} GB")
    
    return hardware_info

def run_first_setup():
    """Запуск процедуры первой настройки"""
    print("Running first-time setup...")
    
    # Генерация секретных ключей
    if not os.getenv('JWT_SECRET') or os.getenv('JWT_SECRET') == 'auto_generate':
        secret_key = generate_secret_key()
        os.environ['JWT_SECRET'] = secret_key
        print("Generated new JWT secret key")
    
    # Создание необходимых директорий
    setup_directories()
    
    # Проверка и создание конфигурационных файлов
    ensure_config_files()
    
    # Определение характеристик оборудования
    hardware_info = detect_hardware()
    
    # Инициализация базы данных
    initialize_database()
    
    # Помечаем, что первоначальная настройка выполнена
    with open('.first_run_complete', 'w') as f:
        f.write('Setup completed successfully')
    
    print("First-time setup completed successfully!")

if __name__ == "__main__":
    run_first_setup()