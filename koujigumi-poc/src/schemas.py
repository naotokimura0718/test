"""データスキーマの定義。"""

from typing import Literal

from pydantic import BaseModel, Field

# ============================================================
# 建物情報
# ============================================================


class BuildingOverview(BaseModel):
    """建物概要（STEP 1の出力）。"""

    project_name: str
    usage: str = Field(description="事務所/住宅/学校/工場/倉庫 等")
    structure: str = Field(description="S造/RC造/SRC造/W造 等")
    floors_above: int = Field(description="地上階数")
    floors_below: int = Field(default=0, description="地下階数")
    total_floor_area: float = Field(description="延床面積 m²")
    building_area: float | None = Field(default=None, description="建築面積 m²")
    max_height: float | None = Field(default=None, description="最高高さ m")
    span_x: float | None = Field(default=None, description="主要スパンX m")
    span_y: float | None = Field(default=None, description="主要スパンY m")


# ============================================================
# 仕上・面積
# ============================================================


class RoomFinish(BaseModel):
    """部屋別の仕上仕様（STEP 2の出力）。"""

    room_name: str
    floor_finish: str
    wall_finish: str
    ceiling_finish: str
    baseboard: str | None = None
    notes: str | None = Field(default=None, description="要確認事項等")


class RoomArea(BaseModel):
    """部屋別の面積（STEP 3の出力）。"""

    room_name: str
    count: int = Field(default=1, description="同仕様の部屋数")
    floor_area: float = Field(description="床面積 m²")
    wall_area: float = Field(description="壁面積 m²（周長×天井高）")
    ceiling_area: float = Field(description="天井面積 m²")
    needs_estimation: bool = Field(default=False, description="求積図がなく推定した場合")


# ============================================================
# 積算
# ============================================================


class UnitPriceRecord(BaseModel):
    """1物件の原単位レコード（過去実績DB用）。"""

    project_id: str
    usage: str
    structure: str
    floors: int
    total_area: float
    span_avg: float = Field(description="主要スパンの平均 m")
    completion_year: int

    concrete_per_area: float = Field(description="コンクリート m³/m²")
    rebar_per_area: float = Field(description="鉄筋 kg/m²")
    formwork_per_area: float = Field(description="型枠 m²/m²")
    steel_per_area: float | None = Field(default=None, description="鉄骨 kg/m²（S造のみ）")


class EstimationResult(BaseModel):
    """原単位推定の結果。"""

    item: str = Field(description="コンクリート/鉄筋/型枠/鉄骨")
    estimated_value: float
    unit: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(description="推定の根拠")
    reference_projects: list[str] = Field(description="参照した過去物件ID")


class CategoryEstimate(BaseModel):
    """工種別の概算。"""

    category: str = Field(description="躯体工事/外装工事/内装仕上工事/電気設備 等")
    amount: int = Field(description="概算額（円）")
    confidence: Literal["高", "中", "低"]
    note: str | None = None


class EstimationReport(BaseModel):
    """概算見積の最終レポート。"""

    building: BuildingOverview
    estimated_units: list[EstimationResult]
    categories: list[CategoryEstimate]
    total_amount: int
    tsubo_cost: int = Field(description="坪単価")
    benchmark_range: str
    benchmark_status: Literal["範囲内", "範囲外（高)", "範囲外（低)"]
    warnings: list[str] = Field(default_factory=list)


# ============================================================
# 構造チェック
# ============================================================


Severity = Literal["critical", "warning", "info"]
CheckCategory = Literal[
    "window_structural",      # サッシ回り構造
    "design_consistency",     # 意匠・構造整合性
    "waterproofing",          # 防水・構造両立
    "simple_check",           # 単純チェック
]


class StructuralIssue(BaseModel):
    """構造チェックの指摘事項。"""

    severity: Severity
    category: CheckCategory
    location: str = Field(description="階・面・部屋を具体的に")
    issue: str = Field(description="1行で問題点")
    detail: str = Field(description="詳細な説明")
    reference: str | None = Field(default=None, description="鴻治組過去事例")
    recommended_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    related_drawings: list[str] = Field(default_factory=list)


class StructuralCheckReport(BaseModel):
    """構造チェックの最終レポート。"""

    project_name: str
    issues: list[StructuralIssue]
    critical_count: int
    warning_count: int
    info_count: int
    overall_assessment: str = Field(description="全体所感")


# ============================================================
# 評価（精度検証）
# ============================================================


class EstimationEvaluation(BaseModel):
    """積算精度の評価結果。"""

    project_id: str
    item: str
    predicted: float
    actual: float  # ground truth
    error_rate: float = Field(description="(predicted - actual) / actual")
    within_target: bool


class StructuralEvaluation(BaseModel):
    """構造チェック精度の評価結果。"""

    project_id: str
    predicted_issues: list[StructuralIssue]

    true_positives: int = Field(description="AIが指摘 & ベテランが正しいと判定")
    false_positives: int = Field(description="AIが指摘 & ベテランが不要と判定")
    false_negatives: int = Field(description="ベテラン指摘 & AIが見落とし")

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0
