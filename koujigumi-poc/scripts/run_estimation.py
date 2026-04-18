"""積算パイプラインを実行するCLIスクリプト。

Usage:
    python scripts/run_estimation.py --input data/drawings/sample.pdf
    python scripts/run_estimation.py --input data/drawings/sample.pdf --dry-run
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.config import settings
from src.estimators.basic_design import (
    estimate_unit_prices,
    extract_building_overview,
    load_reference_records,
)

app = typer.Typer()
console = Console()


async def run_estimation_async(pdf_path: Path, dry_run: bool) -> None:
    """非同期で積算パイプラインを実行。"""
    if dry_run:
        console.print("[yellow]🧪 Dry run mode - API calls skipped[/yellow]")
        _print_dry_run_result(pdf_path)
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # STEP 1: 建物概要抽出
        task = progress.add_task("STEP 1: 建物概要を抽出中...", total=None)
        building = await extract_building_overview(pdf_path)
        progress.update(task, completed=True)

        console.print("\n[green]✓[/green] 建物概要抽出完了")
        console.print(f"  - 物件名: {building.project_name}")
        console.print(f"  - 用途: {building.usage}")
        console.print(f"  - 構造: {building.structure}")
        console.print(f"  - 階数: 地上{building.floors_above}階")
        console.print(f"  - 延床面積: {building.total_floor_area}m²\n")

        # STEP 5: 原単位推定
        task = progress.add_task("STEP 5: 原単位を推定中...", total=None)
        reference_records = load_reference_records(settings.reference_dir)
        estimates = await estimate_unit_prices(building, reference_records)
        progress.update(task, completed=True)

    # 結果表示
    console.print(f"\n[green]✓[/green] 原単位推定完了 ({len(estimates)}項目)\n")
    for e in estimates:
        console.print(f"  [bold]{e.item}[/bold]: {e.estimated_value} {e.unit}")
        console.print(f"    信頼度: {e.confidence:.0%}")
        console.print(f"    根拠: {e.reasoning}")
        console.print(f"    参照物件: {', '.join(e.reference_projects)}\n")

    # 結果保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = settings.results_dir / f"estimation_{timestamp}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_data = {
        "timestamp": timestamp,
        "input_pdf": str(pdf_path),
        "building": building.model_dump(),
        "estimates": [e.model_dump() for e in estimates],
    }
    output_path.write_text(
        json.dumps(result_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    console.print(f"[green]📄 結果保存:[/green] {output_path}")


def _print_dry_run_result(pdf_path: Path) -> None:
    """Dry runモードでの擬似出力。"""
    console.print(f"[dim]Input: {pdf_path}[/dim]")
    console.print(f"[dim]Model: {settings.claude_model}[/dim]")
    console.print(f"[dim]Reference dir: {settings.reference_dir}[/dim]")
    console.print(f"[dim]Results dir: {settings.results_dir}[/dim]")
    console.print("\n[yellow]Dry run - actual API calls skipped.[/yellow]")


@app.command()
def main(
    pdf: Path = typer.Option(..., "--input", "-i", help="設計図面PDFのパス"),
    dry_run: bool = typer.Option(False, "--dry-run", help="API呼び出しをスキップ"),
) -> None:
    """積算パイプラインを実行する。"""
    if not pdf.exists():
        console.print(f"[red]Error: File not found: {pdf}[/red]")
        raise typer.Exit(1)

    console.print("\n[bold cyan]=== 鴻治組 PoC 積算パイプライン ===[/bold cyan]\n")
    asyncio.run(run_estimation_async(pdf, dry_run))


if __name__ == "__main__":
    app()
