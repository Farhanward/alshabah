"""Enterprise-layer tests: config, metrics, hardened HTTP planning service."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from alshabah.config import load_config
from alshabah.observability import Metrics, teardown_logging
from alshabah.service import Handler, create_server
from alshabah.version import __version__


class ConfigTests(unittest.TestCase):
    KEYS = ("ALSHABAH_HOME", "ALSHABAH_API_KEY", "ALSHABAH_PORT")

    def setUp(self) -> None:
        self._saved = {k: os.environ.get(k) for k in self.KEYS}

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_defaults(self) -> None:
        for key in self.KEYS:
            os.environ.pop(key, None)
        cfg = load_config()
        self.assertEqual(cfg.port, 8803)
        self.assertFalse(cfg.auth_required)

    def test_env_overrides(self) -> None:
        os.environ["ALSHABAH_API_KEY"] = "k"
        os.environ["ALSHABAH_PORT"] = "9929"
        cfg = load_config()
        self.assertTrue(cfg.auth_required)
        self.assertEqual(cfg.port, 9929)


class MetricsTests(unittest.TestCase):
    def test_percentiles_ordered(self) -> None:
        metrics = Metrics("alshabah", __version__)
        for value in range(1, 41):
            metrics.observe_ms(float(value))
        snap = metrics.snapshot()
        self.assertLessEqual(snap["latency_ms"]["p50"], snap["latency_ms"]["p95"])
        self.assertLessEqual(snap["latency_ms"]["p95"], snap["latency_ms"]["p99"])


class ServiceTestBase(unittest.TestCase):
    api_key = ""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        os.environ["ALSHABAH_API_KEY"] = self.api_key
        os.environ["ALSHABAH_LOG_DIR"] = str(Path(self._tmp.name) / "logs")
        self.server = create_server(host="127.0.0.1", port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        for key in ("ALSHABAH_API_KEY", "ALSHABAH_LOG_DIR"):
            os.environ.pop(key, None)
        if Handler.logger is not None:
            teardown_logging(Handler.logger)
            Handler.logger = None
        self._tmp.cleanup()

    def request(self, path: str, payload: dict | None = None, headers: dict | None = None):
        url = f"http://127.0.0.1:{self.port}{path}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=data, headers=headers or {})
        if data is not None:
            request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))


class OpenServiceTests(ServiceTestBase):
    api_key = ""

    def test_health(self) -> None:
        status, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "alshabah")

    def test_plan_allowed_domain(self) -> None:
        status, body = self.request("/api/plan", {"task": "search for automation pricing", "url": "https://carbonflows.store"})
        self.assertEqual(status, 200)
        self.assertTrue(body["allowed"])
        self.assertTrue(body["dry_run"])
        self.assertGreaterEqual(len(body["steps"]), 1)

    def test_plan_blocks_unlisted_domain(self) -> None:
        status, body = self.request("/api/plan", {"task": "extract prices", "url": "https://evil.example.net"})
        self.assertEqual(status, 200)
        self.assertFalse(body["allowed"])
        self.assertEqual(body["steps"], [])

    def test_plan_missing_task(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/plan", {})
        self.assertEqual(ctx.exception.code, 400)

    def test_metrics_after_plan(self) -> None:
        self.request("/api/plan", {"task": "contact support"})
        status, metrics = self.request("/api/metrics")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(metrics["counters"].get("http_requests_total", 0), 1)


class AuthServiceTests(ServiceTestBase):
    api_key = "shabah-secret"

    def test_rejects_missing_key(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/metrics")
        self.assertEqual(ctx.exception.code, 401)

    def test_accepts_valid_key(self) -> None:
        status, body = self.request("/api/metrics", headers={"X-API-Key": "shabah-secret"})
        self.assertEqual(status, 200)
        self.assertEqual(body["service"], "alshabah")

    def test_health_open_for_probes(self) -> None:
        status, body = self.request("/api/health")
        self.assertEqual(status, 200)
        self.assertTrue(body["auth_required"])

    def test_oversized_body_rejected(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.request("/api/plan", {"task": "x" * 1_200_000}, headers={"X-API-Key": "shabah-secret"})
        self.assertEqual(ctx.exception.code, 413)


if __name__ == "__main__":
    unittest.main()
