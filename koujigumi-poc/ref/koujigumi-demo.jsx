import { useState, useEffect, useRef } from "react";

const C = {
  navy: "#1B365D", teal: "#2E86AB", red: "#DC4444", amber: "#E59500", green: "#10B981",
  bg: "#F7F8FA", card: "#FFFFFF", text: "#1A1A1A", sub: "#555", muted: "#999",
  border: "#E2E5EA", lightBlue: "#EDF6FA", lightAmber: "#FFF6E6", lightRed: "#FDEEEE"
};

// ======= Hearing-derived sample: 広島市内オフィスビル新築工事（基本設計段階）=======
const SAMPLE = {
  project: {
    name: "広島市中区オフィスビル新築工事",
    stage: "基本設計段階",
    usage: "事務所",
    structure: "S造",
    floors: "地上6階",
    totalArea: "3,200",
    buildingArea: "580",
    span: "8.1m × 7.2m",
    note: "構造図・設備図は未確定（基本設計段階で概算要求）",
  },
  // 基本設計段階での推定：用途×構造×スパンから原単位を推定
  estimation: {
    assumedUnits: [
      { item: "コンクリート", basis: "S造6F事務所の類似物件実績", value: "0.42 m³/m²", qty: "1,344 m³", source: "鴻治組過去10件平均" },
      { item: "鉄骨", basis: "スパン8.1×7.2m・事務所用途", value: "118 kg/m²", qty: "377.6 t", source: "類似スパン実績" },
      { item: "鉄筋", basis: "S造事務所の標準配筋", value: "52 kg/m²", qty: "166.4 t", source: "実績範囲内（±10%）" },
      { item: "型枠", basis: "S造事務所の標準", value: "2.8 m²/m²", qty: "8,960 m²", source: "類似物件実績" },
    ],
    categories: [
      { name: "躯体工事", amount: 412_000_000, confidence: "高", note: "過去実績の中央値で推定" },
      { name: "外装工事", amount: 178_000_000, confidence: "中", note: "カーテンウォール想定・仕様未確定" },
      { name: "内装仕上工事", amount: 89_000_000, confidence: "高", note: "仕上表から読取" },
      { name: "電気設備", amount: 128_000_000, confidence: "中", note: "用途原単位で推定（設備図未確定）" },
      { name: "空調設備", amount: 144_000_000, confidence: "中", note: "事務所用途標準" },
      { name: "衛生設備", amount: 67_200_000, confidence: "中", note: "衛生器具数想定" },
      { name: "外構・仮設", amount: 52_800_000, confidence: "低", note: "配置図から概算" },
    ],
    totalAmount: 1_071_000_000,
    tsuboCost: 1_105_000,
    benchmarkRange: "坪単価 1,050,000〜1,200,000円（S造6F事務所の相場）",
    benchmarkStatus: "範囲内",
  },
  // 差別化の核：サッシ回りの構造的成立性チェック
  structuralChecks: [
    {
      severity: "critical",
      location: "3F 南面 会議室",
      issue: "サッシ開口幅2,700mmに対し、左右の壁厚が150mmしか確保されていない",
      detail: "S造の場合、サッシ両端の柱との取り合いで最低300mm以上の納まりが必要。このままでは方立の固定が構造的に不安定。",
      reference: "鴻治組過去類似案件：同様の指摘で設計変更（壁厚250mm追加）",
      action: "設計事務所へ質疑：サッシ位置を200mmずらすか、方立を梁に直接固定する納まりを検討要請",
    },
    {
      severity: "critical",
      location: "1F エントランス 東面",
      issue: "サッシ FIX窓の寸法3,600×2,400mm に対し、意匠図と構造図でブレース位置が矛盾",
      detail: "意匠図ではサッシ中央部に視界を遮るブレースなしだが、構造図では同位置にX型ブレース配置。現状では施工時に意匠変更が必須。",
      reference: "防水・構造の両立には、サッシ外側にブレースを回す必要あり（過去事例3件）",
      action: "意匠・構造の設計整合性を発注者経由で確認",
    },
    {
      severity: "warning",
      location: "2F〜5F 北面",
      issue: "腰窓サッシの下端と梁下端のクリアランスが80mm",
      detail: "通常100mm以上推奨。サッシ下端と梁下端の取り合いで防水処理が困難になる可能性。",
      reference: "一般的なS造事務所での推奨クリアランス100-150mm",
      action: "納まり詳細図を要請、もしくはサッシ高さを調整",
    },
    {
      severity: "info",
      location: "全階 EV前ホール",
      issue: "仕上表にEV前ホールの床仕上記載なし",
      detail: "平面図には「EV前ホール」として部屋が定義されているが、仕上表に対応する行がない。",
      reference: "—",
      action: "設計事務所に床仕上の仕様を確認",
    },
  ],
  // 積算8ステップの進捗
  processSteps: [
    { id: 1, label: "建物概要・スパン把握", status: "done", detail: "設計概要書から用途・構造・スパンを自動抽出" },
    { id: 2, label: "仕上の読み取り", status: "done", detail: "仕上表8部屋分を構造化（信頼度 94%）" },
    { id: 3, label: "面積の算出", status: "done", detail: "求積図から全8室の面積を読取" },
    { id: 4, label: "内装数量の積算", status: "done", detail: "仕上材別に集計完了" },
    { id: 5, label: "躯体数量の概算推定", status: "done", detail: "過去10件の類似物件実績から原単位を推定" },
    { id: 6, label: "設備・外構・仮設概算", status: "done", detail: "用途原単位で按分" },
    { id: 7, label: "集計・見積書生成", status: "done", detail: "工種別内訳を生成" },
    { id: 8, label: "検算＋構造チェック", status: "done", detail: "坪単価検算＋サッシ回り等の構造的成立性をチェック" },
  ],
  // 時間比較
  timing: {
    traditional: "10〜14日",
    ai: "約30分",
    reduction: "約95%",
  },
};

function formatYen(n) {
  return "¥" + n.toLocaleString();
}

function AnimatedNumber({ value, duration = 1500, prefix = "" }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const step = value / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= value) { setDisplay(value); clearInterval(timer); }
      else setDisplay(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [value, duration]);
  return <>{prefix}{display.toLocaleString()}</>;
}

export default function App() {
  const [phase, setPhase] = useState("upload");
  const [currentStep, setCurrentStep] = useState(0);
  const [activeView, setActiveView] = useState("summary");
  const [expandedCat, setExpandedCat] = useState(null);
  const [expandedCheck, setExpandedCheck] = useState(null);
  const fileRef = useRef(null);

  const startAnalysis = () => {
    setPhase("analyzing");
    setCurrentStep(0);
    let step = 0;
    const timer = setInterval(() => {
      step++;
      if (step > SAMPLE.processSteps.length) {
        clearInterval(timer);
        setTimeout(() => setPhase("result"), 500);
      } else {
        setCurrentStep(step);
      }
    }, 700);
  };

  const reset = () => {
    setPhase("upload");
    setCurrentStep(0);
    setActiveView("summary");
    setExpandedCat(null);
    setExpandedCheck(null);
  };

  const critCount = SAMPLE.structuralChecks.filter(c => c.severity === "critical").length;
  const warnCount = SAMPLE.structuralChecks.filter(c => c.severity === "warning").length;
  const infoCount = SAMPLE.structuralChecks.filter(c => c.severity === "info").length;

  return (
    <div style={{ fontFamily: "'Noto Sans JP', 'Helvetica Neue', sans-serif", background: C.bg, minHeight: "100vh", color: C.text }}>
      {/* Header */}
      <div style={{ background: C.navy, padding: "12px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 30, height: 30, borderRadius: 6, background: C.teal, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 700, fontSize: 13 }}>積</div>
          <div>
            <div style={{ color: "#fff", fontSize: 14, fontWeight: 500, letterSpacing: 0.5 }}>建設図面AI 積算・照査システム</div>
            <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 10, marginTop: 1 }}>基本設計段階の概算 × サッシ回り構造チェック</div>
          </div>
        </div>
        <span style={{ color: "rgba(255,255,255,0.5)", fontSize: 11 }}>鴻治組様向けデモ｜AIベストパートナーズ</span>
      </div>

      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "20px 20px 40px" }}>
        {/* ========== Upload Phase ========== */}
        {phase === "upload" && (
          <div>
            <div style={{ textAlign: "center", padding: "40px 20px 20px" }}>
              <div style={{ fontSize: 11, color: C.teal, fontWeight: 600, letterSpacing: 2, marginBottom: 8 }}>DEMO — 基本設計段階 概算積算</div>
              <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 10, color: C.navy }}>設計図面PDFをアップロード</h1>
              <p style={{ color: C.sub, fontSize: 13, marginBottom: 28, lineHeight: 1.7 }}>
                従来 <b style={{ color: C.red }}>10〜14日</b> かかる読み取り・拾い出しを、AIが <b style={{ color: C.green }}>約30分</b> で完了します。<br />
                構造図がない基本設計段階でも、用途・スパンから原単位を推定して概算を出力します。
              </p>

              <div
                onClick={() => fileRef.current?.click()}
                style={{
                  border: `2px dashed ${C.border}`, borderRadius: 10, padding: "40px 24px",
                  cursor: "pointer", background: C.card, maxWidth: 480, margin: "0 auto",
                  transition: "all 0.2s"
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = C.teal; e.currentTarget.style.background = C.lightBlue; }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = C.border; e.currentTarget.style.background = C.card; }}
              >
                <div style={{ fontSize: 36, marginBottom: 10, color: C.muted }}>📄</div>
                <p style={{ fontSize: 13, color: C.sub, marginBottom: 0 }}>PDFをクリックして選択</p>
                <input ref={fileRef} type="file" accept=".pdf" style={{ display: "none" }} onChange={startAnalysis} />
              </div>

              <button onClick={startAnalysis} style={{
                marginTop: 20, padding: "11px 32px", background: C.teal, color: "#fff",
                border: "none", borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: "pointer"
              }}>
                サンプル物件で解析を実行 →
              </button>
            </div>

            {/* サンプル案件情報 */}
            <div style={{ background: C.card, borderRadius: 8, padding: 20, marginTop: 20, border: `1px solid ${C.border}` }}>
              <div style={{ fontSize: 11, color: C.muted, marginBottom: 8, letterSpacing: 1 }}>SAMPLE PROJECT</div>
              <div style={{ fontSize: 16, fontWeight: 600, color: C.navy, marginBottom: 4 }}>{SAMPLE.project.name}</div>
              <div style={{ fontSize: 12, color: C.sub }}>{SAMPLE.project.structure}・{SAMPLE.project.floors}・延床{SAMPLE.project.totalArea}㎡・{SAMPLE.project.stage}</div>
              <div style={{ fontSize: 11, color: C.amber, marginTop: 8, padding: "6px 10px", background: C.lightAmber, borderRadius: 4, display: "inline-block" }}>
                ⚠ {SAMPLE.project.note}
              </div>
            </div>

            {/* 特徴 */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 16 }}>
              <div style={{ background: C.card, borderRadius: 8, padding: 16, border: `1px solid ${C.border}`, borderTop: `3px solid ${C.teal}` }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: C.navy, marginBottom: 6 }}>① 基本設計段階での概算</div>
                <div style={{ fontSize: 11, color: C.sub, lineHeight: 1.6 }}>構造図が整う前に、用途×構造×スパンから原単位を推定。顧客の「2週間で概算を」に応えられます。</div>
              </div>
              <div style={{ background: C.card, borderRadius: 8, padding: 16, border: `1px solid ${C.border}`, borderTop: `3px solid ${C.amber}` }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: C.navy, marginBottom: 6 }}>② 構造的成立性チェック</div>
                <div style={{ fontSize: 11, color: C.sub, lineHeight: 1.6 }}>サッシ回り等「構造的に成立するか」の判断を自動化。単なる間違い指摘ではなく、施工の視点を持った指摘を行います。</div>
              </div>
            </div>
          </div>
        )}

        {/* ========== Analyzing Phase ========== */}
        {phase === "analyzing" && (
          <div style={{ padding: "40px 20px" }}>
            <div style={{ textAlign: "center", marginBottom: 30 }}>
              <div style={{ fontSize: 11, color: C.teal, fontWeight: 600, letterSpacing: 2, marginBottom: 8 }}>ANALYZING</div>
              <h2 style={{ fontSize: 20, fontWeight: 600, color: C.navy, marginBottom: 8 }}>AI解析中</h2>
              <p style={{ fontSize: 12, color: C.sub }}>{SAMPLE.project.name}</p>
            </div>

            <div style={{ maxWidth: 560, margin: "0 auto", background: C.card, borderRadius: 10, padding: "24px 28px", border: `1px solid ${C.border}` }}>
              {SAMPLE.processSteps.map((step, i) => {
                const isDone = i < currentStep;
                const isActive = i === currentStep - 1;
                const isPending = i >= currentStep;
                return (
                  <div key={step.id} style={{
                    display: "flex", alignItems: "flex-start", gap: 14, padding: "10px 0",
                    borderBottom: i < SAMPLE.processSteps.length - 1 ? `1px solid ${C.bg}` : "none",
                    opacity: isPending ? 0.35 : 1,
                    transition: "opacity 0.4s"
                  }}>
                    <div style={{
                      minWidth: 22, height: 22, borderRadius: "50%", marginTop: 2,
                      background: isDone ? C.green : isActive ? C.teal : C.border,
                      color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 11, fontWeight: 600,
                      transition: "background 0.3s"
                    }}>{isDone ? "✓" : step.id}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 500, color: isActive ? C.navy : isDone ? C.green : C.sub }}>
                        {step.label}
                      </div>
                      <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>{step.detail}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ========== Result Phase ========== */}
        {phase === "result" && (
          <div>
            {/* Summary cards */}
            <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr 1fr", gap: 10, marginBottom: 16 }}>
              <div style={{ background: C.navy, color: "#fff", borderRadius: 8, padding: "14px 18px" }}>
                <div style={{ fontSize: 10, opacity: 0.7, marginBottom: 3, letterSpacing: 1 }}>概算工事費（税抜）</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  <AnimatedNumber value={SAMPLE.estimation.totalAmount} prefix="¥" />
                </div>
                <div style={{ fontSize: 10, opacity: 0.6, marginTop: 2 }}>坪単価 ¥{SAMPLE.estimation.tsuboCost.toLocaleString()}</div>
              </div>
              <div style={{ background: C.card, borderRadius: 8, padding: "14px 16px", border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 10, color: C.muted, marginBottom: 3, letterSpacing: 1 }}>処理時間</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: C.teal }}>30分</div>
                <div style={{ fontSize: 10, color: C.red, marginTop: 2 }}>従来 {SAMPLE.timing.traditional}</div>
              </div>
              <div style={{ background: C.card, borderRadius: 8, padding: "14px 16px", border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 10, color: C.muted, marginBottom: 3, letterSpacing: 1 }}>検算</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: C.green, marginTop: 3 }}>✓ 範囲内</div>
                <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>S造事務所相場</div>
              </div>
              <div style={{ background: C.card, borderRadius: 8, padding: "14px 16px", border: `1px solid ${C.border}` }}>
                <div style={{ fontSize: 10, color: C.muted, marginBottom: 3, letterSpacing: 1 }}>構造チェック指摘</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: C.red }}>
                  <span>{critCount}</span>
                  <span style={{ fontSize: 11, color: C.sub, fontWeight: 400, marginLeft: 4 }}>件の重要指摘</span>
                </div>
                <div style={{ fontSize: 10, color: C.muted, marginTop: 2 }}>警告{warnCount}件・情報{infoCount}件</div>
              </div>
            </div>

            {/* Tabs */}
            <div style={{ display: "flex", gap: 0, borderBottom: `1px solid ${C.border}` }}>
              {[
                { id: "summary", label: "建物概要・原単位推定", emphasis: false },
                { id: "estimate", label: "概算見積", emphasis: false },
                { id: "structural", label: "構造チェック", emphasis: true, badge: critCount },
              ].map(t => (
                <button key={t.id} onClick={() => setActiveView(t.id)} style={{
                  padding: "11px 22px", border: "none", cursor: "pointer", fontSize: 13, fontWeight: 500,
                  background: activeView === t.id ? C.card : "transparent",
                  color: activeView === t.id ? C.navy : C.muted,
                  borderBottom: activeView === t.id ? `2px solid ${t.emphasis ? C.red : C.teal}` : "2px solid transparent",
                  borderRadius: "6px 6px 0 0",
                  transition: "all 0.2s",
                  display: "flex", alignItems: "center", gap: 8
                }}>
                  {t.label}
                  {t.badge && <span style={{ background: C.red, color: "#fff", fontSize: 10, padding: "1px 7px", borderRadius: 10, fontWeight: 700 }}>{t.badge}</span>}
                </button>
              ))}
            </div>

            <div style={{ background: C.card, borderRadius: "0 8px 8px 8px", border: `1px solid ${C.border}`, borderTop: "none", padding: 22 }}>
              {/* ========== Summary View ========== */}
              {activeView === "summary" && (
                <div>
                  <div style={{ marginBottom: 22 }}>
                    <div style={{ fontSize: 11, color: C.muted, marginBottom: 4, letterSpacing: 1 }}>STEP 1 - 建物概要</div>
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: C.navy, marginBottom: 10 }}>{SAMPLE.project.name}</h3>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                      <tbody>
                        {[
                          ["用途", SAMPLE.project.usage],
                          ["構造", SAMPLE.project.structure],
                          ["階数", SAMPLE.project.floors],
                          ["延床面積", SAMPLE.project.totalArea + " ㎡"],
                          ["建築面積", SAMPLE.project.buildingArea + " ㎡"],
                          ["標準スパン", SAMPLE.project.span],
                          ["設計段階", SAMPLE.project.stage],
                        ].map(([k, v], i) => (
                          <tr key={k} style={{ background: i % 2 === 0 ? C.bg : C.card }}>
                            <td style={{ padding: "8px 14px", fontWeight: 500, width: 140, color: C.sub }}>{k}</td>
                            <td style={{ padding: "8px 14px", color: C.text }}>{v}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div>
                    <div style={{ fontSize: 11, color: C.muted, marginBottom: 4, letterSpacing: 1 }}>STEP 5 - 原単位推定（ヒアリング反映）</div>
                    <h3 style={{ fontSize: 16, fontWeight: 600, color: C.navy, marginBottom: 6 }}>構造図がない段階で原単位を推定</h3>
                    <p style={{ fontSize: 11, color: C.sub, marginBottom: 12, lineHeight: 1.6 }}>
                      鴻治組様の過去10件の類似物件実績から、用途・構造・スパンが近い物件の原単位を参照して推定しています。
                    </p>
                    <div style={{ overflowX: "auto" }}>
                      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                        <thead>
                          <tr style={{ background: C.navy }}>
                            {["項目", "推定根拠", "原単位", "数量", "参照元"].map(h => (
                              <th key={h} style={{ padding: "10px 12px", color: "#fff", fontWeight: 500, textAlign: "left", whiteSpace: "nowrap", fontSize: 11 }}>{h}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {SAMPLE.estimation.assumedUnits.map((u, i) => (
                            <tr key={i} style={{ background: i % 2 === 0 ? C.bg : C.card }}>
                              <td style={{ padding: "10px 12px", fontWeight: 500 }}>{u.item}</td>
                              <td style={{ padding: "10px 12px", fontSize: 11, color: C.sub }}>{u.basis}</td>
                              <td style={{ padding: "10px 12px", fontFamily: "monospace", color: C.teal, fontWeight: 600 }}>{u.value}</td>
                              <td style={{ padding: "10px 12px", fontFamily: "monospace" }}>{u.qty}</td>
                              <td style={{ padding: "10px 12px", fontSize: 11, color: C.muted }}>{u.source}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div style={{ fontSize: 11, color: C.teal, marginTop: 10, padding: "8px 12px", background: C.lightBlue, borderRadius: 4 }}>
                      💡 ヒアリング反映：「お客さんから2週間で出してと求められる」に応えるため、構造図を待たずに過去実績から推定します
                    </div>
                  </div>
                </div>
              )}

              {/* ========== Estimate View ========== */}
              {activeView === "estimate" && (
                <div>
                  <div style={{ fontSize: 11, color: C.muted, marginBottom: 4, letterSpacing: 1 }}>STEP 7 - 概算見積書</div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: C.navy, marginBottom: 14 }}>工種別内訳</h3>

                  {SAMPLE.estimation.categories.map((cat, ci) => {
                    const confColor = cat.confidence === "高" ? C.green : cat.confidence === "中" ? C.amber : C.red;
                    const confBg = cat.confidence === "高" ? "#E8F5F0" : cat.confidence === "中" ? C.lightAmber : C.lightRed;
                    return (
                      <div key={ci} onClick={() => setExpandedCat(expandedCat === ci ? null : ci)} style={{
                        display: "flex", justifyContent: "space-between", alignItems: "center",
                        padding: "12px 16px", marginBottom: 4,
                        background: ci % 2 === 0 ? C.bg : C.card, borderRadius: 4, cursor: "pointer",
                        border: `1px solid ${C.border}`,
                      }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                          <span style={{ fontSize: 13, fontWeight: 500, minWidth: 160 }}>{cat.name}</span>
                          <span style={{ fontSize: 10, color: confColor, background: confBg, padding: "2px 8px", borderRadius: 3, fontWeight: 600 }}>
                            信頼度 {cat.confidence}
                          </span>
                          <span style={{ fontSize: 11, color: C.muted }}>{cat.note}</span>
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 600, color: C.navy, fontFamily: "monospace" }}>
                          {formatYen(cat.amount)}
                        </div>
                      </div>
                    );
                  })}

                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 18px", background: C.navy, borderRadius: 6, marginTop: 14 }}>
                    <span style={{ color: "#fff", fontWeight: 600, fontSize: 13 }}>概算工事費合計（税抜）</span>
                    <span style={{ color: "#fff", fontSize: 22, fontWeight: 700, fontFamily: "monospace" }}>
                      {formatYen(SAMPLE.estimation.totalAmount)}
                    </span>
                  </div>

                  <div style={{ marginTop: 14, padding: "12px 16px", background: "#F0FDF4", borderRadius: 4, borderLeft: `3px solid ${C.green}` }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: C.green, marginBottom: 4 }}>✓ STEP 8 - 検算結果</div>
                    <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>
                      坪単価 <b>¥{SAMPLE.estimation.tsuboCost.toLocaleString()}/坪</b> は、{SAMPLE.estimation.benchmarkRange} の範囲内。
                      過去10件の類似物件と整合しており、概算として妥当な水準です。
                    </div>
                  </div>
                </div>
              )}

              {/* ========== Structural Check View ========== */}
              {activeView === "structural" && (
                <div>
                  <div style={{ fontSize: 11, color: C.red, marginBottom: 4, letterSpacing: 1 }}>DIFFERENTIATION - 差別化機能</div>
                  <h3 style={{ fontSize: 16, fontWeight: 600, color: C.navy, marginBottom: 6 }}>構造的成立性チェック（サッシ回り中心）</h3>
                  <p style={{ fontSize: 11, color: C.sub, marginBottom: 14, lineHeight: 1.6 }}>
                    明かり/燈等の競合は「間違いの指摘」が中心ですが、本システムは<b>「構造的に成立するかの判断」</b>に踏み込みます。
                    鴻治組様のベテラン判断を学習データ化することで、若手でもベテラン並みの構造チェックが可能になります。
                  </p>

                  {SAMPLE.structuralChecks.map((check, i) => {
                    const sev = check.severity === "critical" ? { c: C.red, bg: C.lightRed, label: "重要指摘", icon: "⚠" }
                      : check.severity === "warning" ? { c: C.amber, bg: C.lightAmber, label: "注意", icon: "△" }
                        : { c: C.teal, bg: C.lightBlue, label: "情報", icon: "ⓘ" };
                    const isExpanded = expandedCheck === i;

                    return (
                      <div key={i} style={{
                        marginBottom: 10,
                        border: `1px solid ${sev.c}33`,
                        borderLeft: `4px solid ${sev.c}`,
                        borderRadius: 6,
                        background: C.card,
                        overflow: "hidden",
                      }}>
                        <div onClick={() => setExpandedCheck(isExpanded ? null : i)} style={{ padding: "12px 16px", cursor: "pointer" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                            <span style={{ fontSize: 10, fontWeight: 700, color: sev.c, background: sev.bg, padding: "3px 9px", borderRadius: 3, letterSpacing: 0.5 }}>
                              {sev.icon} {sev.label}
                            </span>
                            <span style={{ fontSize: 11, color: C.muted, fontFamily: "monospace" }}>{check.location}</span>
                            <span style={{ marginLeft: "auto", fontSize: 11, color: C.muted }}>
                              {isExpanded ? "▲ 閉じる" : "▼ 詳細を見る"}
                            </span>
                          </div>
                          <div style={{ fontSize: 13, fontWeight: 500, color: C.text, lineHeight: 1.5 }}>
                            {check.issue}
                          </div>
                        </div>

                        {isExpanded && (
                          <div style={{ padding: "0 16px 14px", borderTop: `1px solid ${C.bg}` }}>
                            <div style={{ marginTop: 10 }}>
                              <div style={{ fontSize: 10, color: C.muted, fontWeight: 600, letterSpacing: 1, marginBottom: 4 }}>詳細</div>
                              <div style={{ fontSize: 12, color: C.text, lineHeight: 1.6 }}>{check.detail}</div>
                            </div>

                            {check.reference !== "—" && (
                              <div style={{ marginTop: 10, padding: "8px 12px", background: C.lightBlue, borderRadius: 4 }}>
                                <div style={{ fontSize: 10, color: C.teal, fontWeight: 600, letterSpacing: 1, marginBottom: 3 }}>鴻治組様の過去判断を参照</div>
                                <div style={{ fontSize: 11, color: C.sub, lineHeight: 1.5 }}>{check.reference}</div>
                              </div>
                            )}

                            <div style={{ marginTop: 10, padding: "8px 12px", background: sev.bg, borderRadius: 4 }}>
                              <div style={{ fontSize: 10, color: sev.c, fontWeight: 600, letterSpacing: 1, marginBottom: 3 }}>推奨アクション</div>
                              <div style={{ fontSize: 11, color: C.text, lineHeight: 1.5 }}>→ {check.action}</div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}

                  <div style={{ marginTop: 16, padding: "12px 16px", background: C.navy, borderRadius: 6, color: "#fff" }}>
                    <div style={{ fontSize: 11, opacity: 0.7, letterSpacing: 1, marginBottom: 4 }}>なぜこれが差別化か</div>
                    <div style={{ fontSize: 12, lineHeight: 1.6 }}>
                      通常のAIチェックは「寸法が違う」「記号が矛盾」など表層的な指摘にとどまりますが、
                      本システムは<b style={{ color: C.amber }}>「サッシの納まりが構造的に成立するか」「防水・構造の両立ができるか」</b>といった、
                      施工経験がないと気付けない指摘を、鴻治組様の過去判断を学習することで実現します。
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Reset button */}
            <div style={{ textAlign: "center", marginTop: 24 }}>
              <button onClick={reset} style={{
                padding: "9px 22px", background: "transparent", color: C.muted,
                border: `1px solid ${C.border}`, borderRadius: 6, fontSize: 12, cursor: "pointer"
              }}>↺ 最初からやり直す</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
