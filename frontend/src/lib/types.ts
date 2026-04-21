export type TicketStatus = "open" | "pending" | "resolved";
export type TicketPriority = "low" | "medium" | "high" | "urgent";

export interface Ticket {
  id: string;
  subject: string;
  customer_name: string;
  status: TicketStatus;
  priority: TicketPriority;
  created_at: string;
  preview?: string | null;
}
