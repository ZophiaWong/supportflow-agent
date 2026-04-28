import type { SupportAction } from "../lib/types";

interface SupportActionListProps {
  actions: SupportAction[];
  emptyMessage?: string;
}

function formatActionLabel(actionType: SupportAction["action_type"]): string {
  return actionType.replace(/_/g, " ");
}

export function SupportActionList({
  actions,
  emptyMessage = "No support actions proposed yet.",
}: SupportActionListProps) {
  if (actions.length === 0) {
    return <p>{emptyMessage}</p>;
  }

  return (
    <ul className="action-list">
      {actions.map((action) => (
        <li className="action-list__item" key={action.action_id}>
          <div className="action-list__row">
            <strong>{formatActionLabel(action.action_type)}</strong>
            <span className="pill pill--workflow">{action.status}</span>
          </div>
          <p>{action.reason}</p>
          <p className="draft-meta">
            {action.requires_review ? "Requires approval" : "No approval required"} | Key{" "}
            {action.idempotency_key}
          </p>
        </li>
      ))}
    </ul>
  );
}
