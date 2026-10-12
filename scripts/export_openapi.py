"""Write the backend's OpenAPI spec to a file, in the exact format committed in frontend/src/api/.

    cd backend
    uv run python ../scripts/export_openapi.py ../frontend/src/api/openapi.json
    cd ../frontend && npm run api:generate

CI runs the same two steps and fails if either file changes, so the typed frontend client can
never drift from the backend.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    out = Path(sys.argv[1])
    out.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
