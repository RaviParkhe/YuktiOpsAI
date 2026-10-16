"""
YuktiOpsAI Backend — Root Entry Point.
Exports `app` for ASGI servers (e.g., `uvicorn main:app`).
Running directly via `python main.py` boots the development server.
"""
import sys
from pathlib import Path

# Ensure the backend directory is in the import path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn
from src.main import app

if __name__ == "__main__":
    from src.config import get_settings
    s = get_settings()
    uvicorn.run("src.main:app", host=s.HOST, port=s.PORT, reload=s.DEBUG)