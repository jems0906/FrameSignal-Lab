import { StrictMode, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, ArrowDownToLine, ArrowRight, Check, ChevronRight, CircleHelp, ClipboardCheck, Database, FlaskConical, LoaderCircle, Play, RefreshCw, ShieldCheck, SlidersHorizontal, X } from 'lucide-react';
import { CartesianGrid, ErrorBar, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import type { Analysis, Candidate, Effect, Metric, Operating, Suite } from './types';
import './styles.css';

const candidates: Candidate[] = ['qualified_starts', 'viewing_days'];
const labels: Record<Metric, string> = { qualified_starts: 'Qualified starts', viewing_days: 'Viewing days', watch_minutes: 'Watch time', completion: 'Completion', returned_d29_56: 'Later return' };
const scenarioLabels: Record<string, string> = { helpful: 'Helpful', unrelated: 'Unrelated', misleading: 'Misleading' };
const colors: Record<string, string> = { helpful: '#19765c', unrelated: '#6b7280', misleading: '#bf395a' };
const decimal = (value: number | null | undefined, digits = 2) => value == null ? 'Not estimable' : value.toLocaleString('en-US', { maximumFractionDigits: digits, minimumFractionDigits: digits });
const signed = (value: number | null | undefined, digits = 2) => value == null ? 'Not estimable' : `${value > 0 ? '+' : ''}${decimal(value, digits)}`;
const pct = (value: number) => `${decimal(value * 100, 1)}%`;

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal });
  if (!response.ok) throw new Error(`Analysis request failed (${response.status}). Check the local API and retry.`);
  return response.json();
}

function download(data: unknown, filename: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

function Interval({ effect, percentage = false }: { effect: Effect; percentage?: boolean }) {
  const factor = percentage ? 100 : 1;
  const lower = (effect.lower ?? 0) * factor;
  const upper = (effect.upper ?? 0) * factor;
  const estimate = (effect.effect ?? 0) * factor;
  const extent = Math.max(Math.abs(lower), Math.abs(upper), 0.01) * 1.2;
  const position = (value: number) => `${50 + value / extent * 50}%`;
  if (effect.effect == null) return <span>Not estimable</span>;
  return <div className="interval" aria-label={`Effect ${decimal(estimate)}, interval ${decimal(lower)} to ${decimal(upper)}`}>
    <div className="interval-track"><i className="zero" /><i className="range" style={{ left: position(lower), width: `${(upper - lower) / extent * 50}%` }} /><i className="point" style={{ left: position(estimate) }} /></div>
    <div className="interval-label"><span>{signed(lower)}</span><span>{signed(upper)}{percentage ? ' pp' : ''}</span></div>
  </div>;
}

const definitions: Record<Metric, { population: string; numerator: string; denominator: string; aggregation: string; window: string; limitations: string; decision: string }> = {
  qualified_starts: { population: 'All registered, assigned households, including non-viewers.', numerator: 'Viewing events with at least 2 minutes watched.', denominator: 'All assigned households in each arm.', aggregation: 'Count events per household, then average households.', window: 'Days 0-13 after assignment; sensitivity: days 0-6.', limitations: 'Easy to inflate with presentation or exposure. Repeated title starts count separately. Not a return surrogate by assumption.', decision: 'Primary short-term candidate for screening a presentation policy; higher intended to be better.' },
  viewing_days: { population: 'All registered, assigned households, including non-viewers.', numerator: 'Distinct days with at least one qualified viewing event.', denominator: 'All assigned households in each arm.', aggregation: 'Distinct household-days per household, then average.', window: 'Days 0-13 after assignment; sensitivity: days 0-6.', limitations: 'Saturates at 14 and can reward low-value repeated visits. Calendar window and availability matter.', decision: 'Predefined alternative engagement candidate; higher intended to be better.' },
  watch_minutes: { population: 'All registered, assigned households, including non-viewers.', numerator: 'Total viewed minutes, including events below 2 minutes.', denominator: 'All assigned households in each arm.', aggregation: 'Sum minutes per household, then average.', window: 'Days 0-13 after assignment.', limitations: 'Sensitive to long runtimes, genre mix, unequal exposure, and high-use households. Does not measure artistic value.', decision: 'Diagnostic of consumption intensity; higher intended to be better, not necessarily beneficial.' },
  completion: { population: 'Households with at least one qualified start in the assigned arm.', numerator: 'Starter households with any qualified event watching at least 90% of its title runtime.', denominator: 'Starter households in each arm, not all assigned households.', aggregation: 'Household-level any-completion ratio among starters; complete-household bootstrap.', window: 'Events during days 0-13; completion is within one event.', limitations: 'Starting occurs after assignment. Arms select different populations; this is not a clean ITT causal effect. Not per-title completion.', decision: 'Descriptive viewing-depth diagnostic only; higher intended to be better.' },
  returned_d29_56: { population: 'All registered, assigned households, including non-viewers.', numerator: 'Households with a simulated service return on days 29-56 inclusive.', denominator: 'All assigned households in each arm.', aggregation: 'Binary household outcome, then average; treatment minus control.', window: 'Days 29-56 after assignment; fixed horizon.', limitations: 'Fictional, fully observed service-return outcome. Not Netflix retention, subscription survival, or a title-quality effect.', decision: 'Primary target for presentation-policy decisions. Higher is better; practical effect threshold: +2 percentage points.' },
};

function MetricDialog({ metric, close }: { metric: Metric; close: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { dialog.current?.showModal(); }, []);
  const card = definitions[metric];
  return <dialog ref={dialog} className="metric-dialog" onCancel={close} onClick={event => { if (event.target === dialog.current) close(); }}>
    <div className="dialog-heading"><div><span className="eyebrow">Metric definition</span><h2>{labels[metric]}</h2></div><button className="icon-button" onClick={close} aria-label="Close metric definition" title="Close"><X size={20} /></button></div>
    <dl>{Object.entries(card).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}<div><dt>Missingness</dt><dd>No viewing is zero for ITT metrics, not missing. Non-starters have undefined completion. Return is fully observed; real missing outcomes would need a separate plan.</dd></div></dl>
  </dialog>;
}

function EvidenceTable({ data, open }: { data: Analysis; open: (metric: Metric) => void }) {
  return <div className="table-scroll"><table className="evidence-table"><thead><tr><th>Metric / population</th><th>Control</th><th>Policy</th><th>Effect</th><th>Uncertainty interval</th><th>Evidence</th></tr></thead><tbody>
    {(['qualified_starts', 'viewing_days', 'watch_minutes', 'completion', 'returned_d29_56'] as Metric[]).map(metric => {
      const result = data.metrics[metric];
      const percent = metric === 'completion' || metric === 'returned_d29_56';
      const factor = percent ? 100 : 1;
      const positive = result.lower != null && result.lower > 0;
      const negative = result.upper != null && result.upper < 0;
      return <tr key={metric} className={metric === 'returned_d29_56' ? 'target-row' : ''}><td><button className="metric-link" onClick={() => open(metric)}>{labels[metric]}<CircleHelp size={13} /></button><small>{result.causal ? 'All assigned households' : 'Starters only · descriptive'}</small></td><td>{decimal(result.control_mean == null ? null : result.control_mean * factor)}{percent && '%'}</td><td>{decimal(result.treatment_mean == null ? null : result.treatment_mean * factor)}{percent && '%'}</td><td className="mono">{signed(result.effect == null ? null : result.effect * factor)}<small>{percent ? 'percentage points' : result.unit}</small></td><td><Interval effect={result} percentage={percent} /><small>{metric === 'completion' ? '95% household bootstrap' : candidates.includes(metric as Candidate) ? '97.5% Bonferroni interval' : '95% household interval'}</small></td><td><span className={`status ${!result.causal ? 'neutral' : negative ? 'negative' : positive ? 'positive' : 'neutral'}`}>{!result.causal ? 'Selected sample' : negative ? 'Decrease' : positive ? 'Increase' : 'Unresolved'}</span></td></tr>;
    })}
  </tbody></table></div>;
}

function ExperimentPlot({ suite, candidate, split }: { suite: Suite; candidate: Candidate; split: string }) {
  const rows = suite.experiments.filter(row => row.split === split);
  const plotRows = rows.map(row => ({ ...row, x: row.effects[candidate].effect, y: (row.effects.returned_d29_56.effect ?? 0) * 100,
    xError: [(row.effects[candidate].effect ?? 0) - (row.effects[candidate].lower ?? 0), (row.effects[candidate].upper ?? 0) - (row.effects[candidate].effect ?? 0)],
    yError: [((row.effects.returned_d29_56.effect ?? 0) - (row.effects.returned_d29_56.lower ?? 0)) * 100, ((row.effects.returned_d29_56.upper ?? 0) - (row.effects.returned_d29_56.effect ?? 0)) * 100],
  }));
  return <div className="scatter-wrap" role="img" aria-label={`${split} experiments: ${labels[candidate]} treatment effect versus later return treatment effect, including intervals`}>
    <ResponsiveContainer width="100%" height="100%"><ScatterChart margin={{ top: 24, right: 30, bottom: 28, left: 4 }}>
      <CartesianGrid stroke="#e5e8e3" strokeDasharray="3 5" />
      <XAxis type="number" dataKey="x" name={labels[candidate]} domain={['auto', 'auto']} tick={{ fontSize: 11 }} label={{ value: `${labels[candidate]} effect / household`, position: 'bottom', offset: 12, fontSize: 11 }} />
      <YAxis type="number" dataKey="y" name="Return effect" unit=" pp" domain={[-16, 16]} tick={{ fontSize: 11 }} width={64} />
      <ReferenceLine y={0} stroke="#8a938b" strokeWidth={1.5} /><ReferenceLine x={0} stroke="#8a938b" />
      <ReferenceLine y={2} stroke="#19765c" strokeDasharray="4 4" label={{ value: 'Practical threshold +2 pp', position: 'insideTopRight', fill: '#19765c', fontSize: 10 }} />
      <Tooltip cursor={{ strokeDasharray: '3 3' }} content={({ active, payload }) => {
        const row = payload?.[0]?.payload;
        return active && row ? <div className="chart-tooltip"><strong>{row.id}</strong><span>{scenarioLabels[row.scenario]} · strength {row.strength}</span><span>Candidate: {signed(row.x)}</span><span>Return: {signed(row.y)} pp</span></div> : null;
      }} />
      {Object.entries(colors).map(([scenario, color]) => <Scatter key={scenario} name={scenarioLabels[scenario]} data={plotRows.filter(row => row.scenario === scenario)} fill={color} isAnimationActive={false}><ErrorBar dataKey="xError" direction="x" stroke={color} strokeWidth={1} width={3} /><ErrorBar dataKey="yError" direction="y" stroke={color} strokeWidth={1} width={3} /></Scatter>)}
    </ScatterChart></ResponsiveContainer>
  </div>;
}

function App() {
  const [tab, setTab] = useState('overview');
  const [scenario, setScenario] = useState('helpful');
  const [n, setN] = useState('2000');
  const [seed, setSeed] = useState('20261031');
  const [data, setData] = useState<Analysis | null>(null);
  const [suite, setSuite] = useState<Suite | null>(null);
  const [operating, setOperating] = useState<Operating | null>(null);
  const [loading, setLoading] = useState(false);
  const [suiteLoading, setSuiteLoading] = useState(false);
  const [operatingLoading, setOperatingLoading] = useState(false);
  const [error, setError] = useState('');
  const [suiteError, setSuiteError] = useState('');
  const [operatingError, setOperatingError] = useState('');
  const [metric, setMetric] = useState<Metric | null>(null);
  const [candidate, setCandidate] = useState<Candidate>('qualified_starts');
  const [split, setSplit] = useState('heldout');
  const [diagnosticMetric, setDiagnosticMetric] = useState<Candidate | 'watch_minutes'>('watch_minutes');
  const abort = useRef<AbortController | null>(null);
  const requestVersion = useRef(0);

  async function run(nextScenario = scenario) {
    const size = Number(n), seedValue = Number(seed);
    if (!Number.isInteger(size) || size < 100 || size > 20000 || !Number.isInteger(seedValue) || seedValue < 0 || seedValue > 2147483647) {
      setError('Use 100-20,000 households and a nonnegative integer seed up to 2,147,483,647.');
      return;
    }
    abort.current?.abort();
    const controller = new AbortController();
    abort.current = controller;
    const version = ++requestVersion.current;
    setLoading(true); setError('');
    try { setData(await get<Analysis>(`/api/analysis?scenario=${nextScenario}&n=${size}&seed=${seedValue}`, controller.signal)); }
    catch (exception) { if (!(exception instanceof DOMException && exception.name === 'AbortError')) setError((exception as Error).message); }
    finally { if (version === requestVersion.current) setLoading(false); }
  }

  async function loadSuite() {
    setSuiteLoading(true); setSuiteError('');
    try { setSuite(await get<Suite>('/api/validation')); } catch (exception) { setSuiteError((exception as Error).message); }
    finally { setSuiteLoading(false); }
  }

  async function loadOperating() {
    setOperatingLoading(true); setOperatingError('');
    try { setOperating(await get<Operating>('/api/operating')); } catch (exception) { setOperatingError((exception as Error).message); }
    finally { setOperatingLoading(false); }
  }

  useEffect(() => { void run(); return () => { abort.current?.abort(); }; }, []);
  useEffect(() => { if (tab === 'proxy' && !suite && !suiteLoading && !suiteError) void loadSuite(); }, [tab]);
  useEffect(() => { if (tab === 'diagnostics' && !operating && !operatingLoading && !operatingError) void loadOperating(); }, [tab]);

  const stale = data && (data.scenario !== scenario || data.n !== Number(n) || data.seed !== Number(seed));
  const target = data?.metrics.returned_d29_56;
  const agreement = suite?.agreement[split][candidate];

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="FrameSignal Lab home"><span className="brand-symbol"><Activity size={24} /></span><span>FrameSignal<span className="brand-lab">LAB</span></span></a>
      <div className="workspace-label">MEASUREMENT SCIENCE</div>
      <nav aria-label="Workbench views">{[
        ['overview', 'Experiment', FlaskConical], ['proxy', 'Proxy validation', Activity], ['diagnostics', 'Diagnostics', SlidersHorizontal], ['design', 'Research design', ClipboardCheck],
      ].map(([id, title, Icon]) => { const NavIcon = Icon as typeof Activity; return <button key={id as string} className={tab === id ? 'nav-item active' : 'nav-item'} onClick={() => setTab(id as string)} aria-current={tab === id ? 'page' : undefined}><NavIcon size={18} /><span>{title as string}</span>{tab === id && <ChevronRight size={15} />}</button>; })}<a className="nav-item" href={import.meta.env.VITE_METRICSTEWARD_URL ?? 'http://localhost:5174'}><Database size={18} /><span>MetricSteward</span><ChevronRight size={15} /></a></nav>
      <div className="sidebar-bottom"><div className="synthetic-mark"><Database size={15} />Synthetic data only</div><p>Fictional policies.<br />Real statistical questions.</p><span className="mono">PROTOCOL v1.0</span></div>
    </aside>
    <main>
      <header className="topbar"><div className="breadcrumb">FrameSignal Lab <ChevronRight size={14} /><span>Content measurement</span></div><span className="protocol-tag"><ShieldCheck size={14} /> Fixed-horizon analysis</span></header>
      <div className="page-body">
        <div className="page-heading"><div><div className="eyebrow">CONTENT MEASUREMENT / PROXY VALIDATION</div><h1>{tab === 'overview' ? 'A lift is not always a win.' : tab === 'proxy' ? 'Prediction is not surrogacy.' : tab === 'diagnostics' ? 'Challenge the signal.' : 'Define the decision first.'}</h1><p>{tab === 'overview' ? 'Randomized presentation policy · household-level intention-to-treat' : tab === 'proxy' ? 'Frozen candidates · independent experiment populations · held-out evidence' : tab === 'diagnostics' ? 'Sensitivity, sampling variation, and inference with known truth' : 'Preregistered synthetic protocol · not a definition of Netflix retention'}</p></div><span className="project-number mono">FS / 001</span></div>

        {(tab === 'overview' || tab === 'diagnostics') && <form className="experiment-controls" onSubmit={event => { event.preventDefault(); void run(); }}>
          <div className="scenario-control"><label>Simulation scenario</label><div className="segmented">{Object.entries(scenarioLabels).map(([value, label]) => <button type="button" key={value} aria-pressed={scenario === value} onClick={() => { setScenario(value); void run(value); }} className={scenario === value ? 'selected' : ''}><i style={{ background: colors[value] }} />{label}</button>)}</div></div>
          <label className="numeric-field">Households<input aria-label="Households" type="number" min="100" max="20000" step="100" value={n} onChange={event => setN(event.target.value)} /></label>
          <label className="numeric-field seed-field">Seed<input aria-label="Seed" type="number" min="0" max="2147483647" value={seed} onChange={event => setSeed(event.target.value)} /></label>
          <button className="button primary" type="submit" disabled={loading}>{loading ? <LoaderCircle size={16} className="spin" /> : <Play size={15} />} {loading ? 'Running' : 'Run experiment'}</button>
        </form>}
        {error && <div className="error-banner" role="alert">{error}<button className="icon-button" onClick={() => void run()} title="Retry analysis" aria-label="Retry analysis"><RefreshCw size={17} /></button></div>}
        {stale && !loading && <div className="warning-banner">Inputs changed. Displayed results remain from {scenarioLabels[data.scenario]}, n={data.n}, seed={data.seed}.</div>}

        {tab === 'overview' && <>
          {!data && !error && <div className="loading-state" role="status"><LoaderCircle className="spin" />Generating household evidence…</div>}
          {data && target && <div className={loading ? 'results pending' : 'results'} aria-busy={loading}>
            <section className="target-band">
              <div className="target-info"><span className="eyebrow"><i className="live-dot" />PRIMARY TARGET / DAYS 29-56</span><h2>Later household return</h2><p>{data.description}</p><button className="text-button" onClick={() => setMetric('returned_d29_56')}>View estimand <ArrowRight size={15} /></button></div>
              <div className={`target-number ${(target.effect ?? 0) < 0 ? 'harm' : ''}`}><strong>{signed((target.effect ?? 0) * 100, 1)}<span>pp</span></strong><span>policy − control</span><span className="mono">95% CI [{signed((target.lower ?? 0) * 100, 1)}, {signed((target.upper ?? 0) * 100, 1)}] pp</span></div>
              <div className="target-verdict"><span className={`status ${(target.upper ?? 0) < 0 ? 'negative' : (target.lower ?? 0) > 0.02 ? 'positive' : 'neutral'}`}>{data.memo.recommendation}</span><p>{data.memo.reason}</p><span className="threshold">Practical threshold <strong>+2 pp</strong></span></div>
            </section>
            <div className="summary-grid">{(['qualified_starts', 'viewing_days', 'watch_minutes'] as Metric[]).map(key => <article className="summary-item" key={key}><div className="summary-top"><span>{labels[key]}</span><button className="icon-button" aria-label={`Define ${labels[key]}`} title={`Define ${labels[key]}`} onClick={() => setMetric(key)}><CircleHelp size={15} /></button></div><strong>{signed(data.metrics[key].effect)}</strong><span>{data.metrics[key].unit}</span><small>{data.metrics[key].role}</small></article>)}<article className="summary-item population-summary"><div className="summary-top"><span>ITT population</span><ShieldCheck size={15} /></div><strong>{data.n.toLocaleString()}</strong><span>assigned households</span><small>{data.non_viewers.toLocaleString()} non-viewers retained</small></article></div>
            {data.memo.starts_target_reversal && <div className="reversal-banner"><Activity size={19} /><div><strong>Starts and return point in opposite directions.</strong><span>A starts-only rule would favor this policy. The observed target effect points the other way; consult its interval before concluding harm.</span></div></div>}
            <section className="section"><div className="section-heading"><div><span className="eyebrow">01 / EXPERIMENTAL EVIDENCE</span><h2>Same households. Different signals.</h2></div><a className="button secondary" href={`/api/export?scenario=${data.scenario}&n=${data.n}&seed=${data.seed}`}><ArrowDownToLine size={15} /> Export run</a></div><EvidenceTable data={data} open={setMetric} /><p className="footnote">Household-randomized policy effects; not independent event tests. The two predefined candidate intervals use Bonferroni adjustment. Completion conditions on post-assignment starts.</p></section>
            <section className="memo-section"><div><span className="eyebrow">DECISION RECORD</span><h2>{data.memo.proxy_recommendation}</h2><p>Policy decisions remain tied to the longer-horizon outcome, not to a short-term lift alone.</p><button className="text-button" onClick={() => setTab('proxy')}>Inspect held-out experiments <ArrowRight size={16} /></button></div><div><h3>What not to conclude</h3><p>This synthetic policy effect is not evidence that a specific show caused retention, that artistic value has one score, or that Netflix uses these metrics for content decisions.</p><span className="mono">RUN {data.seed} · {scenarioLabels[data.scenario].toUpperCase()} · N={data.n}</span></div></section>
          </div>}
        </>}

        {tab === 'proxy' && <>
          <div className="validation-controls"><label>Candidate<select value={candidate} onChange={event => setCandidate(event.target.value as Candidate)}>{candidates.map(key => <option key={key} value={key}>{labels[key]}</option>)}</select></label><div className="segmented split-tabs" aria-label="Validation split">{['train', 'validation', 'heldout'].map(value => <button key={value} onClick={() => setSplit(value)} aria-pressed={split === value} className={split === value ? 'selected' : ''}>{value === 'heldout' ? 'Held-out' : value === 'train' ? 'Training' : 'Validation'}</button>)}</div>{suite && <button className="icon-button" title="Download validation evidence" aria-label="Download validation evidence" onClick={() => download(suite, 'framesignal-validation.json')}><ArrowDownToLine size={18} /></button>}</div>
          {suiteLoading && <div className="loading-state" role="status"><LoaderCircle className="spin" />Simulating 27 independent experiments…</div>}
          {suiteError && <div className="error-banner" role="alert">{suiteError}<button className="button secondary" onClick={() => void loadSuite()}>Retry</button></div>}
          {suite && agreement && <>
            <div className="split-strip"><span><Check size={15} />{suite.unique_households.toLocaleString()} unique households</span><span>9 experiments / split</span><span>Frozen metrics · no fitted weights</span></div>
            <section className="proxy-layout"><div><div className="section-heading"><div><span className="eyebrow">EXPERIMENT-LEVEL EFFECTS</span><h2>Does the short-term signal agree?</h2></div></div><div className="plot-axis-label">Later return effect (percentage points)</div><ExperimentPlot suite={suite} candidate={candidate} split={split} /><div className="plot-legend">{Object.entries(colors).map(([key, color]) => <span key={key}><i style={{ background: color }} />{scenarioLabels[key]}</span>)}</div><p className="footnote">Each point is one independent randomized experiment. Bars: 97.5% candidate and 95% target intervals. Zero-target experiments have unstable estimated signs.</p></div>
              <div className="agreement-panel"><span className="eyebrow">{split === 'heldout' ? 'HELD-OUT' : split.toUpperCase()} AGREEMENT</span><strong className="agreement-number">{pct(agreement.observed_agreement)}</strong><p>Observed sign agreement</p><dl className="compact-dl"><div><dt>Experiment bootstrap 95%</dt><dd>{pct(agreement.lower)} – {pct(agreement.upper)}</dd></div><div><dt>Effect-noise sensitivity 95%</dt><dd>{pct(agreement.noise_lower)} – {pct(agreement.noise_upper)}</dd></div><div><dt>Oracle non-null agreement</dt><dd>{pct(agreement.oracle_nonnull_agreement)}</dd></div><div><dt>Null-target / positive proxy</dt><dd>{agreement.oracle_null_proxy_positive} / {agreement.oracle_null_experiments}</dd></div><div><dt>Resolved target intervals</dt><dd>{agreement.resolved_target_experiments} / 9</dd></div></dl><p className="science-note">Neither sign agreement nor a regression of noisy effects establishes causal surrogacy. Acceptance requires an agreement lower bound above 80% and no demonstrated harmful reversal.</p></div>
            </section>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">HOUSEHOLD-LEVEL ASSOCIATION</span><h2>A different question: who returns?</h2></div></div><div className="table-scroll"><table><thead><tr><th>Experiment</th><th>Scenario</th><th>Candidate / return correlation</th><th>Target effect</th><th>Known truth</th></tr></thead><tbody>{suite.experiments.filter(row => row.split === split).map(row => <tr key={row.id}><td className="mono">{row.id}</td><td><span className="scenario-label"><i style={{ background: colors[row.scenario] }} />{scenarioLabels[row.scenario]}</span></td><td>{decimal(row.prediction[candidate], 3)}</td><td>{signed((row.effects.returned_d29_56.effect ?? 0) * 100)} pp</td><td>{signed(row.truth_return_effect * 100)} pp</td></tr>)}</tbody></table></div><p className="footnote">Correlation is descriptive and affected by latent household affinity. Positive individual association can coexist with treatment-effect disagreement. These experiments never share households across splits.</p></section>
          </>}
        </>}

        {tab === 'diagnostics' && <>
          {data && <section className="section"><div className="section-heading"><div><span className="eyebrow">SENSITIVITY ANALYSIS</span><h2>How fragile is the effect?</h2></div><select aria-label="Diagnostic metric" value={diagnosticMetric} onChange={event => setDiagnosticMetric(event.target.value as typeof diagnosticMetric)}>{['qualified_starts', 'viewing_days', 'watch_minutes'].map(key => <option key={key} value={key}>{labels[key as Metric]}</option>)}</select></div><div className="table-scroll"><table><thead><tr><th>Analysis variant</th><th>Effect / household</th><th>95% interval</th><th>Interpretation</th></tr></thead><tbody>{data.diagnostics.rows.map(row => <tr key={row.label}><td>{row.label}</td><td className="mono">{signed(row.effects[diagnosticMetric].effect)}</td><td className="mono">[{signed(row.effects[diagnosticMetric].lower)}, {signed(row.effects[diagnosticMetric].upper)}]</td><td className="note-cell">{row.note}</td></tr>)}</tbody></table></div><p className="footnote">Exploratory diagnostics, not additional confirmatory tests. Runtime and genre subsets retain zero-viewing households. Exposure normalization and winsorization change the estimand.</p>
            <div className="diagnostic-grid"><div><h3>Unequal exposure</h3><dl className="compact-dl">{Object.entries(data.diagnostics.exposure_by_arm).map(([arm, values]) => <div key={arm}><dt>{arm === '0' ? 'Control' : 'Policy'} impressions / HH</dt><dd>{decimal(values.mean)}<small>{values.zero_exposure} households with zero exposure</small></dd></div>)}</dl></div><div><h3>Household sampling variation</h3><dl className="compact-dl"><div><dt>{labels[diagnosticMetric]} bootstrap SD</dt><dd>{decimal(data.diagnostics.sampling_variation[diagnosticMetric].bootstrap_sd, 3)}</dd></div><div><dt>Resampling unit</dt><dd>Complete households</dd></div><div><dt>Bootstrap repetitions</dt><dd>{data.diagnostics.bootstrap_draws}</dd></div></dl></div></div>
          </section>}
          <section className="section"><div className="section-heading"><div><span className="eyebrow">KNOWN-TRUTH OPERATING CHARACTERISTICS</span><h2>Does the target inference behave?</h2></div>{operating && <button className="icon-button" title="Download operating characteristics" aria-label="Download operating characteristics" onClick={() => download(operating, 'framesignal-operating.json')}><ArrowDownToLine size={18} /></button>}</div>
            {operatingLoading && <div className="loading-state" role="status"><LoaderCircle className="spin" />Running 1,000 simulations per effect size…</div>}
            {operatingError && <div className="error-banner" role="alert">{operatingError}<button className="button secondary" onClick={() => void loadOperating()}>Retry</button></div>}
            {operating?.calibration_flags?.map(flag => <p className="science-note" key={flag}>{flag} Flags are exploratory and unadjusted across effect sizes.</p>)}
            {operating && <><div className="split-strip"><span>{operating.repetitions.toLocaleString()} repetitions / effect</span><span>N={operating.n.toLocaleString()} · seed {operating.seed}</span><span>Target inference only</span></div><div className="table-scroll"><table><thead><tr><th>True return effect</th><th>95% CI coverage</th><th>Null FPR / non-null power</th><th>Bias ± MC SE</th><th>Variance</th><th>Practical success</th></tr></thead><tbody>{operating.rows.map(row => <tr key={row.true_effect}><td>{signed(row.true_effect * 100)} pp</td><td>{pct(row.coverage.rate)}<small>[{pct(row.coverage.lower)}, {pct(row.coverage.upper)}]</small></td><td>{pct(row.rejection_rate.rate)}<small>[{pct(row.rejection_rate.lower)}, {pct(row.rejection_rate.upper)}]</small></td><td className="mono">{signed(row.bias * 100, 3)} ± {decimal(row.bias_mc_se * 100, 3)} pp</td><td className="mono">{decimal(row.sampling_variance, 5)}</td><td>{pct(row.practical_success.rate)}</td></tr>)}</tbody></table></div><p className="footnote">{operating.scope} Practical success means the lower target interval exceeds +2 pp. Runs are separate from the interactive scenario.</p></>}
          </section>
          {data && <section className="section"><div className="section-heading"><div><span className="eyebrow">SQL DATA INTEGRITY</span><h2>{data.sql.passed ? 'Population checks passed.' : 'Population checks failed.'}</h2></div><span className={`status ${data.sql.passed ? 'positive' : 'negative'}`}><Database size={14} />{Object.keys(data.sql.counts).length} checks</span></div><div className="sql-grid">{Object.entries(data.sql.counts).map(([key, count]) => <details key={key}><summary><span>{key.replaceAll('_', ' ')}</span><strong className="mono">{count.toLocaleString()}</strong></summary><pre>{data.sql.queries[key]}</pre></details>)}</div></section>}
        </>}

        {tab === 'design' && <>
          <section className="design-section"><span className="eyebrow">THE ESTIMAND</span><h2>The policy effect on the proportion of assigned households returning during days 29–56.</h2><p>Assignment happens at the household. The treatment is a fictional presentation or exposure policy, not the creative quality of a title. All registered households remain eligible, whether or not they view anything.</p><div className="design-facts"><div><span>Randomization</span><strong>Household · balanced 1:1</strong></div><div><span>Primary candidate</span><strong>Qualified starts</strong></div><div><span>Alternative</span><strong>Distinct viewing days</strong></div><div><span>Practical target threshold</span><strong>+2 percentage points</strong></div></div></section>
          <section className="section"><div className="section-heading"><div><span className="eyebrow">FROZEN ANALYSIS PLAN v1.0</span><h2>Before inspecting held-out results.</h2></div></div><div className="protocol-grid"><div><h3>Population & horizon</h3><p>2,000 households per experiment; 9 experiments per split. Short-term days 0–13, fully observed target days 29–56. Fixed-sample Welch intervals on household outcomes; no optional stopping.</p></div><div><h3>Multiplicity</h3><p>One primary target at two-sided α=0.05. Two candidate comparisons form a separate Bonferroni family at α=0.025 each. Other metrics and sensitivities are descriptive.</p></div><div><h3>Leakage prevention</h3><p>Independent household populations and random seeds in training, validation, and held-out experiments. No learned weights in this MVP. Any extension must learn on training, tune on validation, then freeze before held-out assessment.</p></div><div><h3>Success & failure</h3><p>Advance a policy only if its target interval clears +2 pp. Proxy acceptance requires held-out agreement lower bound above 80% and no harmful reversal. Otherwise reject or declare evidence insufficient; no null-as-equivalence shortcut.</p></div><div><h3>Assumptions</h3><p>Random assignment, consistency, no household interference, no attrition, complete exposure logging, and accurate event measurement. Synthetic affinity explains association but is never a proxy input.</p></div><div><h3>Scientific review</h3><p>Self-review only. No peer feedback is claimed. Small experiment counts, constructed scenario truth, and noise in estimated effects limit surrogate conclusions. Observational causal methods and learned composites are deferred.</p></div></div></section>
          <section className="section"><div className="section-heading"><div><span className="eyebrow">METRIC REGISTRY</span><h2>Definitions are part of the measurement.</h2></div></div><div className="registry-list">{Object.entries(labels).map(([key, label]) => <button key={key} onClick={() => setMetric(key as Metric)}><span>{label}</span><span>{key === 'completion' ? 'Descriptive · post-assignment selection' : key === 'returned_d29_56' ? 'Primary decision target' : definitions[key as Metric].window}</span><ArrowRight size={17} /></button>)}</div></section>
          <section className="references"><h3>Methodological starting points</h3><p>Netflix’s published proxy-metric and surrogate-index research motivates the distinction between predictive usefulness and experiment-level decision agreement. It is not proof of an internal content decision metric.</p><a href="https://research.netflix.com/research-area/experimentation-and-causal-inference" target="_blank" rel="noreferrer">Netflix Research: Experimentation & causal inference <ArrowRight size={14} /></a><p className="footnote">See repository research notes for bibliographic verification status and scope.</p></section>
        </>}
        <footer><span>FrameSignal Lab <i /> Synthetic measurement workbench</span><span>Policy effects, not title scores.</span></footer>
      </div>
    </main>
    {metric && <MetricDialog metric={metric} close={() => setMetric(null)} />}
  </div>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);