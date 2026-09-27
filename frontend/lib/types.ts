// Shared types for the frontend, matching ARCHITECTURE.md §5 (API Contract).

export type AnalysisMode = "analysis" | "feedback";

export interface AnalyzeRequest {
  input: string;
  mode: AnalysisMode;
}

export interface AnalyzeResponse {
  success: boolean;
  analysisId: string;
  analysis: string;
  feedback: string;
  recommendations: string[];
  createdAt: string;
}

export interface ApiError {
  success: false;
  error: {
    code: string;
    message: string;
  };
}

// Client-side finding shown inline by the markup demo / feedback list,
// before a real analysisId exists from the backend.
export type FindingType = "flag" | "tip" | "good";

export interface Finding {
  type: FindingType;
  text: string;
}

export interface PerformancePoint {
  round: number;
  score: number;
}
