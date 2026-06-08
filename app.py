"""Compatibility wrapper for older `uvicorn app:app` commands.

The real AttendancePro face API lives in `main.py`. Keeping this small wrapper
avoids accidentally running the previous simulated face-matching server.
"""

from main import app
