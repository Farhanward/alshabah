"""Alshabah web-action planner as a local HTTP service.

``POST /api/plan`` accepts ``{"task": "...", "url": "..."}`` and returns a
dry-run browser/CDP step plan **after** checking the domain allowlist. No
browser is ever launched by this service. Policy loads once at startup
(``ALSHABAH_POLICY``, default ``<project>/config/policy.json``).
"""

from __future__ import annotations

import os
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any

from .config import PROJECT_ROOT
from .http_base import BaseServiceHandler, build_server
from .planner import load_policy, plan_task

_POLICY: dict[str, Any] | None = None


def policy_path() -> Path:
    raw = os.environ.get("ALSHABAH_POLICY", "").strip()
    return Path(raw) if raw else PROJECT_ROOT / "config" / "policy.json"


def _plan_route(data: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    task = str(data.get("task") or "").strip()
    if not task:
        return 400, {"ok": False, "error": "missing 'task'"}
    url = str(data.get("url") or "https://carbonflows.store")
    policy = _POLICY or load_policy(policy_path())
    return 200, {"ok": True, **plan_task(task, url=url, policy=policy)}


class Handler(BaseServiceHandler):
    post_routes = {"/api/plan": staticmethod(_plan_route)}


def create_server(host: str | None = None, port: int | None = None) -> ThreadingHTTPServer:
    global _POLICY
    _POLICY = load_policy(policy_path())
    return build_server(Handler, host=host, port=port)


def run_server(host: str | None = None, port: int | None = None) -> None:
    from .version import __version__

    server = create_server(host=host, port=port)
    print(f"alshabah service v{__version__}: http://{server.server_address[0]}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
