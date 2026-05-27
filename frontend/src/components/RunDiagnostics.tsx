import { RunStatePanel } from "./RunStatePanel";
import { WorkflowTimeline } from "./WorkflowTimeline";
import { WorkflowTrace } from "./WorkflowTrace";
import type { RunStateResponse, RunTimelineEvent, RunTraceEvent } from "../lib/types";

interface RunDiagnosticsProps {
  state: RunStateResponse | null;
  loading: boolean;
  error: string | null;
  timelineEvents: RunTimelineEvent[];
  traceEvents: RunTraceEvent[];
}

export function RunDiagnostics({
  state,
  loading,
  error,
  timelineEvents,
  traceEvents,
}: RunDiagnosticsProps) {
  return (
    <details className="diagnostics-panel">
      <summary>
        <span>
          <span className="detail-panel__eyebrow">Diagnostics</span>
          <strong>Run state, timeline, and trace</strong>
        </span>
        <span className="pill pill--workflow">Debug</span>
      </summary>
      <div className="diagnostics-panel__body">
        <RunStatePanel state={state} loading={loading} error={error} />
        <WorkflowTimeline events={timelineEvents} />
        <WorkflowTrace events={traceEvents} />
      </div>
    </details>
  );
}
