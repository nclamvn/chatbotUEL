export type AnswerStatus = "grounded" | "disputed" | "null" | "oos";
export type ResponseMode = "mock" | "api";

export interface Citation {
  claim_id: string;
  source: string;
  tier: "A" | "B" | "C";
  fetched_at: string;
  evidence_span: string;
  url: string;
}

export interface Answer {
  answer_markdown: string;
  status: AnswerStatus;
  citations: Citation[];
  followups: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "bot";
  text: string;
  answer?: Answer;
  pending?: boolean;
}
