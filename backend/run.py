#!/usr/bin/env python3
"""
AI Livestream Backend Entry Point
"""

import uvicorn
import argparse
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from core.config import get_settings
from core.logger import setup_logger


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Livestream Backend")
    parser.add_argument("--host", default=None, help="API host")
    parser.add_argument("--port", type=int, default=None, help="API port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    settings = get_settings()
    setup_logger(settings.LOGS_DIR)

    host = args.host or settings.API_HOST
    port = args.port or settings.API_PORT

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║            AI Livestream Backend v{settings.APP_VERSION}                    ║
╠══════════════════════════════════════════════════════════════╣
║  API: http://{host}:{port}                                     ║
║  Docs: http://{host}:{port}/docs                               ║
║  Debug: {args.debug or settings.DEBUG}                                        ║
╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=args.reload,
        log_level="debug" if args.debug or settings.DEBUG else "info",
    )


if __name__ == "__main__":
    main()
