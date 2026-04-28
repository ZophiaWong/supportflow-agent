import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { PolicyAssessmentList } from "../components/PolicyAssessmentList";
import { SupportActionList } from "../components/SupportActionList";
import { fetchPendingReviews, resumeRun } from "../lib/api";
import type { PendingReviewItem, ReviewDecision, RunTicketResponse } from "../lib/types";

export function ReviewDetailPage() {
  const { threadId } = useParams<{ threadId: string }>();
  const [pendingReview, setPendingReview] = useState<PendingReviewItem | null>(null);
  const [decision, setDecision] = useState<ReviewDecision>("approve");
  const [editedAnswer, setEditedAnswer] = useState("");
  const [reviewerNote, setReviewerNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<RunTicketResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPendingReview() {
      try {
        const items = await fetchPendingReviews();
        const match = items.find((item) => item.thread_id === threadId) ?? null;

        if (!cancelled) {
          setPendingReview(match);
          setDecision("approve");
          setEditedAnswer(match?.draft.answer ?? "");
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Unknown review queue error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadPendingReview();

    return () => {
      cancelled = true;
    };
  }, [threadId]);

  async function handleSubmit() {
    if (!threadId) {
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const nextResult = await resumeRun(threadId, {
        decision,
        reviewer_note: reviewerNote || null,
        edited_answer: decision === "edit" ? editedAnswer : null,
      });

      setResult(nextResult);
      setPendingReview(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown resume error");
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return <p className="status-panel">Loading pending review...</p>;
  }

  if (error && !pendingReview && !result) {
    return <p className="status-panel status-panel--error">{error}</p>;
  }

  if (!pendingReview && !result) {
    return (
      <section className="screen">
        <div className="empty-state">
          <h2>Review not found</h2>
          <p>This thread is not pending review anymore, or it is not available in this queue.</p>
          <Link className="secondary-link" to="/reviews">
            Back to review queue
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="screen">
      <div className="screen__header">
        <div>
          <p className="screen__eyebrow">Review detail</p>
          <h2>{pendingReview?.ticket_id ?? result?.ticket_id}</h2>
          <p>Inspect the AI draft and submit the reviewer decision.</p>
        </div>
        <Link className="secondary-link" to="/reviews">
          Back to review queue
        </Link>
      </div>

      {pendingReview ? (
        <div className="detail-layout detail-layout--review">
          <section className="result-panel">
            <div className="result-panel__header">
              <div>
                <p className="detail-panel__eyebrow">Ticket {pendingReview.ticket_id}</p>
                <h2>{pendingReview.classification.category} review</h2>
              </div>
              <span className="pill pill--workflow">{pendingReview.classification.priority}</span>
            </div>

            <div className="result-section">
              <h3>Risk flags</h3>
              {pendingReview.risk_flags.length > 0 ? (
                <div className="result-tags">
                  {pendingReview.risk_flags.map((flag) => (
                    <span key={flag} className="pill pill--workflow">
                      {flag.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              ) : (
                <p>No content-risk flags. Review is required for external action approval.</p>
              )}
            </div>

            <div className="result-section">
              <h3>Policy checks</h3>
              <PolicyAssessmentList assessment={pendingReview.policy_assessment} />
            </div>

            <div className="result-section">
              <h3>Proposed actions</h3>
              <SupportActionList actions={pendingReview.proposed_actions ?? []} />
            </div>

            <div className="result-section">
              <h3>Draft reply</h3>
              <p className="draft-reply">{pendingReview.draft.answer}</p>
              <p className="draft-meta">
                Confidence {pendingReview.draft.confidence.toFixed(2)} | Citations:{" "}
                {pendingReview.draft.citations.length > 0
                  ? pendingReview.draft.citations.join(", ")
                  : "None"}
              </p>
            </div>

            <div className="result-section">
              <h3>Knowledge evidence</h3>
              <ul className="result-list">
                {pendingReview.retrieved_chunks.map((hit) => (
                  <li key={hit.doc_id} className="result-list__item">
                    <div className="result-list__row">
                      <strong>{hit.title}</strong>
                      <span>Score {hit.score.toFixed(2)}</span>
                    </div>
                    <p>{hit.snippet}</p>
                  </li>
                ))}
              </ul>
            </div>
          </section>

          <section className="result-panel">
            <div className="result-panel__header">
              <div>
                <p className="detail-panel__eyebrow">Reviewer action</p>
                <h2>Decision</h2>
              </div>
              <span className="pill pill--workflow">{decision}</span>
            </div>

            {error ? (
              <p className="status-panel status-panel--error">{error}</p>
            ) : null}

            <label className="form-field">
              <span>Decision</span>
              <select
                value={decision}
                onChange={(event) => setDecision(event.target.value as ReviewDecision)}
              >
                <option value="approve">Approve</option>
                <option value="edit">Edit</option>
                <option value="reject">Reject</option>
              </select>
            </label>

            {decision === "edit" ? (
              <label className="form-field">
                <span>Edited answer</span>
                <textarea
                  value={editedAnswer}
                  onChange={(event) => setEditedAnswer(event.target.value)}
                  rows={8}
                />
              </label>
            ) : null}

            <label className="form-field">
              <span>Reviewer note</span>
              <textarea
                value={reviewerNote}
                onChange={(event) => setReviewerNote(event.target.value)}
                rows={3}
              />
            </label>

            <button
              className="primary-button"
              type="button"
              onClick={() => void handleSubmit()}
              disabled={submitting}
            >
              {submitting ? "Submitting review..." : "Submit review"}
            </button>
          </section>
        </div>
      ) : null}

      {result ? (
        <section className="result-panel">
          <div className="result-panel__header">
            <div>
              <p className="detail-panel__eyebrow">Completed review</p>
              <h2>{result.ticket_id}</h2>
            </div>
            <span className="pill pill--workflow">{result.status}</span>
          </div>

          {result.final_response ? (
            <div className="result-section">
              <h3>Final response</h3>
              <p className="draft-reply">{result.final_response.answer}</p>
              <p className="draft-meta">
                Disposition {result.final_response.disposition.replace(/_/g, " ")}
              </p>
            </div>
          ) : (
            <div className="result-section">
              <h3>Manual takeover</h3>
              <p>A human agent now owns this ticket because the AI draft was rejected.</p>
            </div>
          )}

          <div className="result-section">
            <h3>Policy checks</h3>
            <PolicyAssessmentList assessment={result.policy_assessment} />
          </div>

          <div className="result-section">
            <h3>Action ledger</h3>
            <SupportActionList actions={result.proposed_actions ?? []} />
          </div>
        </section>
      ) : null}
    </section>
  );
}
