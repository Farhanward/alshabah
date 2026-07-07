from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_POLICY = {"allowed_domains": ["example.com", "carbonflows.store"], "dry_run": True, "max_steps": 8}


def save_policy(path: str | Path, policy: dict | None = None) -> dict:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    data = policy or DEFAULT_POLICY
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"out": str(out.resolve()), "allowed_domains": data["allowed_domains"]}


def load_policy(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        save_policy(p)
    return json.loads(p.read_text(encoding="utf-8"))


def _domain_allowed(url: str, policy: dict) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == domain or host.endswith("." + domain) for domain in policy.get("allowed_domains", []))


def plan_task(task: str, *, url: str = "https://carbonflows.store", policy: dict | None = None) -> dict:
    policy = policy or DEFAULT_POLICY
    if not _domain_allowed(url, policy):
        return {"allowed": False, "reason": "domain not allowed", "steps": []}
    low = task.casefold()
    steps = [{"action": "goto", "url": url}]
    if any(word in low for word in ("contact", "support", "email", "تواصل")):
        steps += [{"action": "click_text", "text": "Contact"}, {"action": "fill", "selector": "message", "value": task}, {"action": "submit", "dry_run": True}]
    elif any(word in low for word in ("search", "find", "ابحث")):
        steps += [{"action": "fill", "selector": "search", "value": task}, {"action": "press", "key": "Enter"}]
    else:
        steps += [{"action": "extract", "target": "page_summary"}]
    return {"allowed": True, "dry_run": bool(policy.get("dry_run", True)), "steps": steps[: int(policy.get("max_steps", 8))], "reason": "planned only; no browser execution"}

