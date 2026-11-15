"""O próprio coverage gate do pipeline também é testado."""

import json

import pytest

from scripts.check_coverage import evaluate, main


def _totals(lines, statements, branches_cov, branches):
    return {
        "covered_lines": lines,
        "num_statements": statements,
        "covered_branches": branches_cov,
        "num_branches": branches,
    }


def test_aprova_quando_linhas_e_branches_atingem_o_minimo():
    ok, _ = evaluate(_totals(85, 100, 80, 100), min_lines=85, min_branches=80)

    assert ok is True


@pytest.mark.parametrize(
    "totals",
    [
        _totals(84, 100, 100, 100),  # linhas abaixo de 85%
        _totals(100, 100, 79, 100),  # branches abaixo de 80%
    ],
)
def test_reprova_quando_qualquer_metrica_fica_abaixo(totals):
    ok, report = evaluate(totals, min_lines=85, min_branches=80)

    assert ok is False
    assert any(line.startswith("[FAIL]") for line in report)


def test_projeto_sem_branches_conta_como_100_porcento():
    ok, report = evaluate(_totals(10, 10, 0, 0), min_lines=85, min_branches=80)

    assert ok is True
    assert "100.00%" in report[1]


def test_main_retorna_codigo_de_saida_do_pipeline(tmp_path, capsys):
    report = tmp_path / "coverage.json"
    report.write_text(json.dumps({"totals": _totals(50, 100, 50, 100)}), encoding="utf-8")

    assert main([str(report)]) == 1
    assert main([str(report), "--lines", "50", "--branches", "50"]) == 0
    assert "Coverage gate reprovado" in capsys.readouterr().err
