# Synthetic RAG Eval Credibility

## Question Overview

- 这些数据是 synthetic 的，真实吗？
- 你是不是为了通过 eval 反向调规则？
- 生成数据是不是太干净、太规则化？
- citation 是否只是表面引用？
- claim-level citation support 现在做到什么程度？
- 为什么不用真实客服数据？
- LLM 生成数据和 LLM 评估之间是否有泄漏？
- 为什么现在 `graph_v1` 不是 100%？
- 低风险 case 期望 `done`，但 graph 仍然 `waiting_review`，这是 bug 吗？
- 这套 eval 能证明 RAG 有用吗，还是只是证明规则写得准？

## Positioning

这套数据不应该被描述成真实生产流量分布。更准确的说法是：它是一套 synthetic、scenario-driven、human-reviewable 的 RAG/workflow regression suite，用来覆盖检索命中、无证据、prompt injection、stale policy、action safety、review routing、claim citation support 等风险。

当前最重要的证据不是“分数很高”，而是数据分布可盘点、失败样本可解释、baseline 有对照、challenge case 没被隐藏。

## Current Evidence

- Dataset card: `data/evals/DATASET_CARD.md`
- Generated profile: `docs/generated/eval-dataset-profile.md`
- Eval dataset: `data/evals/supportflow_v1.jsonl`
- Eval-only tickets: `data/evals/supportflow_tickets.json`
- KB corpus: `data/kb/*.md`
- Profiling script: `backend/scripts/profile_eval_dataset.py`
- Eval runner and report: `backend/scripts/run_offline_eval.py`, `data/evals/results/latest_report.md`

Current profile summary:

- 15 KB documents
- 10 UI demo tickets
- 36 eval-only tickets
- 39 eval examples
- 35 claim-support references
- 20 challenge examples, 16 regression examples, 3 demo examples
- 31 expected `waiting_review`, 8 expected `done`
- 6 no-evidence cases, 1 partial-evidence case, 1 stale/draft evidence case

Current offline eval summary:

- `plain_rag_baseline`: final pass `0.21`, 130 bad cases
- `rag_policy_baseline`: final pass `0.21`, 108 bad cases
- `graph_v1`: final pass `0.67`, 21 bad cases
- `graph_v1` currently has clean retrieval, citation coverage, citation support, and category accuracy at `1.00`
- Remaining `graph_v1` bad cases are concentrated in review routing/finalization for conservative approval-gated sends and drafting for claim-level citation support gaps

## Objections

### The data is synthetic. Is it realistic?

Answer: It is synthetic by design, so I would not claim it reflects real support traffic distribution. I use it as a controlled regression suite for workflow risks that are hard to demonstrate with three happy-path demo tickets.

Evidence to point to: `DATASET_CARD.md` says the data is synthetic and not production distribution. `eval-dataset-profile.md` shows distribution by category, scenario type, evidence condition, risk level, expected status, and intended failure mode.

### Did you tune the rules to pass your own eval?

Answer: That risk exists, so the eval is intentionally not just a perfect-score regression set. The dataset separates `demo`, `regression`, and `challenge` examples. The current `graph_v1` score is not 100%, and the remaining failures are reported rather than hidden.

Evidence to point to: `latest_report.md` shows `graph_v1 final_pass_rate=0.67` and groups bad cases by `drafting`, `review_routing`, and `finalization`.

### Are the generated tickets too clean?

Answer: The dataset now includes clean regression cases and challenge cases. The challenge cases cover unsupported requests, prompt injection, stale/draft policy, security incidents, ambiguous multi-intent retrieval, and low-risk safe-finalization references.

Evidence to point to: `eval-dataset-profile.md` counts `prompt_injection`, `stale_policy`, `ambiguous_multi_intent`, `unsupported_no_evidence`, and `security_incident` scenario types.

### Is citation checking too weak?

Answer: Plain citation presence is not enough. The current eval separates citation coverage, citation support, unsupported-claim absence, and an explicit first version of claim-level support using fixture metadata that maps important claims to KB doc IDs.

Evidence to point to: `backend/app/evals/scoring.py` checks `citation_support` and `claim_support`. `supportflow_v1.jsonl` includes `metadata.claims` with `supporting_doc_ids`.

### Why is `graph_v1` not 100% anymore?

Answer: Because the expanded dataset now includes challenge references. The failures are useful: eight low-risk references expect `done`, while the current graph routes them to `waiting_review` because customer-facing sends are approval-gated; five claim-support cases show that citing one document does not always support every expected claim.

Evidence to point to: `data/evals/results/latest_report.md` bad cases by stage.

### Is the low-risk `done` expectation contradicting action safety?

Answer: It is a deliberate tension in the eval. The current product behavior is conservative: every customer-facing send requires review. The challenge references ask what the system would need to support if low-risk evidence-backed replies should auto-finalize. That makes the limitation explicit instead of pretending the workflow is optimal.

Evidence to point to: `DATASET_CARD.md` interpretation notes and `latest_report.md` `review_routing` / `finalization` bad cases.

### Why not use real data?

Answer: Real support tickets can contain customer private data. For a public portfolio project, synthetic fixtures are safer. The important thing is transparent labeling, data profiling, and a path to replace fixtures with anonymized real tickets later.

Evidence to point to: `DATASET_CARD.md` source and limitation sections.

### Is there LLM leakage in the eval?

Answer: The offline eval is deterministic by default and disables LLM calls unless `--enable-llm` is passed. The current fixtures are hand-authored and marked `generation_method=hand_authored`.

Evidence to point to: `backend/app/evals/runner.py` disables `SUPPORTFLOW_LLM_ENABLED` by default during offline eval; `eval-dataset-profile.md` shows the generation metadata.

## Careful Wording

Avoid saying:

- "The synthetic dataset is realistic production traffic."
- "The eval proves production readiness."
- "RAG quality is solved."
- "The graph should be judged only by final pass rate."

Prefer saying:

- "This is a controlled regression suite for RAG/workflow failure modes."
- "The dataset is synthetic, labeled, profiled, and reviewable."
- "The eval is meant to reveal failures, not hide them."
- "The current graph is strong on retrieval and basic citation support, but still exposes conservative routing and claim-level citation gaps."
