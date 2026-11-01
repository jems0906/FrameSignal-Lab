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

export type ObservationalEstimate = {
  effect: number; lower: number; upper: number; bootstrap_se: number;
  naive_unadjusted_difference_descriptive_only: number;
  overlap: {
    propensity_quantiles: Record<string, number>;
    fraction_inside_common_support: number;
    fraction_outside_overlap_range_0_05_0_95: number;
    fraction_clipped_for_stability: number;
    ipw_effective_sample_size_by_arm: Record<string, number>;
    overlap_check_passed: boolean;
  };
  assumptions: string[]; warning: string;
};
export type ObservationalReport = {
  config: { study_id: string; seed: number; households_per_run: number; household_bootstrap_draws: number };
  results: {
    status: string; warning: string; measured_covariates: string[];
    rows: { scenario: string; unmeasured_confounding_strength: number; n: number; known_population_ate: number; assignment_rate: number; observational_estimate: ObservationalEstimate }[];
  };
};
export type ObservationalReplicationReport = {
  config: { study_id: string; seed: number; households_per_replicate: number; replicates_per_cell: number; confidence_level: number };
  results: {
    status: string; warning: string; familywise_mc_interval_scope: string; aipw_interval_method: string;
    number_of_cells: number; forbidden_estimator_inputs: string[];
    rows: {
      scenario: string; unmeasured_confounding_strength: number; n: number; replicates: number;
      known_population_ate: number; mean_aipw_bias: number; aipw_bias_familywise_mc_interval: [number, number];
      aipw_bias_rmse: number; aipw_wald_interval_coverage: number;
      aipw_wald_coverage_familywise_mc_interval: [number, number]; overlap_check_pass_rate: number;
      mean_ipw_effective_sample_size_by_arm: Record<string, number>;
    }[];
  };
};
export type ObservationalRobustnessReport = {
  config: { study_id: string; seed: number; scenario: string; households_per_replicate: number; replicates_per_cell: number; unmeasured_confounding: number };
  results: {
    status: string; warning: string; familywise_mc_interval_scope: string; aipw_interval_method: string;
    number_of_cells: number;
    rows: {
      overlap_profile: string; nuisance_profile: string; measured_selection_strength: number;
      propensity_nonlinearity: number; outcome_nonlinearity: number; replicates: number;
      mean_aipw_bias: number; aipw_bias_familywise_mc_interval: [number, number]; aipw_bias_rmse: number;
      aipw_wald_interval_coverage: number; aipw_wald_coverage_familywise_mc_interval: [number, number];
      overlap_check_pass_rate: number; mean_ipw_effective_sample_size_by_arm: Record<string, number>;
    }[];
  };
};
export type ObservationalOverlapAuditReport = {
  config: { study_id: string; source_config: string; confidence_level: number; familywise_cells: number };
  results: {
    status: string; warning: string; oracle_usage: string; same_seed_replay: boolean;
    number_of_cells: number; familywise_mc_interval_scope: string;
    rows: {
      overlap_profile: string; nuisance_profile: string; replicates: number;
      estimated_overlap_pass_rate: number; oracle_overlap_pass_rate: number;
      false_warning_rate: number; false_warning_familywise_mc_interval: [number, number];
      missed_warning_rate: number; missed_warning_familywise_mc_interval: [number, number];
      mean_fitted_minus_oracle_outside_difference: number;
      fitted_minus_oracle_outside_difference_familywise_mc_interval: [number, number];
      mean_estimated_ess_by_arm: Record<string, number>; mean_oracle_ess_by_arm: Record<string, number>;
    }[];
  };
};
export type LearnedProxyReport = {
  config: { study_id: string; seed: number; households_per_experiment: number; experiments_per_split: number };
  results: {
    status: string; warning: string; interval_scope: string; unique_households: number;
    weight_freeze_before_heldout: boolean; forbidden_features: string[];
    model: { intercept: number; selected_alpha: number; standardized_coefficients: Record<Candidate, number>; validation_brier_scores: { alpha: number; brier_score: number }[] };
    household_prediction: Record<string, { n_households: number; brier_score: number; pooled_correlation: number; within_assignment_correlations: Record<string, number> }>;
    heldout_experiments: { id: string; scenario: string; strength: number; truth_return_effect: number; effects: Record<Candidate | 'learned_proxy' | 'returned_d29_56', Effect> }[];
    heldout_agreement: Agreement;
  };
};
export type ExtensionReports = {
  observational: ObservationalReport;
  observationalReplication: ObservationalReplicationReport;
  observationalRobustness: ObservationalRobustnessReport;
  observationalOverlapAudit: ObservationalOverlapAuditReport;
  learned: LearnedProxyReport;
};