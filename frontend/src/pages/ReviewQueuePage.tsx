import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { fetchPendingReviews, resumeRun } from "../lib/api";
import type { PendingReviewItem, ReviewDecision, RunTicketResponse } from "../lib/types";

type EditDrafts = Record<string, string>;
type ReviewerNotes = Record<string, string>;
type Decisions = Record<string, ReviewDecision>;
type ReviewResults = Record<string, RunTicketResponse>;

export function ReviewQueuePage() {
  const [pendingReviews, setPendingReviews] = useState<PendingReviewItem[]>([]);
  const [decisions, setDecisions] = useState<Decisions>({});
  const [editDrafts, setEditDrafts] = useState<EditDrafts>({});
  const [reviewerNotes, setReviewerNotes] = useState<ReviewerNotes>({});
  const [submittingThreadId, setSubmittingThreadId] = useState<string | null>(null);
  const [results, setResults] = useState<ReviewResults>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadPendingReviews() {
      try {
        const items = await fetchPendingReviews();
        if (!cancelled) {
          setPendingReviews(items);
          setDecisions(
            Object.fromEntries(items.map((item) => [item.thread_id, "approve" satisfies ReviewDecision])),
          );
          setEditDrafts(Object.fromEntries(items.map((item) => [item.thread_id, item.draft.answer])));
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

    void loadPendingReviews();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(threadId: string) {
    const decision = decisions[threadId] ?? "approve";
    setSubmittingThreadId(threadId);
    setError(null);

    try {
      const result = await resumeRun(threadId, {
        decision,
        reviewer_note: reviewerNotes[threadId] ?? null,
        edited_answer: decision === "edit" ? editDrafts[threadId] ?? "" : null,
      });

      setResults((current) => ({ ...current, [threadId]: result }));
      setPendingReviews((current) => current.filter((item) => item.thread_id !== threadId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown resume error");
    } finally {
      setSubmittingThreadId(null);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="hero__kicker">Day 3 human review</p>
        <h1>Review Queue</h1>
        <p className="hero__lede">
          Review risky tickets, inspect the draft and supporting knowledge, and decide whether to
          approve, edit, or reject the response.
        </p>
        <div className="hero__nav">
          <Link className="secondary-link" to="/tickets">
            Back to inbox
          </Link>
        </div>
      </section>

      {loading ? <p className="status-panel">Loading pending reviews...</p> : null}
      {!loading && error ? <p className="status-panel status-panel--error">{error}</p> : null}
      {!loading && !error && pendingReviews.length === 0 && Object.keys(results).length === 0 ? (
        <p className="status-panel">No pending reviews right now.</p>
      ) : null}

      <section className="review-grid">
        {pendingReviews.map((item) => {
          const decision = decisions[item.thread_id] ?? "approve";
          const isSubmitting = submittingThreadId === item.thread_id;

          return (
            <article key={item.thread_id} className="result-panel">
              <div className="result-panel__header">
                <div>
                  <p className="detail-panel__eyebrow">Ticket {item.ticket_id}</p>
                  <h2>{item.classification.category} review</h2>
                </div>
                <span className="pill pill--workflow">{item.classification.priority}</span>
              </div>

              <div className="result-section">
                <h3>Risk flags</h3>
                <div className="result-tags">
                  {item.risk_flags.map((flag) => (
                    <span key={flag} className="pill pill--workflow">
                      {flag.replace(/_/g, " ")}
                    </span>
                  ))}
                </div>
              </div>

              <div className="result-section">
                <h3>Draft reply</h3>
                <p className="draft-reply">{item.draft.answer}</p>
                <p className="draft-meta">
                  Confidence {item.draft.confidence.toFixed(2)} | Citations:{" "}
                  {item.draft.citations.length > 0 ? item.draft.citations.join(", ") : "None"}
                </p>
              </div>

              <div className="result-section">
                <h3>Knowledge evidence</h3>
                <ul className="result-list">
                  {item.retrieved_chunks.map((hit) => (
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

              <div className="result-section">
                <h3>Review action</h3>
                <label className="form-field">
                  <span>Decision</span>
                  <select
                    value={decision}
                    onChange={(event) => {
                      setDecisions((current) => ({
                        ...current,
                        [item.thread_id]: event.target.value as ReviewDecision,
                      }));
                    }}
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
                      value={editDrafts[item.thread_id] ?? item.draft.answer}
                      onChange={(event) => {
                        setEditDrafts((current) => ({
                          ...current,
                          [item.thread_id]: event.target.value,
                        }));
                      }}
                      rows={8}
                    />
                  </label>
                ) : null}

                <label className="form-field">
                  <span>Reviewer note</span>
                  <textarea
                    value={reviewerNotes[item.thread_id] ?? ""}
                    onChange={(event) => {
                      setReviewerNotes((current) => ({
                        ...current,
                        [item.thread_id]: event.target.value,
                      }));
                    }}
                    rows={3}
                  />
                </label>

                <button
                  className="primary-button"
                  type="button"
                  onClick={() => void handleSubmit(item.thread_id)}
                  disabled={isSubmitting}
                >
                  {isSubmitting ? "Submitting review..." : "Submit review"}
                </button>
              </div>
            </article>
          );
        })}

        {Object.entries(results).map(([threadId, result]) => (
          <article key={threadId} className="result-panel">
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
          </article>
        ))}
      </section>
    </main>
  );
}
