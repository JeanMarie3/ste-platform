export type Platform = 'web' | 'api' | 'database' | 'mobile' | 'desktop';

export interface Requirement {
  id: string;
  project_code: string;
  title: string;
  description: string;
  platforms: Platform[];
  priority: string;
  risk: string;
  status: string;
  created_at: string;
  updated_at: string;
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
  created_at: string;
  updated_at: string;
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
  started_at: string;
  finished_at: string | null;
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

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'standard';
  created_at: string;
  updated_at: string;
}

export interface AuthMessage {
  message: string;
}

