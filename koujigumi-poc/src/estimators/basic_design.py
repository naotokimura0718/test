"""基本設計段階の概算積算ロジック。

鴻治組ヒアリングで判明したメイン機能：
構造図が整う前に、用途×構造×スパンから原単位を推定して概算を出す。
"""

import json
from pathlib import Path

from src.prompts.extract_building_info import (
    EXTRACT_BUILDING_INFO_SYSTEM,
    EXTRACT_BUILDING_INFO_USER,
)
from src.readers.pdf_reader import pdf_to_images
from src.readers.vision_reader import ask_claude_with_images
from src.schemas import (
    BuildingOverview,
    EstimationResult,
    UnitPriceRecord,
)

ESTIMATE_UNIT_SYSTEM = """\
あなたは鴻治組の建築積算ベテランです。基本設計段階で構造図がない段階で、
用途・構造・スパンから過去実績を参照して原単位を推定します。

推定の方針：
1. 類似物件の中央値を基本値とする
2. 対象物件と類似物件の差異（スパン・階数等）で調整する
3. 調整理由を具体的に述べる
4. 信頼度は類似物件との類似度と件数で判断する

重要：
- 類似物件が少ない場合（3件未満）は信頼度を 0.5 以下にする
- 推定の根拠を reasoning に明記する
- 参照した物件IDを reference_projects に列挙する
"""


async def extract_building_overview(pdf_path: Path) -> BuildingOverview:
    """図面PDFから建物概要を抽出（STEP 1）。"""
    images = pdf_to_images(pdf_path, dpi=200, first_page=1, last_page=3)

    return await ask_claude_with_images(
        images=images,
        system_prompt=EXTRACT_BUILDING_INFO_SYSTEM,
        user_prompt=EXTRACT_BUILDING_INFO_USER,
        response_model=BuildingOverview,
    )


def find_similar_projects(
    target: BuildingOverview,
    all_records: list[UnitPriceRecord],
    top_k: int = 10,
) -> list[UnitPriceRecord]:
    """
    類似物件を検索する。

    優先度: 用途一致 > 構造一致 > スパン近接
    """
    # 用途・構造が一致するものを優先
    exact_match = [
        r
        for r in all_records
        if r.usage == target.usage and r.structure == target.structure
    ]

    if len(exact_match) >= top_k:
        # スパンが近いものを選ぶ
        target_span = (target.span_x or 7.0 + target.span_y or 7.0) / 2

        exact_match.sort(
            key=lambda r: abs(r.span_avg - target_span)
        )
        return exact_match[:top_k]

    # 用途のみ一致するものを補完
    usage_match = [
        r
        for r in all_records
        if r.usage == target.usage and r not in exact_match
    ]

    combined = exact_match + usage_match
    return combined[:top_k]


async def estimate_unit_prices(
    target: BuildingOverview,
    reference_records: list[UnitPriceRecord],
) -> list[EstimationResult]:
    """
    原単位を推定する（STEP 5）。

    鴻治組ヒアリングの核心機能：基本設計段階で過去実績から原単位を推定。
    """
    similar = find_similar_projects(target, reference_records, top_k=10)

    reference_text = "\n".join(
        f"- {r.project_id}: {r.usage} {r.structure} {r.floors}F "
        f"延床{r.total_area}m², スパン平均{r.span_avg}m, "
        f"Con {r.concrete_per_area}m³/m², "
        f"鉄筋 {r.rebar_per_area}kg/m², "
        f"型枠 {r.formwork_per_area}m²/m²"
        + (f", 鉄骨 {r.steel_per_area}kg/m²" if r.steel_per_area else "")
        for r in similar
    )

    target_span_avg = None
    if target.span_x and target.span_y:
        target_span_avg = (target.span_x + target.span_y) / 2

    user_prompt = f"""\
対象物件の原単位を推定してください。

【対象物件】
- 用途: {target.usage}
- 構造: {target.structure}
- 階数: 地上{target.floors_above}階
- 延床面積: {target.total_floor_area}m²
- スパン平均: {target_span_avg}m

【類似物件（鴻治組過去実績）】
{reference_text}

上記を踏まえ、コンクリート・鉄筋・型枠・（S造なら）鉄骨の原単位を推定してください。
各項目について EstimationResult を返してください。

JSON配列形式で返してください（list[EstimationResult]）。
"""

    class ResultList(EstimationResult.__config__.arbitrary_types_allowed.__class__):  # type: ignore
        pass

    # list[EstimationResult] を直接返させるためのラッパーモデル
    from pydantic import RootModel

    class EstimationResultList(RootModel[list[EstimationResult]]):
        pass

    results = await ask_claude_with_images(
        images=[],  # 画像不要、テキストのみ
        system_prompt=ESTIMATE_UNIT_SYSTEM,
        user_prompt=user_prompt,
        response_model=EstimationResultList,
    )

    return results.root


def load_reference_records(reference_dir: Path) -> list[UnitPriceRecord]:
    """原単位DBを読み込む。"""
    json_path = reference_dir / "unit_prices.json"
    if not json_path.exists():
        # ダミーデータを返す（開発中）
        return _dummy_records()

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    return [UnitPriceRecord.model_validate(r) for r in data]


def _dummy_records() -> list[UnitPriceRecord]:
    """ダミーの原単位レコード（NDA前の開発用）。"""
    return [
        UnitPriceRecord(
            project_id="DUMMY-001",
            usage="事務所",
            structure="S造",
            floors=6,
            total_area=3500,
            span_avg=7.8,
            completion_year=2023,
            concrete_per_area=0.42,
            rebar_per_area=52,
            formwork_per_area=2.8,
            steel_per_area=120,
        ),
        UnitPriceRecord(
            project_id="DUMMY-002",
            usage="事務所",
            structure="S造",
            floors=5,
            total_area=2800,
            span_avg=7.2,
            completion_year=2022,
            concrete_per_area=0.40,
            rebar_per_area=48,
            formwork_per_area=2.7,
            steel_per_area=115,
        ),
        UnitPriceRecord(
            project_id="DUMMY-003",
            usage="事務所",
            structure="S造",
            floors=7,
            total_area=4200,
            span_avg=8.4,
            completion_year=2024,
            concrete_per_area=0.44,
            rebar_per_area=54,
            formwork_per_area=2.9,
            steel_per_area=122,
        ),
    ]
