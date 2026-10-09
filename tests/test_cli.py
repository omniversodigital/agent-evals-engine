import os
import tempfile
import pytest
from src.cli import run_compare

class DummyArgs:
    def __init__(self, dataset, prompt_a, prompt_b, output):
        self.dataset = dataset
        self.prompt_a = prompt_a
        self.prompt_b = prompt_b
        self.output = output

def test_cli_run_compare():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test_report.md")
        args = DummyArgs(
            dataset="data/golden_dataset.json",
            prompt_a="data/prompt_v1.txt",
            prompt_b="data/prompt_v2.txt",
            output=out_path
        )
        run_compare(args)
        assert os.path.exists(out_path)
        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Relatório Comparativo de Evals A/B" in content
            assert "Pontuação Composta" in content
