"""Resume o CSV do Locust (taxa de erro, latência média, p95, RPS) em Markdown.

Uso: python scripts/load_report.py reports/load/wallet_stats.csv [--max-error-rate 1.0]

Sai com código 1 se a taxa de erro das transferências exceder o limite.
"""

import argparse
import csv
import sys
from pathlib import Path


def summarize(rows: list[dict[str, str]]) -> list[dict[str, float | str]]:
    summary = []
    for row in rows:
        requests = int(row["Request Count"])
        failures = int(row["Failure Count"])
        summary.append(
            {
                "name": row["Name"] if row["Type"] else "TOTAL",
                "requests": requests,
                "failures": failures,
                "error_rate": 100.0 * failures / requests if requests else 0.0,
                "avg_ms": float(row["Average Response Time"]),
                "p95_ms": float(row["95%"]) if row["95%"] not in ("", "N/A") else 0.0,
                "rps": float(row["Requests/s"]),
            }
        )
    return summary


def to_markdown(summary: list[dict[str, float | str]]) -> str:
    lines = [
        "| Endpoint | Requisições | Falhas | Taxa de erro | Latência média | p95 | RPS |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for s in summary:
        lines.append(
            f"| {s['name']} | {s['requests']} | {s['failures']} | {s['error_rate']:.2f}% "
            f"| {s['avg_ms']:.1f} ms | {s['p95_ms']:.0f} ms | {s['rps']:.1f} |"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stats_csv", nargs="?", default="reports/load/wallet_stats.csv")
    parser.add_argument("--max-error-rate", type=float, default=1.0)
    args = parser.parse_args(argv)

    with Path(args.stats_csv).open(encoding="utf-8") as fh:
        summary = summarize(list(csv.DictReader(fh)))
    print(to_markdown(summary))

    transfers = [s for s in summary if str(s["name"]).startswith("/transfers")]
    requests = sum(int(s["requests"]) for s in transfers)
    failures = sum(int(s["failures"]) for s in transfers)
    error_rate = 100.0 * failures / requests if requests else 100.0
    print(f"\nTaxa de erro em /transfers: {error_rate:.2f}% (limite {args.max_error_rate}%)")
    return 0 if requests and error_rate <= args.max_error_rate else 1


if __name__ == "__main__":
    sys.exit(main())
