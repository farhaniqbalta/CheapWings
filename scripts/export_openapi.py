"""Run from repo root: .venv/bin/python scripts/export_openapi.py.

JSON is a YAML 1.2 subset; the .yaml artifact needs no optional YAML runtime parser.
"""

import json
from pathlib import Path

from cheapwings.api.routes import create_app

schema = create_app().openapi()
Path("contracts/openapi.yaml").write_text(json.dumps(schema, indent=2) + "\n")
