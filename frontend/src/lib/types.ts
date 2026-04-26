export type TicketStatus = "open" | "pending" | "resolved";
export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type WorkflowCategory = "billing" | "account" | "product" | "bug" | "other";
export type WorkflowPriority = "P0" | "P1" | "P2" | "P3";
export type WorkflowStatus = "done" | "failed" | "running" | "waiting_review" | "manual_takeover";
export type ReviewDecision = "approve" | "edit" | "reject";
export type RunTimelineEventType =
  | "run_started"
  | "classify_completed"
  | "retrieve_completed"
  | "draft_completed"
  | "risk_gate_completed"
  | "interrupt_created"
  | "review_submitted"
  | "run_resumed"
  | "run_completed"
  | "run_failed";

export interface Ticket {
  id: string;
  subject: string;
  customer_name: string;
  status: TicketStatus;
  priority: TicketPriority;
  created_at: string;
  preview?: string | null;
}

export interface TicketClassification {
  category: WorkflowCategory;
  priority: WorkflowPriority;
  reason: string;
}

export interface KBHit {
  doc_id: string;
  title: string;
  score: number;
  snippet: string;
}

export interface DraftReply {
  answer: string;
  citations: string[];
  confidence: number;
}

export interface RiskAssessment {
  review_required: boolean;
  risk_flags: string[];
  reason: string;
}

export interface PendingReviewItem {
  thread_id: string;
  ticket_id: string;
  classification: TicketClassification;
  draft: DraftReply;
  retrieved_chunks: KBHit[];
  risk_flags: string[];
  allowed_decisions: ReviewDecision[];
}

export interface FinalResponse {
  answer: string;
  citations: string[];
  disposition: "auto_finalized" | "approved" | "edited";
}

export interface SubmitReviewDecisionRequest {
  decision: ReviewDecision;
  reviewer_note?: string | null;
  edited_answer?: string | null;
}

export interface RunTicketResponse {
  thread_id: string;
  ticket_id: string;
  status: WorkflowStatus;
  classification: TicketClassification;
  retrieved_chunks: KBHit[];
  draft: DraftReply;
  risk_assessment?: RiskAssessment | null;
  pending_review?: PendingReviewItem | null;
  final_response?: FinalResponse | null;
}

export interface RunTimelineEvent {
  event_id: string;
  thread_id: string;
  ticket_id: string;
  event_type: RunTimelineEventType;
  node_name?: string | null;
  status: WorkflowStatus;
  message?: string | null;
  created_at: string;
  payload?: Record<string, unknown> | null;
}

export interface RunTimelineResponse {
  thread_id: string;
  events: RunTimelineEvent[];
}

export interface RunStateResponse {
  thread_id: string;
  ticket_id: string;
  status: WorkflowStatus;
  current_node?: string | null;
  classification?: TicketClassification | null;
  retrieved_chunks: KBHit[];
  draft?: DraftReply | null;
  risk_assessment?: RiskAssessment | null;
  review_decision?: SubmitReviewDecisionRequest | null;
  final_response?: FinalResponse | null;
  pending_review?: PendingReviewItem | null;
  error?: string | null;
}
