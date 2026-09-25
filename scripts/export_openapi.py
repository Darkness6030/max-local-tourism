"""Export the public API contract without credentials or local environment values."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.app import app

if __name__ == "__main__":
    output = ROOT / "openapi.json"
    output.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n")
    print(f"OpenAPI {app.openapi_version} exported to {output.name}")
