export function getShortRunId(threadId: string): string {
  return threadId.slice(-8);
}

export function formatRunLabel(ticketId: string, threadId: string): string {
  return `${ticketId} · Run ${getShortRunId(threadId)}`;
}
