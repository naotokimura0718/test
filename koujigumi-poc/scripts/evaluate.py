"""精度評価を実行するCLIスクリプト。

Usage:
    python scripts/evaluate.py \
        --predictions results/ \
        --ground-truth data/ground_truth/
"""

import json
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console

from src.config import settings
from src.evaluation.evaluator import (
    evaluate_estimation,
    evaluate_structural_check,
    generate_evaluation_report,
    save_evaluation_report,
)
from src.schemas import EstimationReport, StructuralCheckReport

app = typer.Typer()
console = Console()


@app.command()
def main(
    predictions: Path = typer.Option(
        settings.results_dir, "--predictions", "-p", help="予測結果のディレクトリ"
    ),
    ground_truth: Path = typer.Option(
        settings.ground_truth_dir, "--ground-truth", "-g", help="正解データのディレクトリ"
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="レポート出力パス"),
) -> None:
    """精度評価を実行してレポートを生成。"""
    console.print("\n[bold cyan]=== 精度評価 ===[/bold cyan]\n")

    if not predictions.exists():
        console.print(f"[red]Predictions dir not found: {predictions}[/red]")
        raise typer.Exit(1)
    if not ground_truth.exists():
        console.print(f"[yellow]Ground truth dir not found: {ground_truth}[/yellow]")
        console.print("[yellow]NDA締結前はground truthがありません[/yellow]")
        raise typer.Exit(1)

    # 積算評価
    estimation_evals = []
    estimation_files = list(predictions.glob("estimation_*.json"))
    for pred_file in estimation_files:
        with pred_file.open(encoding="utf-8") as f:
            pred_data = json.load(f)
        # 対応するground truthを探す（命名規則による）
        project_name = pred_data.get("building", {}).get("project_name", "")
        gt_file = ground_truth / f"{project_name}.json"
        if not gt_file.exists():
            console.print(f"[yellow]Skip: No ground truth for {project_name}[/yellow]")
            continue
        with gt_file.open(encoding="utf-8") as f:
            gt = json.load(f)
        # EstimationReport にキャストしきれない場合があるので簡易ハンドリング
        try:
            prediction = EstimationReport.model_validate(pred_data)
        except Exception as e:
            console.print(f"[yellow]Skip {pred_file.name}: {e}[/yellow]")
            continue
        results = evaluate_estimation(
            prediction, gt, target_error=settings.target_estimation_error
        )
        estimation_evals.extend(results)

    # 構造チェック評価
    structural_evals = []
    structural_files = list(predictions.glob("structural_*.json"))
    for pred_file in structural_files:
        with pred_file.open(encoding="utf-8") as f:
            pred_data = json.load(f)
        prediction = StructuralCheckReport.model_validate(pred_data)

        review_file = ground_truth / f"{prediction.project_name}_review.json"
        if not review_file.exists():
            console.print(
                f"[yellow]Skip: No veteran review for {prediction.project_name}[/yellow]"
            )
            continue
        with review_file.open(encoding="utf-8") as f:
            review = json.load(f)

        eval_result = evaluate_structural_check(prediction, review)
        structural_evals.append(eval_result)

    # レポート生成
    report_md = generate_evaluation_report(
        estimation_evals=estimation_evals,
        structural_evals=structural_evals,
        target_estimation_error=settings.target_estimation_error,
        target_precision=settings.target_structural_precision,
        target_recall=settings.target_structural_recall,
    )

    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = settings.results_dir / f"evaluation_report_{timestamp}.md"

    save_evaluation_report(report_md, output)
    console.print(f"\n[green]✓ 評価レポート生成:[/green] {output}\n")
    console.print(report_md)


if __name__ == "__main__":
    app()
