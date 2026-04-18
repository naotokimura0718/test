# 鴻治組 建設図面AI PoC

広島AIサンドボックス採択案件。鴻治組様の設計図面から、基本設計段階での概算積算と、サッシ回り等の構造的成立性チェックを自動化するPoC。

## プロジェクトの背景

2026年4月17日に鴻治組様とヒアリング実施、NDA締結・図面及び拾い出し数量データ提供で合意済み。詳細は `docs/hearing_summary.md` を参照。

**このPoCで検証すること：**

1. **積算精度**：AIが設計図面から拾い出した数量が、鴻治組様の実際の拾い出し数量と誤差◯%以内に収まるか
2. **構造チェック精度**：サッシ回り等の構造的指摘を、鴻治組様のベテラン判断と一致する形で提示できるか

両者を同等に評価する。

## 技術アプローチ

**Phase 1（MVP）**: Claude API主体（AアプローチA）
- マルチモーダルLLM（Claude Sonnet 4）にPDFを直接渡して解析
- プロンプトエンジニアリングで積算・チェックを実現
- 開発速度を優先、精度のベースラインを把握する

**Phase 2（精度不足時）**: カスタムOCR+LLMハイブリッド（アプローチB）
- PDFからテキスト・表を抽出（PyMuPDF等）
- 図面領域を画像処理で検出（CTO松島のCV技術活用）
- 構造化データをLLMに渡して推論させる
- Aで精度が足りない場合のみ移行

Phase 1で精度指標を取り、Bに進むかを意思決定する。

## フォルダ構成

```
koujigumi-poc/
├── README.md               # このファイル
├── CLAUDE.md               # Claude Code向けの作業指示
├── docs/
│   ├── hearing_summary.md       # 4/17ヒアリング議事録の要点
│   ├── tech_notes.md            # 技術メモ・差別化ポイント
│   ├── estimation_process.md    # 積算8ステップの業務理解
│   └── structural_check_spec.md # 構造チェック仕様（サッシ回り中心）
├── src/
│   ├── readers/            # 図面読み取り
│   │   ├── pdf_reader.py
│   │   └── vision_reader.py     # Claude Vision API呼び出し
│   ├── estimators/         # 積算ロジック
│   │   ├── basic_design.py      # 基本設計段階の原単位推定
│   │   └── unit_price_db.py     # 原単位データベース
│   ├── checkers/           # 構造チェック
│   │   ├── structural.py        # サッシ回り等の構造チェック
│   │   └── consistency.py       # 図面間整合性チェック
│   ├── prompts/            # LLMプロンプト集
│   │   ├── extract_building_info.py
│   │   ├── estimate_quantities.py
│   │   └── check_structural.py
│   └── evaluation/         # 精度評価
│       ├── estimation_eval.py   # 積算精度評価
│       └── structural_eval.py   # 構造チェック精度評価
├── data/
│   ├── drawings/           # 鴻治組様から受領する図面PDF（NDA後）
│   ├── ground_truth/       # 鴻治組様の実際の拾い出し数量
│   └── reference/          # 過去実績の原単位データ（一般公開値）
├── scripts/
│   ├── run_estimation.py   # 積算実行スクリプト
│   ├── run_structural.py   # 構造チェック実行スクリプト
│   └── evaluate.py         # 精度評価スクリプト
├── tests/
├── results/                # 実行結果の格納
├── .env.example            # ANTHROPIC_API_KEY等の設定例
├── requirements.txt
└── pyproject.toml
```

## セットアップ

```bash
# Python 3.11+ を推奨
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env に ANTHROPIC_API_KEY=sk-ant-... を記入

# 動作確認（ダミーデータで実行）
python scripts/run_estimation.py --input data/drawings/sample.pdf --dry-run
```

## 開発フロー

### NDA締結前（今やること）

1. フレームワーク構築（`src/` 以下の骨組み）
2. ダミーデータで積算パイプラインを動作確認
3. 既存の `koujigumi-demo.jsx` で使ったサンプルデータを `data/reference/` に配置
4. プロンプトのドラフト作成

### NDA締結後・データ受領後

1. 受領した図面PDFを `data/drawings/` に配置（.gitignore済）
2. 実際の拾い出し数量を `data/ground_truth/` に配置
3. `python scripts/run_estimation.py` で全件実行
4. `python scripts/evaluate.py` で精度評価レポート生成
5. 精度が目標に達しない場合、プロンプト改善 or Approach Bへ移行検討

## 精度目標

| 指標 | 目標値 | 評価方法 |
|------|--------|----------|
| 積算精度（数量誤差） | ±10%以内 | AIの拾い出し数量 vs 鴻治組様の実際の拾い出し数量 |
| 構造チェック Precision | 70%以上 | AIの指摘 vs ベテランが「正しい指摘」と判定した割合 |
| 構造チェック Recall | 50%以上 | ベテランの指摘 vs AIが検出できた割合 |

※ 目標値はPhase 1開始後、鴻治組様とすり合わせて調整する

## 担当

- **PM/CEO**: 木村 直人（株式会社AIベストパートナーズ）
- **CTO/技術リード**: 松島 幸平
- **鴻治組様 窓口**: 檜山 直利 様（建築部）

## 関連リンク

- 広島AIサンドボックス: https://hiroshima-ai.jp/（ダミー）
- 鴻治組様事業計画書: 別途共有
- デモUI: `ref/koujigumi-demo.jsx`

## ライセンス

Proprietary. © 2026 株式会社AIベストパートナーズ
