import argparse
import os
import sys


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
    
    if not os.environ.get("SIEM_ADMIN_PASSWORD"):
        print("Error: SIEM_ADMIN_PASSWORD environment variable is required")
        print("Set it with: export SIEM_ADMIN_PASSWORD='your_password'")
        sys.exit(1)
    
    try:
        import uvicorn
        uvicorn.run(
            "web.app:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    except ImportError:
        print("Error: uvicorn is not installed. Install it with: pip install uvicorn")
        sys.exit(1)


if __name__ == "__main__":
    main()
