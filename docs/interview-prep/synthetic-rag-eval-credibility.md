# Synthetic RAG Eval 可信度

## 问题总览

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
- 这个项目现在真的有用到 RAG 吗？
- 为什么要费时费力做 offline eval？
- offline eval 到底在评估什么？
- `retrieval_hit` / `citation_coverage` / `citation_support` / `claim_support` 分别怎么评估？
- 如何用现有 `latest_report.md`、`latest_summary.json`、`bad_cases.jsonl` 手动 demo offline eval 的有效性？
- `plain_rag_baseline`、`rag_policy_baseline`、`graph_v1` 的对比说明了什么？

## 基本定位

这套数据不应该被描述成真实生产流量分布。更准确的说法是：它是一套 synthetic、scenario-driven、human-reviewable 的 RAG/workflow regression suite，用来覆盖检索命中、无证据、prompt injection、stale policy、action safety、review routing、claim citation support 等风险。

当前最重要的证据不是“分数很高”，而是数据分布可盘点、失败样本可解释、baseline 有对照、challenge case 没被隐藏。

## 当前证据

- 数据说明：`data/evals/DATASET_CARD.md`
- 数据分布报告：`docs/generated/eval-dataset-profile.md`
- Eval 数据集：`data/evals/supportflow_v1.jsonl`
- Eval-only tickets：`data/evals/supportflow_tickets.json`
- KB 语料：`data/kb/*.md`
- Profiling 脚本：`backend/scripts/profile_eval_dataset.py`
- Eval runner 和报告：`backend/scripts/run_offline_eval.py`, `data/evals/results/latest_report.md`

当前 profile 摘要：

- 15 份 KB 文档
- 10 条 UI demo tickets
- 36 条 eval-only tickets
- 39 条 eval examples
- 35 条 claim-support references
- 20 条 challenge examples，16 条 regression examples，3 条 demo examples
- 31 条 expected `waiting_review`，8 条 expected `done`
- 6 条 no-evidence cases，1 条 partial-evidence case，1 条 stale/draft evidence case

当前 offline eval 摘要：

- `plain_rag_baseline`：final pass `0.21`，130 个 bad cases
- `rag_policy_baseline`：final pass `0.21`，108 个 bad cases
- `graph_v1`：final pass `0.67`，21 个 bad cases
- `graph_v1` 当前 retrieval、citation coverage、citation support、category accuracy 都是 `1.00`
- 剩余 `graph_v1` bad cases 集中在两类：保守的 customer-facing send 审批导致 review routing/finalization 失败，以及 claim-level citation support 不足导致 drafting 失败

## Offline Eval 的必要性

当前项目确实有用到 RAG，但要精确表达：它是本地 Markdown KB + lexical retrieval + citation-grounded drafting 的轻量 RAG，不是 hosted vector database 或 embedding search。ticket 进入 LangGraph 后，`retrieve_knowledge` 会用 ticket subject 和 preview 检索 `data/kb/*.md`，`draft_reply` 会基于 `retrieved_chunks` 生成回答和 citations，后续 `risk_gate` 和 offline eval 会继续检查 evidence、citation、policy 和 routing。

offline eval 值得做，是因为它解决了手动 demo 无法解决的三个问题：

- 可复现：同一批 39 个 eval examples 可以重复运行，不依赖人工点 UI 或 LLM API 状态。
- 可比较：同一批数据同时跑 `plain_rag_baseline`、`rag_policy_baseline`、`graph_v1`，可以看出完整 workflow 相比弱 baseline 多解决了什么。
- 可定位：失败会落到 `drafting`、`review_routing`、`finalization`、`actions`、`policy` 等 stage，而不是只得到一个模糊的总分。

面试时可以这样说：

> 我做 offline eval 不是为了证明系统完美，而是为了把 RAG/workflow 的质量拆开看。比如检索是否命中、citation 是否存在、citation 是否来自 retrieved docs、claim 是否被 citation 支撑、policy/action/status 是否符合预期。这样系统失败时，我能知道是 retrieval 问题、citation 问题、policy 问题，还是 workflow routing 过于保守。

当前结果能支撑这个说法：`graph_v1 final_pass_rate=0.67`，不是满分；但 `retrieval_hit=1.00`、`citation_coverage=1.00`、`citation_support=1.00`、`policy_ids=1.00`、`action_types=1.00`。剩余 21 个 bad cases 集中在 5 个 `drafting` claim-support failures，以及 8 组 `review_routing` / `finalization` conservative routing failures。

## Eval 指标如何评估

`retrieval_hit` 评估检索有没有找对 KB。每个 eval example 的 `reference_outputs.should_retrieve_doc_ids` 写明期望检索到哪些 doc。如果期望非空，实际 `retrieved_doc_ids` 只要和期望有交集就算命中；如果期望为空，实际也必须为空，否则就是 `unexpected_retrieval`。

`citation_coverage` 评估应该有 citation 的回答是否真的带 citation。reference 里的 `must_include_citation=true` 表示这个 case 应该引用 KB；如果系统输出的 `citations` 为空，就会产生 `missing_citation`。

`citation_support` 评估 citation 是否来自本次 retrieved evidence。它会检查 `output.citations` 是否属于 `output.retrieved_doc_ids`，并用 `retrieved_evidence_by_doc_id` 做基础 support 检查。这个指标比“有没有 citation”更强，但仍然是 document-level support。

`claim_support` 评估关键 claim 是否被正确的 cited docs 支撑。eval metadata 里会写 `claims` 和对应 `supporting_doc_ids`。系统必须同时检索到这些支持文档，并在 citations 中引用它们。当前 `graph_v1 claim_support=0.85`，说明系统能做基础 grounding，但多 claim、多文档场景下仍有缺口。

`review_trigger_accuracy` 评估是否正确触发 human review。它直接比较 `reference_outputs.should_trigger_review` 和系统输出的 `review_required`。当前 `graph_v1 review_trigger_accuracy=0.79`，主要是因为 8 个低风险 challenge references 期望 `done`，但当前 graph 对 customer-facing send 仍保守进入 `waiting_review`。

`expected_status` 评估 workflow 最终状态是否符合 reference，例如 `done`、`waiting_review`、`manual_takeover`、`failed`。这能证明 eval 不只看回答文本，也检查 workflow control。

`expected_policy_ids`、`expected_action_types`、`expected_action_statuses` 评估 policy 和 action safety。比如 refund case 是否触发 billing policy，credit case 是否提出 `apply_credit`，action 是否保持 `proposed` 而不是绕过 review 直接执行。

## 如何手动 Demo Offline Eval 的有效性

第一步，打开 `docs/generated/eval-dataset-profile.md`，先展示数据集不是随便堆的。重点讲 39 个 eval examples、20 个 challenge examples、6 个 no-evidence cases、1 个 partial-evidence case、1 个 stale/draft evidence case，以及 31 个 expected `waiting_review` 和 8 个 expected `done`。这说明 synthetic 数据是按风险和证据条件组织的。

第二步，打开 `data/evals/results/latest_report.md`，展示三个 target 的 Summary：

    plain_rag_baseline | 39 | 0.21 | 130
    rag_policy_baseline | 39 | 0.21 | 108
    graph_v1 | 39 | 0.67 | 21

这里要强调：`plain_rag_baseline` 即使 retrieval/citation 还可以，也没有完整 workflow、policy、action 能力；`rag_policy_baseline` 增加了分类和基础 policy，但仍缺 action proposal 和完整 graph 状态；`graph_v1` bad cases 最少，说明 LangGraph workflow、policy gate、action layer、review routing 在起作用。

第三步，看 `latest_report.md` 的 Metric Rates。重点展示 `graph_v1` 的强项和缺口：

    Category 1.00
    Retrieval hit 1.00
    Citation coverage 1.00
    Citation support 1.00
    Claim support 0.85
    Review routing 0.79
    Policy IDs 1.00
    Action types 1.00
    Final pass 0.67

这时可以说：eval 的价值不是给一个总分，而是告诉我当前系统强在 retrieval、citation、policy/action，弱在 claim-level citation 和 conservative routing。

第四步，用 E-014 展示 claim-support failure。`data/evals/supportflow_v1.jsonl` 中 E-014 是 `outage_export_data_loss`，期望 claim “Outages and data loss reports should be escalated with impact details.” 被 `incident_escalation_runbook` 支撑。`bad_cases.jsonl` 显示 graph_v1 实际检索到了 `incident_escalation_runbook`，但 `cited_supporting_doc_ids` 是空，所以失败在 `drafting`，类型是 `claim_not_supported_by_citation`。这说明问题不是 retrieval，而是 draft citation 没有覆盖关键 claim。

第五步，用 E-005 展示 conservative review-routing failure。E-005 是低风险 export question，reference 期望 `should_trigger_review=false`、`expected_status=done`。但 `bad_cases.jsonl` 里 graph_v1 实际 `review_required=true`、`status=waiting_review`。这说明当前 workflow 对 customer-facing send 采取保守审批策略，eval 把这个产品/工程取舍暴露出来了。

第六步，用 baseline bad cases 说明为什么不是“只做 RAG 检索”就够了。`plain_rag_baseline` 有 130 个 bad cases，其中 `actions=62`、`review_routing=31`、`finalization=31`。这说明 plain RAG baseline 缺少 action proposal、human review routing 和 workflow state control。`graph_v1` 的价值是 RAG + LangGraph workflow + policy/action safety 的组合。

一段可以直接讲的 demo 话术：

> 我会先打开 dataset profile，证明 eval 数据按 scenario、evidence condition、risk level 和 expected status 做了盘点。然后打开 latest report，对比三个 target：plain RAG baseline、带基础 policy 的 baseline、完整 graph_v1。当前 graph_v1 的 retrieval hit、citation coverage、citation support、policy IDs、action types 都是 1.00，但 final pass 是 0.67。这个非满分是有用的，因为 bad cases 集中暴露了两类问题：claim-level citation support 不足，以及低风险 case 被保守路由到 human review。比如 E-014 检索到了 incident escalation 文档，但 citation 没有支撑对应 claim；E-005 是低风险 export question，reference 期望 done，但当前 graph 仍 waiting_review。这个 eval 的价值就是把失败定位到 drafting、review_routing、finalization，而不是只给一个总分。

## 面试质疑与回答

### 这个项目现在真的有用到 RAG 吗？

回答：有，但要准确表达。当前项目使用的是本地 Markdown KB + lexical retrieval + citation-grounded drafting 的轻量 RAG。它不是 hosted vector database，也不是 embedding search。RAG 体现在 workflow 里：ticket 先分类，然后 `retrieve_knowledge` 检索 KB，`draft_reply` 使用 retrieved chunks 生成带 citation 的 draft，policy gate 和 eval 再检查 evidence/citation 是否足够。

可以指向的证据：`backend/app/graph/nodes/retrieve_knowledge.py`、`backend/app/graph/nodes/draft_reply.py`、`backend/app/services/retrieval.py`、`data/kb/*.md`。

### 为什么要费时费力做 offline eval？

回答：因为只靠 UI demo 很容易变成 scripted demo。offline eval 能把质量变成可复现、可比较、可定位的证据。它可以证明系统不是只在三条 happy path 上跑通，也可以解释 RAG、policy、action、workflow routing 各自在哪些地方有效或失败。

可以指向的证据：`data/evals/results/latest_summary.json` 对比了三个 target；`latest_report.md` 按 target 和 failure stage 汇总 bad cases。

### `plain_rag_baseline`、`rag_policy_baseline`、`graph_v1` 的对比说明了什么？

回答：`plain_rag_baseline` 展示只有基础 retrieval/draft 时会缺什么；`rag_policy_baseline` 展示加上分类和基础 policy 后仍缺 action proposal 和完整 workflow state；`graph_v1` 展示 LangGraph workflow、policy gate、action layer、review routing 带来的增量价值。这个对比能说明项目不是只做了 RAG 检索，而是在做 RAG + workflow orchestration + safety 的组合。

可以指向的证据：`latest_report.md` 中 `plain_rag_baseline` 有 130 个 bad cases，`rag_policy_baseline` 有 108 个，`graph_v1` 有 21 个；`graph_v1` 的 policy IDs 和 action types 都是 `1.00`。

### 这些数据是 synthetic 的，真实吗？

回答：这是刻意设计成 synthetic 的，所以我不会说它代表真实客服流量分布。我把它当成一套受控 regression suite，用来覆盖三条 happy-path demo tickets 很难展示的 workflow 风险。

可以指向的证据：`DATASET_CARD.md` 明确说明数据是 synthetic，不能代表 production distribution。`eval-dataset-profile.md` 展示了 category、scenario type、evidence condition、risk level、expected status、intended failure mode 等分布。

### 你是不是为了通过 eval 反向调规则？

回答：这个风险确实存在，所以这套 eval 不是只保留能拿满分的 regression set。数据里区分了 `demo`、`regression` 和 `challenge` examples。当前 `graph_v1` 不是 100%，剩余失败被报告出来，而不是被隐藏。

可以指向的证据：`latest_report.md` 显示 `graph_v1 final_pass_rate=0.67`，并把 bad cases 按 `drafting`、`review_routing`、`finalization` 分组。

### 生成数据是不是太干净、太规则化？

回答：现在数据里既有干净的 regression cases，也有 challenge cases。challenge cases 覆盖 unsupported requests、prompt injection、stale/draft policy、security incidents、ambiguous multi-intent retrieval，以及低风险 safe-finalization references。

可以指向的证据：`eval-dataset-profile.md` 统计了 `prompt_injection`、`stale_policy`、`ambiguous_multi_intent`、`unsupported_no_evidence`、`security_incident` 等 scenario types。

### citation 检查是不是太弱？

回答：只检查有没有 citation 肯定不够。现在 eval 把 citation coverage、citation support、unsupported-claim absence 拆开，并且有一个第一版 claim-level support：在 fixture metadata 里把重要 claim 映射到支持它的 KB doc IDs。

可以指向的证据：`backend/app/evals/scoring.py` 检查 `citation_support` 和 `claim_support`。`supportflow_v1.jsonl` 里包含带 `supporting_doc_ids` 的 `metadata.claims`。

### 为什么 `graph_v1` 现在不是 100%？

回答：因为扩展后的数据集包含 challenge references。这些失败是有价值的：8 条低风险 reference 期望 `done`，但当前 graph 因为 customer-facing send 需要审批而路由到 `waiting_review`；另外 5 条 claim-support cases 说明，只引用一个文档不一定能支持所有 expected claims。

可以指向的证据：`data/evals/results/latest_report.md` 里的 bad cases by stage。

### 低风险 `done` 期望是否和 action safety 矛盾？

回答：这是 eval 里刻意保留的张力。当前产品行为是保守的：所有 customer-facing send 都需要 review。challenge references 在问，如果未来希望低风险、有证据支撑的回复可以 auto-finalize，系统需要补什么能力。这样可以把限制说清楚，而不是假装 workflow 已经最优。

可以指向的证据：`DATASET_CARD.md` 的 interpretation notes，以及 `latest_report.md` 里的 `review_routing` / `finalization` bad cases。

### 为什么不用真实客服数据？

回答：真实 support tickets 很可能包含客户隐私数据。对于公开求职项目，synthetic fixtures 更安全。关键不是假装 synthetic 等于真实数据，而是透明标注、做数据 profiling，并保留以后替换成 anonymized real tickets 的路径。

可以指向的证据：`DATASET_CARD.md` 的 source 和 limitation sections。

### LLM 生成数据和 LLM 评估之间是否有泄漏？

回答：offline eval 默认是 deterministic 的，并且会禁用 LLM calls；只有显式传 `--enable-llm` 才会启用。当前 fixtures 是 hand-authored，并标记为 `generation_method=hand_authored`。

可以指向的证据：`backend/app/evals/runner.py` 在 offline eval 默认禁用 `SUPPORTFLOW_LLM_ENABLED`；`eval-dataset-profile.md` 展示 generation metadata。

## 谨慎措辞

避免说：

- "The synthetic dataset is realistic production traffic."
- "The eval proves production readiness."
- "RAG quality is solved."
- "The graph should be judged only by final pass rate."

更建议说：

- "This is a controlled regression suite for RAG/workflow failure modes."
- "The dataset is synthetic, labeled, profiled, and reviewable."
- "The eval is meant to reveal failures, not hide them."
- "The current graph is strong on retrieval and basic citation support, but still exposes conservative routing and claim-level citation gaps."
