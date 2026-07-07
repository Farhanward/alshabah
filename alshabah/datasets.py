from __future__ import annotations

import json
from pathlib import Path


def convert_bitext(input_path: str | Path, out_path: str | Path, *, limit: int = 0) -> dict:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = 0
    with Path(input_path).open("r", encoding="utf-8") as handle, out.open("w", encoding="utf-8") as output:
        for line in handle:
            if limit and rows >= limit:
                break
            if not line.strip():
                continue
            rec = json.loads(line)
            output.write(json.dumps({"task": rec.get("instruction") or "", "url": "https://carbonflows.store", "intent": rec.get("intent")}, ensure_ascii=False) + "\n")
            rows += 1
    return {"out": str(out.resolve()), "rows": rows}

