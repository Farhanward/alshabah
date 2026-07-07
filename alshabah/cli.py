from __future__ import annotations

import argparse
import json
from pathlib import Path

from .batch import evaluate
from .datasets import convert_bitext
from .planner import load_policy, plan_task, save_policy
from .reports import markdown


def _write_json(path: str | Path, data: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="alshabah", description="الشبح: مخطط فعل ويب dry-run.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init-policy")
    init.add_argument("--out", default="config/policy.json")
    plan = sub.add_parser("plan")
    plan.add_argument("--policy", default="config/policy.json")
    plan.add_argument("--task", required=True)
    plan.add_argument("--url", default="https://carbonflows.store")
    convert = sub.add_parser("convert-bitext")
    convert.add_argument("--input", default="C:/Projects/almandoub/data/external/bitext_customer_support_12000.jsonl")
    convert.add_argument("--out", default="data/benchmarks/alshabah_bitext_tasks.jsonl")
    convert.add_argument("--limit", type=int, default=12000)
    batch = sub.add_parser("batch")
    batch.add_argument("--input", default="data/benchmarks/alshabah_bitext_tasks.jsonl")
    batch.add_argument("--policy", default="config/policy.json")
    batch.add_argument("--json-out", default="reports/alshabah_benchmark.json")
    batch.add_argument("--report", default="reports/alshabah_benchmark.md")
    stress = sub.add_parser("stress")
    stress.add_argument("--input", default="data/benchmarks/alshabah_bitext_tasks.jsonl")
    stress.add_argument("--policy", default="config/policy.json")
    stress.add_argument("--repeat", type=int, default=3)
    stress.add_argument("--json-out", default="reports/alshabah_stress.json")
    stress.add_argument("--report", default="reports/alshabah_stress.md")
    serve = sub.add_parser("serve")
    serve.add_argument("--host")
    serve.add_argument("--port", type=int)
    sub.add_parser("version")
    args = parser.parse_args(argv)
    if args.cmd == "serve":
        from .service import run_server

        run_server(host=args.host, port=args.port)
        return 0
    if args.cmd == "version":
        from .version import __version__

        print(json.dumps({"service": "alshabah", "version": __version__}, ensure_ascii=False))
        return 0
    if args.cmd == "init-policy":
        print(json.dumps(save_policy(args.out), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "plan":
        print(json.dumps(plan_task(args.task, url=args.url, policy=load_policy(args.policy)), ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "convert-bitext":
        print(json.dumps(convert_bitext(args.input, args.out, limit=args.limit), ensure_ascii=False, indent=2))
        return 0
    if args.cmd in {"batch", "stress"}:
        summary = evaluate(args.input, args.policy, repeat=getattr(args, "repeat", 1))
        _write_json(args.json_out, summary)
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(markdown(summary, "تقرير ضغط الشبح" if args.cmd == "stress" else "تقرير الشبح"), encoding="utf-8")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if summary["collapse_check"]["passed"] else 2
    raise ValueError(args.cmd)


if __name__ == "__main__":
    raise SystemExit(main())

