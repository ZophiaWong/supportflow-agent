export type TicketStatus = "open" | "pending" | "resolved";
export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type WorkflowCategory = "billing" | "account" | "product" | "bug" | "other";
export type WorkflowPriority = "P0" | "P1" | "P2" | "P3";

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

export interface RunTicketResponse {
  thread_id: string;
  ticket_id: string;
  status: "done" | "failed" | "running";
  classification: TicketClassification;
  retrieved_chunks: KBHit[];
  draft: DraftReply;
}
