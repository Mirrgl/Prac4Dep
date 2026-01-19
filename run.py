#!/usr/bin/env python3
"""
Альтернативный скрипт запуска с загрузкой .env файла
"""
import os
import sys
from pathlib import Path


def load_env_file(env_path=".env"):
    """Загрузка переменных из .env файла"""
    if not Path(env_path).exists():
        print(f"Ошибка: файл {env_path} не найден")
        print("Создайте его из .env.example")
        sys.exit(1)
    
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            # Пропускаем комментарии и пустые строки
            if not line or line.startswith('#'):
                continue
            
            # Парсим KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Убираем кавычки если есть
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value
                print(f"Загружено: {key}={value}")


def main():
    print("=== SIEM Web Interface ===\n")
    
    # Загружаем .env
    load_env_file()
    
    # Проверяем обязательные переменные
    if not os.environ.get("SIEM_ADMIN_PASSWORD"):
        print("\nОшибка: SIEM_ADMIN_PASSWORD не установлен в .env")
        sys.exit(1)
    
    print(f"\nЗапуск на {os.environ.get('SIEM_WEB_HOST', '0.0.0.0')}:{os.environ.get('SIEM_WEB_PORT', '8000')}")
    print("Нажмите Ctrl+C для остановки\n")
    
    # Импортируем и запускаем
    try:
        import uvicorn
        uvicorn.run(
            "web.app:app",
            host=os.environ.get("SIEM_WEB_HOST", "0.0.0.0"),
            port=int(os.environ.get("SIEM_WEB_PORT", "8000")),
            reload=False
        )
    except ImportError:
        print("Ошибка: uvicorn не установлен")
        print("Установите: pip install uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
