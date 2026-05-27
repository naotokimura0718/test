"""スキーマの基本テスト。"""

import pytest

from src.schemas import (
    BuildingOverview,
    StructuralEvaluation,
    StructuralIssue,
)


def test_building_overview_basic() -> None:
    """基本的な建物概要オブジェクトが作れる。"""
    b = BuildingOverview(
        project_name="テストビル",
        usage="事務所",
        structure="S造",
        floors_above=6,
        total_floor_area=3200.0,
    )
    assert b.project_name == "テストビル"
    assert b.floors_below == 0  # default
    assert b.span_x is None


def test_structural_issue_severity() -> None:
    """構造チェックの指摘が正しく型付けされる。"""
    issue = StructuralIssue(
        severity="critical",
        category="window_structural",
        location="3F 南面 会議室",
        issue="サッシ開口2700mmに対し壁厚150mm",
        detail="方立の固定が構造的に不安定",
        recommended_action="設計変更を依頼",
        confidence=0.92,
    )
    assert issue.severity == "critical"
    assert issue.confidence == 0.92


def test_structural_evaluation_metrics() -> None:
    """Precision/Recallの算出が正しい。"""
    eval_result = StructuralEvaluation(
        project_id="TEST-001",
        predicted_issues=[],
        true_positives=7,
        false_positives=3,
        false_negatives=2,
    )
    # Precision: 7 / (7+3) = 0.7
    assert eval_result.precision == pytest.approx(0.7)
    # Recall: 7 / (7+2) = 0.777...
    assert eval_result.recall == pytest.approx(7 / 9)


def test_structural_evaluation_zero_division() -> None:
    """評価データが空の場合 0.0 を返す。"""
    eval_result = StructuralEvaluation(
        project_id="TEST-002",
        predicted_issues=[],
        true_positives=0,
        false_positives=0,
        false_negatives=0,
    )
    assert eval_result.precision == 0.0
    assert eval_result.recall == 0.0
