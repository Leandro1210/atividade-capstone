"""Coverage gate: falha (exit 1) se linhas ou branches ficarem abaixo do mínimo.

O ``--cov-fail-under`` do pytest-cov só verifica um percentual combinado; este
script audita as duas métricas exigidas separadamente a partir do coverage.json.

Uso: python scripts/check_coverage.py [caminho/coverage.json] [--lines 85] [--branches 80]
"""

import argparse
import json
import sys
from pathlib import Path


def evaluate(totals: dict, min_lines: float, min_branches: float) -> tuple[bool, list[str]]:
    statements = totals["num_statements"]
    branches = totals["num_branches"]
    line_pct = 100.0 * totals["covered_lines"] / statements if statements else 100.0
    branch_pct = 100.0 * totals["covered_branches"] / branches if branches else 100.0

    checks = [
        ("Linhas/statements", line_pct, min_lines),
        ("Branches", branch_pct, min_branches),
    ]
    ok = True
    report = []
    for name, value, minimum in checks:
        passed = value >= minimum
        ok &= passed
        status = "OK  " if passed else "FAIL"
        report.append(f"[{status}] {name}: {value:6.2f}% (mínimo {minimum:.0f}%)")
    return ok, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", default="reports/coverage.json")
    parser.add_argument("--lines", type=float, default=85.0)
    parser.add_argument("--branches", type=float, default=80.0)
    args = parser.parse_args(argv)

    totals = json.loads(Path(args.report).read_text(encoding="utf-8"))["totals"]
    ok, report = evaluate(totals, args.lines, args.branches)
    print("\n".join(report))
    if not ok:
        print("Coverage gate reprovado: cobertura abaixo do mínimo exigido.", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
