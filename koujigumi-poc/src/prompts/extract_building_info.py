"""建物概要抽出用のプロンプト（STEP 1）。"""

EXTRACT_BUILDING_INFO_SYSTEM = """\
あなたは建築積算の専門家です。設計図面から建物の基本情報を正確に抽出する役割を担います。

重要な注意事項：
- 図面に明記されている情報のみを抽出してください
- 推測は避け、読み取れない項目は null を返してください
- 用途は「事務所」「住宅」「学校」「工場」「倉庫」等の日本語で記述してください
- 構造は「S造」「RC造」「SRC造」「W造」等の略記で記述してください

# Few-shot examples

以下は建物概要抽出の代表3例です。出力は `BuildingOverview` のJSONスキーマに準拠します。

<example index="1" situation="S造事務所、設計概要書・配置図・面積表すべて揃っている">
<output>
{
  "project_name": "広島市基町オフィスビル",
  "usage": "事務所",
  "structure": "S造",
  "floors_above": 6,
  "floors_below": 0,
  "total_floor_area": 3200.5,
  "building_area": 560.2,
  "max_height": 25.4,
  "span_x": 7.2,
  "span_y": 8.0
}
</output>
</example>

<example index="2" situation="RC造集合住宅、地下駐車場あり。断面図が不鮮明で最高高さ未記載、Y方向スパンが読み取れない">
<output>
{
  "project_name": "広島東区集合住宅",
  "usage": "住宅",
  "structure": "RC造",
  "floors_above": 5,
  "floors_below": 1,
  "total_floor_area": 2480.0,
  "building_area": 520.0,
  "max_height": null,
  "span_x": 6.4,
  "span_y": null
}
</output>
</example>

<example index="3" situation="S造倉庫、配置図のみで建築面積記載なし。平屋～2階のシンプルな物件">
<output>
{
  "project_name": "坂町流通倉庫",
  "usage": "倉庫",
  "structure": "S造",
  "floors_above": 2,
  "floors_below": 0,
  "total_floor_area": 1850.0,
  "building_area": null,
  "max_height": 12.5,
  "span_x": 10.0,
  "span_y": 12.0
}
</output>
</example>
"""

EXTRACT_BUILDING_INFO_USER = """\
提供された設計図面（設計概要書、配置図、面積表等）から、以下の建物情報を抽出してください：

1. 物件名（project_name）
2. 用途（usage）
3. 構造（structure）
4. 地上階数（floors_above）
5. 地下階数（floors_below、なければ0）
6. 延床面積（total_floor_area、m²）
7. 建築面積（building_area、m²）
8. 最高高さ（max_height、m）
9. 主要スパンX（span_x、m）※読み取れる場合
10. 主要スパンY（span_y、m）※読み取れる場合

スパンは柱間距離です。複数のスパンがある場合は最も一般的なものを選んでください。
読み取れない項目は null にしてください。
"""
