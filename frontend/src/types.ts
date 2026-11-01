export type Metric = 'qualified_starts' | 'viewing_days' | 'watch_minutes' | 'completion' | 'returned_d29_56';
export type Candidate = 'qualified_starts' | 'viewing_days';
export type Effect = {
  label: string; unit: string; role: string; causal: boolean;
  effect: number | null; lower: number | null; upper: number | null; se: number | null;
  control_mean: number | null; treatment_mean: number | null; p_value: number | null;
  n_control: number; n_treatment: number; alpha?: number; warning?: string;
  starters_control?: number; starters_treatment?: number;
};
export type Plan = {
  version: string; primary_candidate: string; primary_target: string; households_per_experiment: number;
  experiments_per_split: number; practical_target_effect: number; candidate_alpha: number;
  stopping_rule: string; learning: string;
};
export type Analysis = {
  scenario: string; description: string; n: number; seed: number; events: number; non_viewers: number; estimand: string;
  truth: { return_effect: number }; plan: Plan; metrics: Record<Metric, Effect>;
  prediction: { metrics: Record<Candidate, { correlation: number; lower: number; upper: number; within_arm: number[] }>; warning: string };
  diagnostics: {
    rows: { label: string; note: string; effects: Record<Candidate | 'watch_minutes', Effect> }[];
    caps: Record<string, number>; genre_mix: { genre: string; events: number; mean_runtime: number; watch_minutes: number }[];
    exposure_by_arm: Record<string, { mean: number; zero_exposure: number }>;
    sampling_variation: Record<Candidate | 'watch_minutes' | 'returned_d29_56', { bootstrap_sd: number; lower: number; upper: number }>;
    bootstrap_draws: number;
  };
  sql: { passed: boolean; failures: string[]; counts: Record<string, number>; queries: Record<string, string> };
  memo: { recommendation: string; reason: string; starts_target_reversal: boolean; proxy_recommendation: string; limitations: string[] };
};
export type Agreement = {
  observed_agreement: number; lower: number; upper: number; noise_lower: number; noise_upper: number;
  n_experiments: number; resolved_target_experiments: number; oracle_nonnull_agreement: number;
  oracle_null_proxy_positive: number; oracle_null_experiments: number; warning: string;
};
export type Experiment = {
  id: string; split: string; scenario: string; strength: number; seed: number; n: number; truth_return_effect: number;
  effects: Record<Exclude<Metric, 'completion'>, Effect>; prediction: Record<Candidate, number>;
};
export type Suite = {
  plan: Plan; experiments: Experiment[]; agreement: Record<string, Record<Candidate, Agreement>>;
  unique_households: number; leakage_check: boolean; decision: string; frozen_candidates: Candidate[];
};
export type Rate = { rate: number; lower: number; upper: number };
export type Operating = {
  n: number; seed: number; repetitions: number; scope: string; calibration_flags: string[];
  rows: { true_effect: number; coverage: Rate; rejection_rate: Rate; practical_success: Rate; bias: number; bias_mc_se: number; sampling_variance: number; mean_interval_width: number }[];
};