"""精度評価モジュール。

積算精度と構造チェック精度の両方を同等に評価する。
"""

import json
from pathlib import Path
from statistics import mean, median

from src.schemas import (
    EstimationEvaluation,
    EstimationReport,
    StructuralCheckReport,
    StructuralEvaluation,
    StructuralIssue,
)


def evaluate_estimation(
    prediction: EstimationReport,
    ground_truth: dict[str, float],
    target_error: float = 0.10,
) -> list[EstimationEvaluation]:
    """
    積算結果を正解データと比較して精度を算出。

    Args:
        prediction: AIが出した積算レポート
        ground_truth: 鴻治組様の実際の拾い出し数量
            例: {"concrete_m3": 1320.0, "rebar_t": 165.4, ...}
        target_error: 許容誤差（デフォルト 10%）

    Returns:
        項目ごとの評価結果リスト
    """
    results = []
    project_id = prediction.building.project_name

    for estimate in prediction.estimated_units:
        key = _normalize_item_key(estimate.item)
        if key not in ground_truth:
            continue

        actual = ground_truth[key]
        # estimated_value は原単位なので、数量に変換する必要あり
        # （MVPでは estimate.estimated_value を「数量」として扱う簡易実装）
        predicted = estimate.estimated_value * prediction.building.total_floor_area

        error_rate = (predicted - actual) / actual if actual > 0 else 0
        within = abs(error_rate) <= target_error

        results.append(
            EstimationEvaluation(
                project_id=project_id,
                item=estimate.item,
                predicted=predicted,
                actual=actual,
                error_rate=error_rate,
                within_target=within,
            )
        )

    return results


def _normalize_item_key(item: str) -> str:
    """項目名を正規化する。"""
    mapping = {
        "コンクリート": "concrete_m3",
        "鉄筋": "rebar_t",
        "型枠": "formwork_m2",
        "鉄骨": "steel_t",
    }
    return mapping.get(item, item)


def evaluate_structural_check(
    prediction: StructuralCheckReport,
    veteran_review: list[dict],
) -> StructuralEvaluation:
    """
    構造チェック結果をベテランレビューと比較。

    veteran_review の形式:
    [
        {
            "issue_id": 0,
            "judgment": "correct" | "unnecessary" | "missing",
            "notes": "...",
        },
        ...
    ]

    - correct: AIの指摘が正しい（TP）
    - unnecessary: AIの指摘が不要（FP）
    - missing: AIが見落とした指摘（FN）
    """
    tp = sum(1 for r in veteran_review if r["judgment"] == "correct")
    fp = sum(1 for r in veteran_review if r["judgment"] == "unnecessary")
    fn = sum(1 for r in veteran_review if r["judgment"] == "missing")

    return StructuralEvaluation(
        project_id=prediction.project_name,
        predicted_issues=prediction.issues,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
    )


def generate_evaluation_report(
    estimation_evals: list[EstimationEvaluation],
    structural_evals: list[StructuralEvaluation],
    target_estimation_error: float = 0.10,
    target_precision: float = 0.70,
    target_recall: float = 0.50,
) -> str:
    """
    評価レポートをMarkdown形式で生成する。
    """
    md = ["# 精度評価レポート\n"]

    # ============ 積算精度 ============
    md.append("## 1. 積算精度\n")
    if estimation_evals:
        total = len(estimation_evals)
        within_count = sum(1 for e in estimation_evals if e.within_target)
        hit_rate = within_count / total

        errors = [abs(e.error_rate) for e in estimation_evals]

        md.append(f"- 評価件数: {total}")
        md.append(f"- 目標達成率: {hit_rate:.1%} ({within_count}/{total})")
        md.append(f"- 平均誤差: {mean(errors):.1%}")
        md.append(f"- 中央値誤差: {median(errors):.1%}")
        md.append(f"- 目標値: ±{target_estimation_error:.0%}以内\n")

        md.append("### 詳細\n")
        md.append("| 物件 | 項目 | 予測 | 実績 | 誤差 | 目標達成 |")
        md.append("|------|------|------|------|------|---------|")
        for e in estimation_evals:
            status = "✓" if e.within_target else "✗"
            md.append(
                f"| {e.project_id} | {e.item} | {e.predicted:.1f} | "
                f"{e.actual:.1f} | {e.error_rate:+.1%} | {status} |"
            )
        md.append("")
    else:
        md.append("*評価データなし*\n")

    # ============ 構造チェック精度 ============
    md.append("## 2. 構造チェック精度\n")
    if structural_evals:
        total_tp = sum(e.true_positives for e in structural_evals)
        total_fp = sum(e.false_positives for e in structural_evals)
        total_fn = sum(e.false_negatives for e in structural_evals)

        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        md.append(f"- 評価物件数: {len(structural_evals)}")
        md.append(f"- True Positive: {total_tp}")
        md.append(f"- False Positive: {total_fp}")
        md.append(f"- False Negative: {total_fn}")
        md.append(f"- **Precision**: {precision:.1%} (目標 {target_precision:.0%})")
        md.append(f"- **Recall**: {recall:.1%} (目標 {target_recall:.0%})")
        md.append(f"- F1 Score: {f1:.1%}\n")

        precision_ok = precision >= target_precision
        recall_ok = recall >= target_recall
        overall_ok = precision_ok and recall_ok

        if overall_ok:
            md.append("### ✅ 目標達成\n\n精度指標は両方とも目標をクリアしています。")
        else:
            md.append("### ⚠ 目標未達\n")
            if not precision_ok:
                md.append(f"- Precision が目標を下回っています ({precision:.1%} < {target_precision:.0%})")
                md.append("  - 誤検出が多い。プロンプトで除外条件を強化すべき")
            if not recall_ok:
                md.append(f"- Recall が目標を下回っています ({recall:.1%} < {target_recall:.0%})")
                md.append("  - 見落としが多い。チェック観点を増やす、または Approach B を検討")
    else:
        md.append("*評価データなし*\n")

    # ============ サマリ・推奨アクション ============
    md.append("\n## 3. 総合判断と推奨アクション\n")

    estimation_ok = (
        estimation_evals
        and sum(1 for e in estimation_evals if e.within_target) / len(estimation_evals) >= 0.7
    )
    structural_ok = structural_evals and all(
        (e.precision >= target_precision and e.recall >= target_recall)
        for e in structural_evals
    )

    if estimation_ok and structural_ok:
        md.append("**✅ Phase 1 (Approach A) で目標精度を達成。**")
        md.append("- 本格開発に進むことを推奨")
        md.append("- プロンプトのリファインを継続")
    else:
        md.append("**⚠ Phase 1 で目標未達の項目あり。以下を検討：**")
        md.append("")
        if not estimation_ok:
            md.append("- 積算精度の改善：")
            md.append("  1. プロンプトのfew-shot examplesを追加")
            md.append("  2. 原単位DBを拡充（より多くの類似物件を参照）")
            md.append("  3. Approach B（OCR+LLMハイブリッド）への移行検討")
        if not structural_ok:
            md.append("- 構造チェック精度の改善：")
            md.append("  1. 鴻治組様の過去指摘事例をfew-shotに追加")
            md.append("  2. サッシ回り特化のプロンプトに分離")
            md.append("  3. 図面間クロスリファレンスの強化")

    return "\n".join(md)


def save_evaluation_report(
    report_md: str,
    output_path: Path,
) -> None:
    """評価レポートをファイルに保存。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_md, encoding="utf-8")
