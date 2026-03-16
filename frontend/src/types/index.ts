export type Platform = 'web' | 'api' | 'database' | 'mobile' | 'desktop';

export interface Requirement {
  id: string;
  title: string;
  description: string;
  platforms: Platform[];
  priority: string;
  risk: string;
  status: string;
}

export interface TestCase {
  id: string;
  requirement_id: string;
  title: string;
  objective: string;
  platform: Platform;
  priority: string;
  review_status: string;
  metadata?: Record<string, unknown>;
}

export interface Verdict {
  status: string;
  reason: string;
  confidence: number;
}

export interface StepExecution {
  step_number: number;
  action: string;
  expected_result: string;
  actual_result: string;
  verdict: Verdict;
  evidence: string[];
}

export interface TestRun {
  id: string;
  test_case_id: string;
  agent_type: Platform;
  environment: string;
  status: string;
  summary_reason: string;
  confidence_score: number;
  steps: StepExecution[];
}

export interface AISuggestion {
  ai_available: boolean;
  title: string;
  description: string;
  platforms: Platform[];
  priority: string;
  risk: string;
  business_rules: string[];
}

