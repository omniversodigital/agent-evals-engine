import argparse
import json
import os
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.models import TestCase
from src.runner import AgentRunner
from src.judge import LLMJudge

console = Console()

def main():
    parser = argparse.ArgumentParser(description="Agent Evals Engine CLI - Benchmark & Evaluation Suite for LLMs")
    subparsers = parser.add_subparsers(dest="command")

    # Command: compare
    compare_parser = subparsers.add_parser("compare", help="Compare two prompt versions against a golden dataset")
    compare_parser.add_argument("--dataset", default="data/golden_dataset.json", help="Path to golden dataset JSON")
    compare_parser.add_argument("--prompt-a", default="data/prompt_v1.txt", help="Path to baseline prompt file")
    compare_parser.add_argument("--prompt-b", default="data/prompt_v2.txt", help="Path to challenger prompt file")
    compare_parser.add_argument("--output", default="reports/sample_comparison.md", help="Path to save markdown report")

    args = parser.parse_args()

    if not args.command or args.command == "compare":
        run_compare(args)
    else:
        parser.print_help()

def run_compare(args):
    console.print(Panel.fit("[bold cyan]Agent Evals Engine[/bold cyan] - [yellow]WhatsApp Lead Evaluation Suite[/yellow]"))

    dataset_path = getattr(args, "dataset", "data/golden_dataset.json")
    prompt_a_path = getattr(args, "prompt_a", "data/prompt_v1.txt")
    prompt_b_path = getattr(args, "prompt_b", "data/prompt_v2.txt")
    output_path = getattr(args, "output", "reports/sample_comparison.md")

    if not os.path.exists(dataset_path):
        console.print(f"[bold red]Erro:[/bold red] Dataset '{dataset_path}' não encontrado.")
        sys.exit(1)

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        test_cases = [TestCase(**item) for item in data]

    with open(prompt_a_path, "r", encoding="utf-8") as f:
        prompt_a = f.read()

    with open(prompt_b_path, "r", encoding="utf-8") as f:
        prompt_b = f.read()

    console.print(f"Carregados [bold green]{len(test_cases)}[/bold green] casos de teste do Golden Dataset.")
    console.print("A executar benchmark comparativo A/B...")

    runner = AgentRunner()
    report = runner.compare_prompts(test_cases, prompt_a, prompt_b)

    # Console Summary Table
    table = Table(title="Resultados Agregados de Evals (A/B Test)")
    table.add_column("Métrica", style="cyan")
    table.add_column("Baseline (v1)", justify="center", style="magenta")
    table.add_column("Challenger (v2)", justify="center", style="green")
    table.add_column("Delta", justify="center", style="bold yellow")

    table.add_row("Pontuação Composta (0-100)", f"{report.baseline_score}", f"{report.challenger_score}", f"+{report.score_delta}")
    table.add_row("Casos com Melhoria", "-", f"{report.improvements_count}/{len(test_cases)}", "-")
    table.add_row("Casos com Regressão", "-", f"{report.regressions_count}", "-")
    table.add_row("Veredito CI/CD", "BASELINE", "PASS" if report.is_safe_to_deploy else "FAIL", "SAFE TO DEPLOY" if report.is_safe_to_deploy else "BLOCKED")

    console.print(table)

    # Save Markdown report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report.summary_markdown)

    console.print(f"\n[bold green][OK][/bold green] Relatorio detalhado gravado com sucesso em: [bold]{output_path}[/bold]")
    if report.is_safe_to_deploy:
        console.print("[bold green]Decisao: APROVADO PARA PRODUCAO (Sem regressoes).[/bold green]\n")
    else:
        console.print("[bold red]Decisao: REPROVADO (Regressoes detetadas).[/bold red]\n")

if __name__ == "__main__":
    main()
