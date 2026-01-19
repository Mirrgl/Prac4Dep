import argparse
import os
import sys
from dotenv import load_dotenv

# Загрузка переменных из .env файла
load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="SIEM Web Interface - Security Event Monitoring"
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("SIEM_WEB_HOST", "0.0.0.0"),
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SIEM_WEB_PORT", "8000")),
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    # Отладочный вывод
    print(f"DEBUG: SIEM_WEB_HOST из env = '{os.environ.get('SIEM_WEB_HOST', 'НЕ УСТАНОВЛЕН')}'")
    print(f"DEBUG: SIEM_WEB_PORT из env = '{os.environ.get('SIEM_WEB_PORT', 'НЕ УСТАНОВЛЕН')}'")
    print(f"DEBUG: args.host = '{args.host}'")
    print(f"DEBUG: args.port = '{args.port}'")
    
    if not os.environ.get("SIEM_ADMIN_PASSWORD"):
        print("Error: SIEM_ADMIN_PASSWORD environment variable is required")
        print("Set it with: export SIEM_ADMIN_PASSWORD='your_password'")
        sys.exit(1)
    
    try:
        import uvicorn
        
        host = args.host
        port = args.port
        
        print(f"\n{'='*60}")
        print(f"  SIEM Web Interface")
        print(f"  Доступен по адресу: http://{host}:{port}")
        print(f"  Health check: http://{host}:{port}/health")
        print(f"{'='*60}\n")
        
        uvicorn.run(
            "web.app:app",
            host=host,
            port=port,
            reload=args.reload,
            log_level="info"
        )
    except ImportError as e:
        print(f"Error: uvicorn import failed: {e}")
        print("Install it with: pip install uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
