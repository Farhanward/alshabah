from __future__ import annotations


def markdown(summary: dict, title: str = "تقرير الشبح") -> str:
    return "\n".join(
        [
            f"# {title}",
            "",
            f"- المعالجة: `{summary.get('processed', 0)}`",
            f"- مسموح: `{summary.get('allowed', 0)}`",
            f"- ممنوع: `{summary.get('blocked', 0)}`",
            f"- خطوات مخططة: `{summary.get('steps', 0)}`",
            f"- أخطاء: `{summary.get('errors', 0)}`",
            f"- p99: `{summary.get('latency_ms', {}).get('p99', 0):.4f}ms`",
            "",
        ]
    )

