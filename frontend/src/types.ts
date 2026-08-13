export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFO";
export type Status = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Repository {
  id: string;
  github_owner: string;
  github_name: string;
  default_branch: string;
  created_at: string;
}

export interface Finding {
  id: string;
  rule_id: string;
  category: string;
  severity: Severity;
  confidence: number;
  file_path: string;
  start_line: number;
  end_line: number;
  title: string;
  explanation: string;
  suggested_fix: string;
  code_snippet: string | null;
  reviewed: boolean;
}

export interface Analysis {
  id: string;
  repository_id: string;
  branch: string;
  commit_sha: string | null;
  status: Status;
  quality_score: number | null;
  security_score: number | null;
  maintainability_score: number | null;
  architecture_score: number | null;
  technical_debt_minutes: number | null;
  language_breakdown: Record<string, number>;
  error: string | null;
  created_at: string;
}

export interface AnalysisDetail extends Analysis { findings: Finding[] }

