from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import TargetManifest
from .oracle import interpret
from .verifier import verify_target


def main() -> int:
    parser = argparse.ArgumentParser(description="Thea exact-head verifier")
    parser.add_argument("manifest", type=Path, help="JSON target manifest")
    parser.add_argument("--oracle", action="store_true", help="run the local Oracle review layer")
    parser.add_argument("--context", type=Path, help="optional UTF-8 context document")
    args = parser.parse_args()

    target = TargetManifest.from_dict(json.loads(args.manifest.read_text(encoding="utf-8")))
    result = verify_target(target)
    output: dict[str, object] = {"thea": result.to_dict()}

    if args.oracle:
        context = args.context.read_text(encoding="utf-8") if args.context else ""
        output["oracle"] = interpret(result, context).to_dict()

    print(json.dumps(output, indent=2, sort_keys=True))
    return 1 if result.verdict.value == "HOLD" else 0


if __name__ == "__main__":
    raise SystemExit(main())
