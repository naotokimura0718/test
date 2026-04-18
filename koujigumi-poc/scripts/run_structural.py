"""構造的成立性チェックを実行するCLIスクリプト（差別化の核）。

Usage:
    python scripts/run_structural.py --input data/drawings/sample.pdf --name "広島市オフィスビル"
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.checkers.structural import run_structural_check
from src.config import settings

app = typer.Typer()
console = Console()


async def run_check_async(pdf_path: Path, project_name: str, dry_run: bool) -> None:
    if dry_run:
        console.print("[yellow]🧪 Dry run - API calls skipped[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("構造チェックを実行中...", total=None)
        report = await run_structural_check(pdf_path, project_name)
        progress.update(task, completed=True)

    # サマリ表示
    console.print(
        f"\n[green]✓[/green] 構造チェック完了\n"
        f"  - 重要指摘: [red]{report.critical_count}件[/red]\n"
        f"  - 警告: [yellow]{report.warning_count}件[/yellow]\n"
        f"  - 情報: {report.info_count}件\n"
    )

    console.print(f"[bold]全体所感:[/bold] {report.overall_assessment}\n")

    # 重要指摘のみ表示
    critical_issues = [i for i in report.issues if i.severity == "critical"]
    if critical_issues:
        console.print("[bold red]【重要指摘】[/bold red]\n")
        for i, issue in enumerate(critical_issues, 1):
            console.print(f"  {i}. [bold]{issue.location}[/bold]")
            console.print(f"     問題: {issue.issue}")
            console.print(f"     推奨: {issue.recommended_action}\n")

    # 結果保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = settings.results_dir / f"structural_{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        report.model_dump_json(indent=2), encoding="utf-8"
    )
    console.print(f"[green]📄 結果保存:[/green] {output_path}")


@app.command()
def main(
    input: Path = typer.Option(..., "--input", "-i", help="図面PDFのパス"),
    name: str = typer.Option("対象物件", "--name", "-n", help="物件名"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """構造的成立性チェックを実行。"""
    if not input.exists():
        console.print(f"[red]Error: File not found: {input}[/red]")
        raise typer.Exit(1)

    console.print(
        f"\n[bold cyan]=== 鴻治組 PoC 構造チェック（差別化機能） ===[/bold cyan]\n"
    )
    console.print(f"[dim]対象: {name}[/dim]\n")
    asyncio.run(run_check_async(input, name, dry_run))


if __name__ == "__main__":
    app()
