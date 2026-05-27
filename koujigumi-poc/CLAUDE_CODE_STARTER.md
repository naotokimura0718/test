# Claude Code で最初に送るプロンプト

このプロジェクトを Claude Code で開いて、以下を最初のメッセージとして送ってください。

---

## 推奨スタータープロンプト

```
CLAUDE.md と docs/hearing_summary.md、docs/tech_notes.md を読んで、
プロジェクトの状況を把握してください。

現在の状況:
- 2026年4月17日に鴻治組様とヒアリング完了
- NDA締結・データ提供で合意済み
- 実データはまだ手元に届いていない（NDA送付中）
- コードのスケルトンは構築済み

まず以下を確認してください:
1. requirements.txt のライブラリを pip install できるか
2. tests/ を pytest で実行できるか（スキーマテスト）
3. scripts/run_estimation.py --dry-run が動作するか

その後、以下のうち優先度の高いものから進めます:
A) プロンプト改善（src/prompts/check_structural.py のfew-shot examples追加）
B) ダミーPDFでの動作確認（data/reference/ にダミー図面を置いて通しテスト）
C) 評価スクリプトの整備（scripts/evaluate.py の動作確認）

どれから始めたいか聞いてください。
```

---

## 代替：最初のタスクを具体指示するパターン

実データが届くまでにプロンプトを磨き込みたい場合：

```
CLAUDE.md を読んでプロジェクト文脈を把握した後、
src/prompts/check_structural.py を見てください。

現在 few-shot examples が空なので、
docs/hearing_summary.md と docs/structural_check_spec.md の事例をもとに、
以下の3つの指摘パターンを few-shot example として追加してください:

1. サッシ開口幅と壁厚の不整合（critical）
2. 意匠図と構造図のブレース位置矛盾（critical）
3. 梁下端とサッシ上端のクリアランス不足（warning）

各 example は実際の鴻治組案件の雰囲気を出しつつ、
StructuralIssue のスキーマに厳密に従う JSON で記述してください。

プロンプトに含める際は、トークン消費量も意識してください。
```

---

## コミット前にやること

1. `pytest tests/` でテストが通ることを確認
2. `ruff check src/ scripts/` でリントが通ることを確認
3. `mypy src/` で型チェックが通ることを確認
4. `.env` がコミット対象に含まれていないことを確認（`git status` で確認）
5. `data/drawings/` `data/ground_truth/` の中身がコミットされていないことを確認

---

## 進捗管理

作業が進んだら CLAUDE.md の「現在のステータス」を Claude Code に更新させてください。

```
CLAUDE.md の「現在のステータス」を更新してください。
今日やったこと: [...]
次にやること: [...]
```

---

## 鴻治組様からデータを受領したら

```
鴻治組様から以下のデータを受領しました:
- 図面PDF: data/drawings/project_a.pdf
- 拾い出し数量: data/ground_truth/project_a.json

このデータで PoC を実行し、精度評価レポートを生成してください。

実行手順:
1. python scripts/run_estimation.py -i data/drawings/project_a.pdf
2. python scripts/run_structural.py -i data/drawings/project_a.pdf -n "物件A"
3. python scripts/evaluate.py
4. 生成されたレポート (results/evaluation_report_*.md) の内容を要約

結果を見て、精度が目標に達しているか判断し、
達していなければプロンプト改善の具体案を3つ提案してください。
```
