import { StrictMode, useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Activity, ArrowDownToLine, ArrowRight, Check, ChevronRight, CircleHelp, ClipboardCheck, Database, FlaskConical, LoaderCircle, Play, RefreshCw, ShieldCheck, SlidersHorizontal, X } from 'lucide-react';
import { CartesianGrid, ErrorBar, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import type { Analysis, Candidate, Effect, ExtensionReports, Metric, Operating, Suite } from './types';
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
  const [extensions, setExtensions] = useState<ExtensionReports | null>(null);
  const [loading, setLoading] = useState(false);
  const [suiteLoading, setSuiteLoading] = useState(false);
  const [operatingLoading, setOperatingLoading] = useState(false);
  const [extensionLoading, setExtensionLoading] = useState(false);
  const [error, setError] = useState('');
  const [suiteError, setSuiteError] = useState('');
  const [operatingError, setOperatingError] = useState('');
  const [extensionError, setExtensionError] = useState('');
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

  async function loadExtensions() {
    setExtensionLoading(true); setExtensionError('');
    try {
      const [observational, observationalReplication, observationalRobustness, observationalOverlapAudit, observationalCrossfitAudit, observationalThresholdStress, learned] = await Promise.all([
        get<ExtensionReports['observational']>('/api/observational'),
        get<ExtensionReports['observationalReplication']>('/api/observational-replication'),
        get<ExtensionReports['observationalRobustness']>('/api/observational-robustness'),
        get<ExtensionReports['observationalOverlapAudit']>('/api/observational-overlap-audit'),
        get<ExtensionReports['observationalCrossfitAudit']>('/api/observational-crossfit-audit'),
        get<ExtensionReports['observationalThresholdStress']>('/api/observational-threshold-stress'),
        get<ExtensionReports['learned']>('/api/learned-proxy'),
      ]);
      setExtensions({ observational, observationalReplication, observationalRobustness, observationalOverlapAudit, observationalCrossfitAudit, observationalThresholdStress, learned });
    } catch (exception) { setExtensionError((exception as Error).message); }
    finally { setExtensionLoading(false); }
  }

  useEffect(() => { void run(); return () => { abort.current?.abort(); }; }, []);
  useEffect(() => { if (tab === 'proxy' && !suite && !suiteLoading && !suiteError) void loadSuite(); }, [tab]);
  useEffect(() => { if (tab === 'diagnostics' && !operating && !operatingLoading && !operatingError) void loadOperating(); }, [tab]);
  useEffect(() => { if (tab === 'extensions' && !extensions && !extensionLoading && !extensionError) void loadExtensions(); }, [tab]);

  const stale = data && (data.scenario !== scenario || data.n !== Number(n) || data.seed !== Number(seed));
  const target = data?.metrics.returned_d29_56;
  const agreement = suite?.agreement[split][candidate];

  return <div className="app-shell">
    <aside className="sidebar">
      <a className="brand" href="/" aria-label="FrameSignal Lab home"><span className="brand-symbol"><Activity size={24} /></span><span>FrameSignal<span className="brand-lab">LAB</span></span></a>
      <div className="workspace-label">MEASUREMENT SCIENCE</div>
      <nav aria-label="Workbench views">{[
        ['overview', 'Experiment', FlaskConical], ['proxy', 'Proxy validation', Activity], ['diagnostics', 'Diagnostics', SlidersHorizontal], ['extensions', 'Extensions', Database], ['design', 'Research design', ClipboardCheck],
      ].map(([id, title, Icon]) => { const NavIcon = Icon as typeof Activity; return <button key={id as string} className={tab === id ? 'nav-item active' : 'nav-item'} onClick={() => setTab(id as string)} aria-current={tab === id ? 'page' : undefined}><NavIcon size={18} /><span>{title as string}</span>{tab === id && <ChevronRight size={15} />}</button>; })}<a className="nav-item" href={import.meta.env.VITE_METRICSTEWARD_URL ?? 'http://localhost:5174'}><Database size={18} /><span>MetricSteward</span><ChevronRight size={15} /></a></nav>
      <div className="sidebar-bottom"><div className="synthetic-mark"><Database size={15} />Synthetic data only</div><p>Fictional policies.<br />Real statistical questions.</p><span className="mono">PROTOCOL v1.0</span></div>
    </aside>
    <main>
      <header className="topbar"><div className="breadcrumb">FrameSignal Lab <ChevronRight size={14} /><span>Content measurement</span></div><span className="protocol-tag"><ShieldCheck size={14} /> Fixed-horizon analysis</span></header>
      <div className="page-body">
        <div className="page-heading"><div><div className="eyebrow">CONTENT MEASUREMENT / PROXY VALIDATION</div><h1>{tab === 'overview' ? 'A lift is not always a win.' : tab === 'proxy' ? 'Prediction is not surrogacy.' : tab === 'diagnostics' ? 'Challenge the signal.' : tab === 'extensions' ? 'Explore beyond randomization.' : 'Define the decision first.'}</h1><p>{tab === 'overview' ? 'Randomized presentation policy · household-level intention-to-treat' : tab === 'proxy' ? 'Frozen candidates · independent experiment populations · held-out evidence' : tab === 'diagnostics' ? 'Sensitivity, sampling variation, and inference with known truth' : tab === 'extensions' ? 'Exploratory synthetic extensions · separate from randomized ITT' : 'Preregistered synthetic protocol · not a definition of Netflix retention'}</p></div><span className="project-number mono">FS / 001</span></div>

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

        {tab === 'extensions' && <>
          {extensionLoading && <div className="loading-state" role="status"><LoaderCircle size={20} className="spin" />Loading predeclared extension reports…</div>}
          {extensionError && <div className="error-banner" role="alert">{extensionError}<button className="button secondary" onClick={() => void loadExtensions()}>Retry</button></div>}
          {extensions && <>
            <div className="split-strip"><span><ShieldCheck size={15} />Exploratory only</span><span>Observational selection is simulated</span><span>Learned weights frozen before held-out assessment</span><button className="icon-button" title="Download extension evidence" aria-label="Download extension evidence" onClick={() => download(extensions, 'framesignal-extensions.json')}><ArrowDownToLine size={17} /></button></div>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">OBSERVATIONAL SENSITIVITY / AIPW</span><h2>Measured adjustment does not erase hidden confounding.</h2></div><span className="status neutral">Not randomized ITT</span></div>
              <p className="footnote">Treatment assignment is selected from measured affinity/opportunity and a simulated latent-loyalty factor. AIPW adjusts only for the measured covariates. The hidden-confounding strength varies across runs; late return and oracle fields are not estimator inputs.</p>
              <div className="table-scroll"><table><thead><tr><th>Scenario</th><th>Hidden confounding</th><th>Known population effect</th><th>Naive difference</th><th>Measured-covariate AIPW</th><th>Bootstrap 95% interval</th><th>Overlap / ESS</th></tr></thead><tbody>{extensions.observational.results.rows.map(row => { const estimate = row.observational_estimate; const overlap = estimate.overlap; return <tr key={`${row.scenario}-${row.unmeasured_confounding_strength}`}><td>{scenarioLabels[row.scenario]}</td><td>{row.unmeasured_confounding_strength.toFixed(1)}</td><td className="mono">{signed(row.known_population_ate * 100)} pp</td><td className="mono">{signed(estimate.naive_unadjusted_difference_descriptive_only * 100)} pp</td><td className="mono">{signed(estimate.effect * 100)} pp</td><td className="mono">[{signed(estimate.lower * 100)}, {signed(estimate.upper * 100)}] pp</td><td><span className={`status ${overlap.overlap_check_passed ? 'positive' : 'negative'}`}>{overlap.overlap_check_passed ? 'Pass' : 'Flag'}</span><small>common {pct(overlap.fraction_inside_common_support)} · outside {pct(overlap.fraction_outside_overlap_range_0_05_0_95)} · ESS {decimal(overlap.ipw_effective_sample_size_by_arm['0'], 0)}/{decimal(overlap.ipw_effective_sample_size_by_arm['1'], 0)}</small></td></tr>; })}</tbody></table></div>
              <div className="science-note">{extensions.observational.results.warning} The AIPW interval resamples complete households; it does not account for every nuisance-model uncertainty or remove unmeasured confounding.</div>
              <div className="table-scroll"><table><thead><tr><th>Identification assumption</th></tr></thead><tbody>{extensions.observational.results.rows[0].observational_estimate.assumptions.map(item => <tr key={item}><td>{item}</td></tr>)}</tbody></table></div>
            </section>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">REPLICATED OBSERVATIONAL SENSITIVITY</span><h2>Repeated simulations clarify average bias.</h2></div><span className="status neutral">{extensions.observationalReplication.results.rows[0].replicates} replicates × {extensions.observationalReplication.results.number_of_cells} cells</span></div>
              <p className="footnote">{extensions.observationalReplication.results.warning} Each replicate uses an AIPW influence-function Wald interval, not the household-bootstrap interval above. Bias and coverage Monte Carlo intervals use Bonferroni familywise control across the fixed cells.</p>
              <div className="table-scroll"><table><thead><tr><th>Scenario</th><th>Hidden confounding</th><th>Mean AIPW bias</th><th>Bias RMSE</th><th>Wald interval coverage</th><th>Overlap pass rate</th><th>Mean ESS control / treatment</th></tr></thead><tbody>{extensions.observationalReplication.results.rows.map(row => { const biasInterval = row.aipw_bias_familywise_mc_interval; const coverageInterval = row.aipw_wald_coverage_familywise_mc_interval; const ess = row.mean_ipw_effective_sample_size_by_arm; return <tr key={`${row.scenario}-${row.unmeasured_confounding_strength}`}><td>{scenarioLabels[row.scenario]}</td><td>{row.unmeasured_confounding_strength.toFixed(1)}</td><td className="mono">{signed(row.mean_aipw_bias * 100)} pp<small>[{signed(biasInterval[0] * 100)}, {signed(biasInterval[1] * 100)}] MC</small></td><td className="mono">{decimal(row.aipw_bias_rmse * 100, 2)} pp</td><td>{pct(row.aipw_wald_interval_coverage)}<small>[{pct(coverageInterval[0])}, {pct(coverageInterval[1])}] MC</small></td><td>{pct(row.overlap_check_pass_rate)}</td><td className="mono">{decimal(ess['0'], 0)} / {decimal(ess['1'], 0)}</td></tr>; })}</tbody></table></div>
              <div className="science-note">{extensions.observationalReplication.results.familywise_mc_interval_scope} These intervals describe Monte Carlo uncertainty within this generator only; they do not establish real-world identification, validate the original bootstrap intervals, or approve any proxy.</div>
            </section>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">POSITIVITY / NUISANCE-MODEL STRESS</span><h2>Separate overlap stress from model misspecification.</h2></div><span className="status neutral">{extensions.observationalRobustness.results.rows[0].replicates} replicates × {extensions.observationalRobustness.results.number_of_cells} cells</span></div>
              <p className="footnote">{extensions.observationalRobustness.results.warning} Hidden confounding is fixed at zero. The four nuisance profiles test both models correct, propensity-only misspecification, outcome-only misspecification, and both misspecified.</p>
              <div className="table-scroll"><table><thead><tr><th>Overlap</th><th>Nuisance profile</th><th>Mean AIPW bias</th><th>Bias RMSE</th><th>Wald interval coverage</th><th>Overlap pass rate</th><th>Mean ESS control / treatment</th></tr></thead><tbody>{extensions.observationalRobustness.results.rows.map(row => { const biasInterval = row.aipw_bias_familywise_mc_interval; const coverageInterval = row.aipw_wald_coverage_familywise_mc_interval; const ess = row.mean_ipw_effective_sample_size_by_arm; return <tr key={`${row.overlap_profile}-${row.nuisance_profile}`}><td>{row.overlap_profile}</td><td>{row.nuisance_profile.replaceAll('_', ' ')}</td><td className="mono">{signed(row.mean_aipw_bias * 100)} pp<small>[{signed(biasInterval[0] * 100)}, {signed(biasInterval[1] * 100)}] MC</small></td><td className="mono">{decimal(row.aipw_bias_rmse * 100, 2)} pp</td><td>{pct(row.aipw_wald_interval_coverage)}<small>[{pct(coverageInterval[0])}, {pct(coverageInterval[1])}] MC</small></td><td>{pct(row.overlap_check_pass_rate)}</td><td className="mono">{decimal(ess['0'], 0)} / {decimal(ess['1'], 0)}</td></tr>; })}</tbody></table></div>
              <div className="science-note">{extensions.observationalRobustness.results.familywise_mc_interval_scope} Monte Carlo results apply only to this constructed design. Double robustness does not guarantee finite-sample performance; poor overlap can destabilize estimates even when both nuisance models are correctly specified.</div>
            </section>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">ORACLE OVERLAP AUDIT / DIAGNOSTIC ONLY</span><h2>Did the fitted propensity model flag the same support problems?</h2></div><span className="status neutral">Paired same-seed replay · {extensions.observationalOverlapAudit.results.number_of_cells} cells</span></div>
              <p className="footnote">{extensions.observationalOverlapAudit.results.warning} Oracle propensities are used only to audit overlap diagnostics and never enter AIPW. A false warning means fitted diagnostics fail while oracle diagnostics pass; a missed warning is the reverse.</p>
              <div className="table-scroll"><table><thead><tr><th>Overlap</th><th>Nuisance profile</th><th>Fitted pass</th><th>Oracle pass</th><th>False warning</th><th>Missed warning</th><th>Outside-range difference</th><th>Mean ESS fitted / oracle, control · treatment</th></tr></thead><tbody>{extensions.observationalOverlapAudit.results.rows.map(row => { const falseInterval = row.false_warning_familywise_mc_interval; const missedInterval = row.missed_warning_familywise_mc_interval; const outsideInterval = row.fitted_minus_oracle_outside_difference_familywise_mc_interval; const fittedEss = row.mean_estimated_ess_by_arm; const oracleEss = row.mean_oracle_ess_by_arm; return <tr key={`${row.overlap_profile}-${row.nuisance_profile}`}><td>{row.overlap_profile}</td><td>{row.nuisance_profile.replaceAll('_', ' ')}</td><td>{pct(row.estimated_overlap_pass_rate)}</td><td>{pct(row.oracle_overlap_pass_rate)}</td><td>{pct(row.false_warning_rate)}<small>[{pct(falseInterval[0])}, {pct(falseInterval[1])}] MC</small></td><td>{pct(row.missed_warning_rate)}<small>[{pct(missedInterval[0])}, {pct(missedInterval[1])}] MC</small></td><td className="mono">{signed(row.mean_fitted_minus_oracle_outside_difference * 100)} pp<small>[{signed(outsideInterval[0] * 100)}, {signed(outsideInterval[1] * 100)}] MC</small></td><td className="mono">{decimal(fittedEss['0'], 0)}/{decimal(oracleEss['0'], 0)} · {decimal(fittedEss['1'], 0)}/{decimal(oracleEss['1'], 0)}</td></tr>; })}</tbody></table></div>
              <div className="science-note">{extensions.observationalOverlapAudit.results.familywise_mc_interval_scope} This known-truth audit is possible only in simulation. Oracle probabilities are not available in real observational data.</div>
            </section>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">CROSS-FITTED OVERLAP AUDIT / DIAGNOSTIC ONLY</span><h2>Does out-of-fold fitting change overlap warnings?</h2></div><span className="status neutral">{extensions.observationalCrossfitAudit.results.cross_fitting_folds}-fold · {extensions.observationalCrossfitAudit.results.number_of_cells} cells</span></div>
              <p className="footnote">{extensions.observationalCrossfitAudit.results.warning} This compares overlap diagnostics only; it does not calculate cross-fitted AIPW treatment effects. Oracle propensities remain audit-only.</p>
              <div className="table-scroll"><table><thead><tr><th>Overlap</th><th>Nuisance profile</th><th>In-sample false warning</th><th>Cross-fit false warning</th><th>Cross-fit minus in-sample</th><th>In-sample missed warning</th><th>Cross-fit missed warning</th><th>Oracle pass</th></tr></thead><tbody>{extensions.observationalCrossfitAudit.results.rows.map(row => { const difference = row.crossfit_minus_in_sample_false_warning_familywise_mc_interval; return <tr key={`${row.overlap_profile}-${row.nuisance_profile}`}><td>{row.overlap_profile}</td><td>{row.nuisance_profile.replaceAll('_', ' ')}</td><td>{pct(row.in_sample_false_warning_rate)}</td><td>{pct(row.crossfit_false_warning_rate)}</td><td className="mono">{signed(row.crossfit_minus_in_sample_false_warning_rate * 100, 1)} pp<small>[{signed(difference[0] * 100, 1)}, {signed(difference[1] * 100, 1)}] MC</small></td><td>{pct(row.in_sample_missed_warning_rate)}</td><td>{pct(row.crossfit_missed_warning_rate)}</td><td>{pct(row.oracle_overlap_pass_rate)}</td></tr>; })}</tbody></table></div>
              <div className="science-note">{extensions.observationalCrossfitAudit.results.familywise_mc_interval_scope} Cross-fitting does not guarantee better overlap calibration, resolve positivity violations, or correct propensity-model misspecification.</div>
            </section>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">THRESHOLD OPERATING STUDY / EXPLORATORY</span><h2>How do prespecified support rules change flags?</h2></div><span className="status neutral">{extensions.observationalThresholdStress.results.number_of_threshold_rules} rules · fresh seed</span></div>
              <p className="footnote">{extensions.observationalThresholdStress.results.warning} Oracle pass rates are available only in this simulated audit; no threshold is selected or recommended.</p>
              <div className="table-scroll"><table><thead><tr><th>Rule</th><th>Propensity range</th><th>ESS floor</th><th>Oracle pass</th><th>In-sample pass</th><th>Cross-fit pass</th><th>In-sample false warning</th><th>Cross-fit false warning</th><th>Cross-fit minus in-sample</th></tr></thead><tbody>{extensions.observationalThresholdStress.results.threshold_summaries.map(row => { const inInterval = row.in_sample.false_warning_familywise_mc_interval; const crossInterval = row.crossfit.false_warning_familywise_mc_interval; const deltaInterval = row.crossfit_minus_in_sample_false_warning_familywise_mc_interval; return <tr key={row.threshold_rule}><td className="mono">{row.threshold_rule}</td><td className="mono">{row.propensity_range[0].toFixed(2)}–{row.propensity_range[1].toFixed(2)}</td><td>{row.minimum_effective_sample_size}</td><td>{pct(row.oracle.pass_rate)}</td><td>{pct(row.in_sample.pass_rate)}</td><td>{pct(row.crossfit.pass_rate)}</td><td>{pct(row.in_sample.false_warning_rate)}<small>[{pct(inInterval[0])}, {pct(inInterval[1])}] MC</small></td><td>{pct(row.crossfit.false_warning_rate)}<small>[{pct(crossInterval[0])}, {pct(crossInterval[1])}] MC</small></td><td className="mono">{signed(row.crossfit_minus_in_sample_false_warning_rate * 100, 1)} pp<small>[{signed(deltaInterval[0] * 100, 1)}, {signed(deltaInterval[1] * 100, 1)}] MC</small></td></tr>; })}</tbody></table></div>
              <div className="science-note">{extensions.observationalThresholdStress.results.familywise_mc_interval_scope} The study compares prespecified rules on this generator only; looser flags do not prove acceptable identification and stricter flags do not prove invalidity.</div>
            </section>
            <section className="section"><div className="section-heading"><div><span className="eyebrow">LEARNED HOUSEHOLD SCORE</span><h2>Prediction and treatment-effect agreement are different tests.</h2></div><span className="status neutral">Educational only · not approved</span></div>
              <p className="footnote">Weights fit on training households only; ridge strength selected on validation Brier score; the model is frozen before held-out experiments are generated. Features: qualified starts and viewing days. No assignment, affinity, oracle probability, or late outcome is a score feature.</p>
              <div className="table-scroll"><table><thead><tr><th>Split</th><th>Households</th><th>Brier score</th><th>Pooled prediction correlation</th><th>Control correlation</th><th>Policy correlation</th></tr></thead><tbody>{['train', 'validation', 'heldout'].map(splitName => { const prediction = extensions.learned.results.household_prediction[splitName]; return <tr key={splitName}><td>{splitName}</td><td>{prediction.n_households.toLocaleString()}</td><td className="mono">{decimal(prediction.brier_score, 4)}</td><td className="mono">{decimal(prediction.pooled_correlation, 3)}</td><td className="mono">{decimal(prediction.within_assignment_correlations['0'], 3)}</td><td className="mono">{decimal(prediction.within_assignment_correlations['1'], 3)}</td></tr>; })}</tbody></table></div>
              <div className="split-strip"><span>Selected ridge alpha {decimal(extensions.learned.results.model.selected_alpha, 2)}</span><span>Train-only standardized weights</span>{Object.entries(extensions.learned.results.model.standardized_coefficients).map(([feature, weight]) => <span key={feature}>{labels[feature as Candidate]}: {signed(weight, 3)}</span>)}</div>
              <div className="section-heading"><div><span className="eyebrow">FROZEN HELD-OUT EXPERIMENTS</span><h3>Score effects versus later-return effects</h3></div><strong className="mono">Agreement {pct(extensions.learned.results.heldout_agreement.observed_agreement)}</strong></div>
              <div className="table-scroll"><table><thead><tr><th>Experiment</th><th>Scenario</th><th>Learned-score effect</th><th>Return effect</th><th>Known truth</th></tr></thead><tbody>{extensions.learned.results.heldout_experiments.map(row => <tr key={row.id}><td className="mono">{row.id}</td><td>{scenarioLabels[row.scenario]}</td><td className="mono">{signed(row.effects.learned_proxy.effect)} [{signed(row.effects.learned_proxy.lower)}, {signed(row.effects.learned_proxy.upper)}]</td><td className="mono">{signed((row.effects.returned_d29_56.effect ?? 0) * 100)} pp</td><td className="mono">{signed(row.truth_return_effect * 100)} pp</td></tr>)}</tbody></table></div>
              <dl className="compact-dl"><div><dt>Experiment-bootstrap agreement interval</dt><dd>{pct(extensions.learned.results.heldout_agreement.lower)} – {pct(extensions.learned.results.heldout_agreement.upper)}</dd></div><div><dt>Effect-noise sensitivity interval</dt><dd>{pct(extensions.learned.results.heldout_agreement.noise_lower)} – {pct(extensions.learned.results.heldout_agreement.noise_upper)}</dd></div></dl>
              <div className="science-note">{extensions.learned.results.warning} {extensions.learned.results.interval_scope}</div>
            </section>
          </>}
        </>}

        {tab === 'design' && <>
          <section className="design-section"><span className="eyebrow">THE ESTIMAND</span><h2>The policy effect on the proportion of assigned households returning during days 29–56.</h2><p>Assignment happens at the household. The treatment is a fictional presentation or exposure policy, not the creative quality of a title. All registered households remain eligible, whether or not they view anything.</p><div className="design-facts"><div><span>Randomization</span><strong>Household · balanced 1:1</strong></div><div><span>Primary candidate</span><strong>Qualified starts</strong></div><div><span>Alternative</span><strong>Distinct viewing days</strong></div><div><span>Practical target threshold</span><strong>+2 percentage points</strong></div></div></section>
          <section className="section"><div className="section-heading"><div><span className="eyebrow">FROZEN ANALYSIS PLAN v1.0</span><h2>Before inspecting held-out results.</h2></div></div><div className="protocol-grid"><div><h3>Population & horizon</h3><p>2,000 households per experiment; 9 experiments per split. Short-term days 0–13, fully observed target days 29–56. Fixed-sample Welch intervals on household outcomes; no optional stopping.</p></div><div><h3>Multiplicity</h3><p>One primary target at two-sided α=0.05. Two candidate comparisons form a separate Bonferroni family at α=0.025 each. Other metrics and sensitivities are descriptive.</p></div><div><h3>Leakage prevention</h3><p>Baseline candidates are predefined. The optional learned score uses independent train/validation/held-out households and is fit, tuned, and frozen before held-out assessment.</p></div><div><h3>Success & failure</h3><p>Advance a policy only if its target interval clears +2 pp. Proxy acceptance requires held-out agreement lower bound above 80% and no harmful reversal. Otherwise reject or declare evidence insufficient; no null-as-equivalence shortcut.</p></div><div><h3>Assumptions</h3><p>Random assignment, consistency, no household interference, no attrition, complete exposure logging, and accurate event measurement. Synthetic affinity explains association but is never a proxy input.</p></div><div><h3>Scientific review</h3><p>Self-review only. No peer feedback is claimed. Optional observational and learned-score extensions remain exploratory; neither changes the randomized baseline or constitutes approval.</p></div></div></section>
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