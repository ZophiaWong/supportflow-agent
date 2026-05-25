---
name: supportflow-review
description: Review the SupportFlow-agent project from an interviewer/HR perspective using code evidence. Use this skill when auditing implemented workflow, LangGraph state, RAG, guardrails, human review, action execution, persistence, evals, traces, or interview readiness. Do not use for generic refactoring or feature implementation unless explicitly asked.
---

# SupportFlow Review Skill

## Purpose

Use this skill to review the current SupportFlow-agent project in a code-evidence-driven way.

The goal is not to produce generic documentation. The goal is to help the project owner regain control of the project by answering interview-style questions with direct references to the current implementation, identifying gaps, and turning those gaps into focused hardening tasks.

SupportFlow-agent is a production-oriented prototype for AI-assisted customer support ticket triage. It uses FastAPI, React, LangGraph, RAG, guardrails, human review, safe action execution, persistence, traces, and evals to demonstrate controlled AI workflow engineering.

## When to use

Use this skill when the user asks to:

- review the current SupportFlow implementation
- audit whether a feature is actually implemented
- answer interviewer or HR-style questions about the project
- identify production-like gaps
- create `docs/notes` review documents
- prepare architecture notes, interview notes, or hardening plans
- inspect LangGraph nodes, state schema, RAG, guardrails, review queue, action layer, persistence, trace, or eval logic

Do not use this skill when the task is only:

- implementing a new feature without review
- doing broad code cleanup
- writing generic README content
- creating marketing copy
- rewriting unrelated documentation

## Core principle

Always distinguish:

1. Implemented
2. Partially implemented
3. Designed but not implemented
4. Future work

Never claim a feature exists unless the code evidence supports it.

## Default behavior

Unless the user explicitly asks for code changes, operate in read-only audit mode.

Read the relevant files first. Then produce a structured review document.

Do not rewrite the project during the review. Do not invent architecture that is not present in the codebase. Do not turn gaps into implemented claims.

## Required output format

For every reviewed question, use this structure:

```md
# 问题

## 当前实现
- 相关文件：
- 相关函数 / class：
- 当前行为：

## 设计意图
- 为什么这样设计：

## 缺口
- 当前还不像 production-like 的地方：

## Hardening 建议
- 最小改动：
- 后续增强：

## 面试表达
- 30 秒回答：
- 深挖回答：
```

## Evidence rules

For each claim under “当前实现”, include concrete evidence:

- file path
- function name, class name, API route, React component, graph node, model, schema, or test
- short description of actual behavior

Good:

```md
- 相关文件：backend/app/graph/nodes/policy_check.py
- 相关函数 / class：policy_check_node(...)
- 当前行为：根据 risk_flags 和 citation 状态决定是否进入 human_review。
```

Bad:

```md
- 当前行为：系统有完善的策略检查机制。
```

If the evidence is weak, say so explicitly.

## Review workflow

Follow this process:

### Step 1: Clarify the review target

Identify the module or question being reviewed. Examples:

- Why does this project use LangGraph?
- How does human review work?
- How does RAG citation validation work?
- How are high-risk actions controlled?
- How does persistence work?
- How are traces and evals implemented?
- What makes this different from a chatbot?

### Step 2: Locate relevant files

Search the repository for relevant implementation files. Prefer exact code references over assumptions.

Likely areas include:

```text
backend/
  app/
    graph/
    nodes/
    models/
    schemas/
    services/
    api/
    db/
    evals/
    traces/

frontend/
  src/
    pages/
    components/
    api/
    types/

docs/
tests/
```

Adapt to the actual repository structure.

### Step 3: Summarize current implementation

Describe what the code actually does now.

Keep this section factual. Avoid aspirational phrasing.

### Step 4: Infer design intent

Explain why this design likely exists.

Use restrained language:

- “The design appears to...”
- “This likely exists to...”
- “Based on the current flow...”

Do not overstate intent if the code does not make it clear.

### Step 5: Identify gaps

Evaluate the gap between current implementation and a production-like AI workflow system.

Use these dimensions:

- workflow control
- state clarity
- RAG reliability
- citation grounding
- guardrail coverage
- human review semantics
- action safety
- persistence and checkpointing
- traceability
- eval coverage
- error handling
- interview explainability

### Step 6: Recommend hardening

Split recommendations into:

- 最小改动：small changes that improve project credibility quickly
- 后续增强：larger improvements that can be deferred

Do not recommend a rewrite unless the current implementation is structurally unusable.

### Step 7: Produce interview expression

Write two answers:

- 30 秒回答：concise, HR/interviewer-friendly
- 深挖回答：technical answer suitable for follow-up questions

## Standard review questions

Use these as reusable question prompts.

### Project positioning

1. 这个项目一句话是什么？
2. 它和普通客服 chatbot 有什么区别？
3. 项目最能体现 AI Agent 工程能力的点是什么？
4. 当前项目是 production-ready，production-like，还是 production-oriented prototype？

### Business workflow

5. 工单生命周期是什么？
6. 工单有哪些类型？
7. 哪些工单可以自动处理，哪些必须人工审核？
8. 什么是最终成功状态？
9. 什么情况下进入人工升级？

### LangGraph workflow

10. 为什么这里适合用 LangGraph？
11. Graph state 里有哪些核心字段？
12. 每个节点的职责是什么？
13. 条件路由规则是什么？
14. 哪些节点需要 checkpoint？
15. 人工审核 reject/edit/approve 后 graph 如何继续？

### RAG and citations

16. 知识库内容从哪里来？
17. chunking 或 KB item 组织方式是什么？
18. 检索结果如何进入 prompt？
19. 回复中的引用如何生成？
20. 如何判断引用是否支持回复？
21. 检索失败或低置信度时系统如何处理？

### Guardrails and risk control

22. 有哪些风险规则？
23. 哪些规则是 deterministic，哪些由 LLM 判断？
24. 缺少引用时怎么办？
25. 高风险退款、账号、安全、隐私请求怎么处理？
26. 如何避免 agent 直接执行高影响动作？

### Human review

27. 审核员看到什么信息？
28. 审核员可以 approve、edit、reject 吗？
29. 审核结果是否真正影响 graph 后续路由？
30. 审核记录如何持久化？
31. 人工拒绝案例是否进入后续 eval 或 regression？

### Action layer

32. 系统有哪些 proposed actions？
33. proposed_action、approved_action、executed_action 是否分离？
34. 哪些 action 有副作用？
35. 如何保证 action 不重复执行？
36. action 失败如何记录和恢复？

### Persistence and state

37. SQLite 里存了哪些表？
38. LangGraph checkpoint 和业务表是什么关系？
39. ticket_id、run_id、checkpoint_id 如何关联？
40. 状态恢复和页面展示分别依赖哪些数据？

### Trace and observability

41. 一次 ticket run 能否回放？
42. trace 记录哪些节点输入输出？
43. trace 面向开发者、审核员、面试官分别有什么价值？
44. 出错后如何定位失败节点？

### Evals and tests

45. 如何评估分类准确率？
46. 如何评估 RAG 命中？
47. 如何评估引用充分性？
48. 如何评估风险路由是否正确？
49. 如何定义端到端成功？
50. 当前失败最多的是哪类 case？
51. 哪些 eval 已实现，哪些只是设计？

### Architecture tradeoffs

52. 为什么不用纯 if-else workflow？
53. 为什么不用 Dify / Coze？
54. 为什么不是 fully autonomous agent？
55. 为什么选择 FastAPI + React + LangGraph？
56. 如果要接入真实客服系统，需要补哪些边界？

## Documentation target

When asked to create documentation, prefer this structure:

```text
docs/
  notes/
    00_project_positioning.md
    01_interview_questions.md
    02_current_implementation_audit.md
    03_gap_analysis.md
    04_hardening_plan.md

  architecture/
    workflow_overview.md
    langgraph_state_schema.md
    node_responsibilities.md
    persistence_model.md
    action_layer.md
    human_review_flow.md

  evals/
    eval_design.md
    ticket_fixture_design.md
    rag_eval.md
    routing_eval.md
    end_to_end_eval.md

  decisions/
    ADR-001-why-langgraph.md
    ADR-002-why-human-review.md
    ADR-003-why-sqlite-checkpoint.md
    ADR-004-why-not-autonomous-agent.md

  interview/
    project_pitch.md
    deep_dive_qna.md
    failure_cases.md
    resume_bullets.md
```

Use `docs/notes` for exploration and audit notes.

Use `docs/architecture` for stable implementation descriptions.

Use `docs/evals` for evaluation design and results.

Use `docs/decisions` for architecture tradeoffs.

Use `docs/interview` for resume and interview preparation.

## Hardening priority rubric

When identifying gaps, rank them in this order:

### P0: Project control

- one-sentence positioning
- ticket lifecycle
- graph state schema
- node responsibility table

### P1: Production-like evidence

- realistic ticket fixtures
- KB documents and policies
- review queue semantics
- action audit model

### P2: Evaluation

- classification eval
- retrieval eval
- citation eval
- review routing eval
- end-to-end eval

### P3: Observability

- trace timeline
- node input/output record
- run replay
- structured error records

### P4: Advanced hardening

- idempotent action execution
- failure recovery
- regression suite
- reviewer feedback loop
- deployment notes

## Output style

Be direct and evidence-focused.

Prefer tables when comparing current implementation, gap, and hardening direction.

Do not produce long abstract explanations unless asked.

Do not flatter the project.

Do not hide gaps.

If the implementation is demo-level, say so precisely and explain what evidence would make it production-like.

## Definition of done

A review is complete only if it answers:

1. What is currently implemented?
2. Where is it implemented?
3. What production-like concern does it address?
4. What is still missing?
5. What is the smallest useful hardening step?
6. How should the user explain this in an interview?
