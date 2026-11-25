"""End-to-end tests for the ybench CLI (in-process)."""

import json

import pytest

from yoruba_benchmark.cli import main


def test_run_mock_model_a(capsys):
    assert main(["run", "--mock", "model-a"]) == 0
    out = capsys.readouterr().out
    assert "Model: model-a (60 items)" in out
    assert "Overall" in out
    assert "Factual QA" in out


def test_run_mock_json_output(capsys):
    assert main(["run", "--mock", "model-b", "--json"]) == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["summary"]["model"] == "model-b"
    assert data["summary"]["n"] == 60
    assert len(data["records"]) == 60
    assert data["records"][0]["item_id"] == "yb-faq-01"


def test_run_mock_out_file(tmp_path, capsys):
    out_path = tmp_path / "results-a.json"
    assert main(["run", "--mock", "model-a", "--out", str(out_path)]) == 0
    assert out_path.is_file()
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["summary"]["overall_pass_rate"] == 1.0


def test_run_category_only(capsys):
    assert main(["run", "--mock", "model-a", "--category", "safety"]) == 0
    out = capsys.readouterr().out
    assert "Model: model-a (10 items)" in out


def test_run_needs_mock_or_input(capsys):
    assert main(["run"]) == 2
    assert "needs --mock" in capsys.readouterr().err


def test_run_input_jsonl(tmp_path, capsys):
    path = tmp_path / "responses.jsonl"
    path.write_text(
        json.dumps({"prompt_id": "yb-faq-01", "model": "my-model",
                    "response": "Olú ìlú Nàìjíríà ni Abùjá."}, ensure_ascii=False) + "\n"
        + json.dumps({"prompt_id": "yb-faq-02", "model": "my-model",
                      "response": "Ìbàdàn ni olú ìlú Ìpínlẹ̀ Ọ̀yọ́."}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    assert main(["run", "--input", str(path), "--model", "my-model"]) == 0
    out = capsys.readouterr().out
    assert "Model: my-model (2 items)" in out


def test_run_input_unknown_id(tmp_path, capsys):
    path = tmp_path / "bad.jsonl"
    path.write_text(
        json.dumps({"prompt_id": "yb-nope-01", "model": "m", "response": "x"}) + "\n",
        encoding="utf-8",
    )
    assert main(["run", "--input", str(path), "--model", "m"]) == 2
    assert "unknown prompt_id" in capsys.readouterr().err


def test_compare_mocks(capsys):
    assert main(["compare", "--a", "model-a", "--b", "model-b"]) == 0
    out = capsys.readouterr().out
    assert "Head-to-head: model-a vs model-b (60 items)" in out
    assert "Overall" in out


def test_compare_json(capsys):
    assert main(["compare", "--a", "model-a", "--b", "model-c", "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["model_a"] == "model-a"
    assert data["model_b"] == "model-c"
    assert data["wins_a"] > data["wins_b"]


def test_compare_unknown_model(capsys):
    assert main(["compare", "--a", "model-a", "--b", "gpt-9"]) == 2
    assert "neither a mock model" in capsys.readouterr().err


def test_report_from_saved_file(tmp_path, capsys):
    out_path = tmp_path / "results.json"
    assert main(["run", "--mock", "model-c", "--out", str(out_path)]) == 0
    capsys.readouterr()
    assert main(["report", "--input", str(out_path)]) == 0
    out = capsys.readouterr().out
    assert "Model: model-c (60 items)" in out
    assert "Overall" in out


def test_list_all(capsys):
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "yb-faq-01" in out
    assert "yb-rea-10" in out
    assert "Factual QA (10 items)" in out


def test_list_category(capsys):
    assert main(["list", "--category", "safety"]) == 0
    out = capsys.readouterr().out
    assert "yb-saf-01" in out
    assert "yb-faq-01" not in out


def test_unknown_mock_choice_exits_2():
    with pytest.raises(SystemExit) as excinfo:
        main(["run", "--mock", "gpt-9"])
    assert excinfo.value.code == 2
