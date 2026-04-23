# Day2 Graph Happy Path

This ExecPlan is a living document. Keep `Progress`, `Decision Log`, `Surprises & Discoveries`, and `Outcomes & Retrospective` updated as work advances.

## Purpose / Big Picture

Day2 的目标不是把项目做“更复杂”，而是让它**第一次真正像一个 LangGraph 项目**。

今天只证明一条最小同步 happy path：

**选择工单 -> `load_ticket_context` -> `classify_ticket` -> `retrieve_knowledge` -> `draft_reply` -> FastAPI 返回结构化结果 -> 前端详情页展示分类、证据和草稿**

这一天的重点是：

- 把 graph 的 `state / nodes / edges / compile / invoke` 跑通
- 把前后端联动从“静态壳子”推进到“工作流结果页”
- 把“模型效果问题”和“系统编排问题”分开
- 为 Day3 的 `risk_gate + human_review_interrupt` 打好状态和调用基础

## Why Today Matters

Day1 解决的是项目壳子、接口边界、repo 组织方式。  
Day2 解决的是：**这个项目到底是不是 LangGraph workflow 项目**。

如果 Day2 跑通，你就不再只是有一个：

- FastAPI 壳子
- React 页面
- mock 数据列表

你会有一个真正的 workflow 执行闭环：

- 结构化 state
- 明确 node 职责
- graph compile / invoke
- 结构化 API 输出
- 前端展示中间产物

## Scope

### In Scope

- 统一 demo 数据语言，保证中文工单能命中 KB
- 新建 Day2 active ExecPlan
- 增加 `ticket_repo` 和 `retrieval` 两个 service
- 定义 graph 共享状态与节点输出 schema
- 实现 4 个 LangGraph 节点：
  - `load_ticket_context`
  - `classify_ticket`
  - `retrieve_knowledge`
  - `draft_reply`
- 编译同步 graph
- 新增 `POST /api/v1/tickets/{ticket_id}/run`
- 前端详情区展示：
  - ticket detail
  - classification
  - retrieved chunks
  - draft reply
- 增加 1 个最小 smoke test

### Out of Scope

今天坚决不做：

- conditional routing
- `risk_gate`
- interrupt / resume
- review queue 联动
- SSE / streaming
- LangSmith tracing
- 数据库 / ORM / migration
- 向量库 / embedding / reranker
- LLM 实现（先用 deterministic stub）
- Docker
- 真实工单系统集成

## Success Criteria

今天结束前，必须满足以下 6 条：

1. demo KB 已统一成中文或双语
2. graph 的 4 个节点已写完并能成功 `invoke`
3. `POST /api/v1/tickets/{ticket_id}/run` 能返回结构化结果
4. 前端能选中 ticket 并显示 workflow 结果
5. 至少 1 个 smoke test 通过
6. 本文档的 `Progress / Decision Log` 已更新

## Guardrails

为了避免 Day2 失控，必须遵守下面这些限制：

- **先稳边界，再换实现**
  - `classify_ticket` 先规则分类
  - `draft_reply` 先模板草稿
  - 但 contract 必须已经定成结构化 schema
- **API 层不直接读 JSON**
  - ticket 读取放到 `ticket_repo.py`
- **node 不直接扫目录**
  - 检索逻辑放到 `retrieval.py`
- **graph state 存原始结构**
  - 不要只存一个大字符串 prompt
- **今天只跑同步 happy path**
  - 先验证 orchestration
- **今天可以接 checkpointer，但不做人审**
  - 为 Day3 留好基础，不提前引入额外变量

## Milestones

## Milestone 1: Data Alignment

### Goal

让中文工单能检索到有效 KB。

### Tasks

- 更新 `refund_policy.md`
- 新增 `account_unlock.md`
- 新增 `bug_export_issue.md`

### Acceptance

- 中文 ticket 与中文 KB 主题一致
- 至少每种主要类别对应 1 份 KB 文档

## Milestone 2: Service Boundary

### Goal

把数据访问和 graph orchestration 分开。

### Tasks

- 新建 `services/ticket_repo.py`
- 新建 `services/retrieval.py`

### Acceptance

- API 不直接读 JSON 文件
- node 不直接遍历 `data/kb/`

## Milestone 3: Graph Happy Path

### Goal

实现最小同步 graph。

### Tasks

- 更新 `graph/state.py`
- 新建 `schemas/graph.py`
- 实现 4 个 node
- 新建 `graph/builder.py`

### Acceptance

- `graph.invoke({"ticket_id": "T-1001"}, config=...)` 能返回完整结果
- 返回结果包含：
  - `classification`
  - `retrieved_chunks`
  - `draft`

## Milestone 4: Run API

### Goal

让后端可以按 ticket 触发 workflow。

### Tasks

- 新建 `api/v1/runs.py`
- 在 `main.py` 挂载 router

### Acceptance

- `POST /api/v1/tickets/{ticket_id}/run` 可用
- 非法 ticket 返回 404
- 正常调用返回结构化 payload

## Milestone 5: Frontend Workflow Result Panel

### Goal

前端可以从“列表页”进入“执行结果页”。

### Tasks

- 扩展 `types.ts`
- 扩展 `api.ts`
- 新建 `TicketDetail.tsx`
- 新建 `WorkflowResultPanel.tsx`
- 更新 `TicketsPage.tsx`

### Acceptance

- 点击左侧 ticket 后，右侧显示 detail
- 点击“Run workflow”按钮后，右侧显示分类、证据和草稿

## File Plan

按下面顺序推进，避免乱序：

1. `docs/exec-plans/active/2026-04-21-day2-graph-happy-path.md`
2. `data/kb/refund_policy.md`
3. `data/kb/account_unlock.md`
4. `data/kb/bug_export_issue.md`
5. `backend/app/services/ticket_repo.py`
6. `backend/app/services/retrieval.py`
7. `backend/app/schemas/graph.py`
8. `backend/app/graph/state.py`
9. `backend/app/graph/nodes/load_ticket_context.py`
10. `backend/app/graph/nodes/classify_ticket.py`
11. `backend/app/graph/nodes/retrieve_knowledge.py`
12. `backend/app/graph/nodes/draft_reply.py`
13. `backend/app/graph/builder.py`
14. `backend/app/api/v1/runs.py`
15. `backend/app/main.py`
16. `frontend/src/lib/types.ts`
17. `frontend/src/lib/api.ts`
18. `frontend/src/components/TicketDetail.tsx`
19. `frontend/src/components/WorkflowResultPanel.tsx`
20. `frontend/src/pages/TicketsPage.tsx`
21. `backend/tests/integration/test_graph_smoke.py`

## State Design

第一版 graph state 先保持轻量、清晰、可调试：

```python
from typing import Any, Literal, TypedDict
from app.schemas.graph import TicketClassification, KBHit, DraftReply

class TicketState(TypedDict, total=False):
    thread_id: str
    ticket_id: str
    ticket: dict[str, Any]

    classification: TicketClassification
    retrieval_query: str
    retrieved_chunks: list[KBHit]
    draft: DraftReply

    status: Literal["queued", "running", "done", "failed"]
    current_node: Literal[
        "load_ticket_context",
        "classify_ticket",
        "retrieve_knowledge",
        "draft_reply",
    ]
    error: str | None
```

### Design Notes

- `ticket`：原始业务数据，不要在 state 里只存 prompt 文本
- `classification / retrieved_chunks / draft`：中间结构化产物
- `current_node`：给 debug 和后续 timeline 使用
- `thread_id`：今天先立起来，Day3 的 interrupt / resume 直接复用
- `status`：只保留运行状态，不混入 review 状态

## Contract Design

```python
from typing import Literal
from pydantic import BaseModel

class TicketClassification(BaseModel):
    category: Literal["billing", "account", "product", "bug", "other"]
    priority: Literal["P0", "P1", "P2", "P3"]
    reason: str

class KBHit(BaseModel):
    doc_id: str
    title: str
    score: float
    snippet: str

class DraftReply(BaseModel):
    answer: str
    citations: list[str]
    confidence: float

class RunTicketResponse(BaseModel):
    thread_id: str
    ticket_id: str
    status: Literal["done", "failed", "running"]
    classification: TicketClassification
    retrieved_chunks: list[KBHit]
    draft: DraftReply
```

### Why This Contract Matters

- graph state 轻量，便于 orchestration
- node output contract 明确，便于替换实现
- FastAPI `response_model` 能做输出过滤和校验
- Day3 以后即使把规则分类换成 LLM，也不需要改 API 边界

## Node Responsibilities

## `load_ticket_context`

### Input

- `ticket_id`

### Output

- `ticket`
- `status = "running"`
- `current_node = "load_ticket_context"`

### Responsibility

- 从 `ticket_repo` 读取业务数据
- 初始化 graph 执行上下文

## `classify_ticket`

### Input

- `ticket`

### Output

- `classification`
- `current_node = "classify_ticket"`

### Responsibility

- 基于规则做最小分类
- 不做工具调用
- 不做复杂 reasoning

### Rule Sketch

- 出现“退款 / 发票 / 扣费 / 账单” -> `billing`
- 出现“登录 / 密码 / 锁定 / 账号” -> `account`
- 出现“报错 / 无响应 / bug / 导出失败” -> `bug`
- 否则 -> `other`

## `retrieve_knowledge`

### Input

- `classification`
- `ticket`

### Output

- `retrieval_query`
- `retrieved_chunks`
- `current_node = "retrieve_knowledge"`

### Responsibility

- 组合 query
- 调 `retrieval.py`
- 返回 top-k `KBHit`

## `draft_reply`

### Input

- `ticket`
- `classification`
- `retrieved_chunks`

### Output

- `draft`
- `status = "done"`
- `current_node = "draft_reply"`

### Responsibility

- 先生成模板版草稿
- 引用命中文档标题
- 没有 hit 时降低置信度，避免乱编

## Graph Shape

今天只做固定边，不做条件路由：

```mermaid
flowchart LR
    A([START]) --> B[load_ticket_context]
    B --> C[classify_ticket]
    C --> D[retrieve_knowledge]
    D --> E[draft_reply]
    E --> F([END])
```

## Graph Builder Skeleton

```python
from functools import lru_cache
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

from app.graph.state import TicketState
from app.graph.nodes.load_ticket_context import load_ticket_context
from app.graph.nodes.classify_ticket import classify_ticket
from app.graph.nodes.retrieve_knowledge import retrieve_knowledge
from app.graph.nodes.draft_reply import draft_reply

@lru_cache(maxsize=1)
def get_support_graph():
    builder = StateGraph(TicketState)

    builder.add_node("load_ticket_context", load_ticket_context)
    builder.add_node("classify_ticket", classify_ticket)
    builder.add_node("retrieve_knowledge", retrieve_knowledge)
    builder.add_node("draft_reply", draft_reply)

    builder.add_edge(START, "load_ticket_context")
    builder.add_edge("load_ticket_context", "classify_ticket")
    builder.add_edge("classify_ticket", "retrieve_knowledge")
    builder.add_edge("retrieve_knowledge", "draft_reply")
    builder.add_edge("draft_reply", END)

    return builder.compile(checkpointer=InMemorySaver())
```

## Service Design

## `ticket_repo.py`

### Responsibilities

- `list_tickets()`
- `get_ticket_by_id(ticket_id: str)`

### Rules

- 统一从 `demo_tickets.json` 读取
- API 层不自己打开文件
- graph node 只依赖 service，不依赖文件路径细节

## `retrieval.py`

### Responsibilities

- 读取本地 KB 文档
- 做最简 lexical scoring
- 返回 `KBHit[]`

### Rules

- 先做稳定版，不做 embedding
- 先保证“能解释、能调试、能替换”

## API Plan

## Endpoint

`POST /api/v1/tickets/{ticket_id}/run`

### Responsibility

- 接收 `ticket_id`
- 构造 `thread_id`
- 调 graph
- 返回结构化结果

### Response

- `thread_id`
- `ticket_id`
- `status`
- `classification`
- `retrieved_chunks`
- `draft`

### Error Handling

- ticket 不存在 -> 404
- 其他异常 -> 500 + 明确错误信息（今天可先最简处理）

## Minimal Route Skeleton

```python
from fastapi import APIRouter, HTTPException
from app.graph.builder import get_support_graph
from app.schemas.graph import RunTicketResponse

router = APIRouter()

@router.post("/tickets/{ticket_id}/run", response_model=RunTicketResponse)
def run_ticket(ticket_id: str):
    graph = get_support_graph()
    thread_id = f"ticket-{ticket_id}"
    config = {"configurable": {"thread_id": thread_id}}

    try:
        result = graph.invoke({"ticket_id": ticket_id}, config=config)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "thread_id": thread_id,
        "ticket_id": ticket_id,
        "status": result["status"],
        "classification": result["classification"],
        "retrieved_chunks": result["retrieved_chunks"],
        "draft": result["draft"],
    }
```

## Frontend Plan

今天前端只需要 3 个新增能力：

1. 点击左侧 ticket 后，右侧显示 detail
2. 点击“Run workflow”按钮
3. 展示 workflow 结果：
   - category / priority
   - top KB hits
   - draft answer / confidence

## Recommended Components

- `TicketDetail.tsx`
- `WorkflowResultPanel.tsx`

## UI Constraints

今天不做：

- timeline
- streaming
- state animation
- review queue
- fancy loading choreography

今天只做**结果可见**。

## Testing Plan

新增一个最小 smoke test：

```python
def test_graph_smoke():
    graph = get_support_graph()
    config = {"configurable": {"thread_id": "test-ticket-T-1001"}}

    result = graph.invoke({"ticket_id": "T-1001"}, config=config)

    assert result["classification"].category == "billing"
    assert len(result["retrieved_chunks"]) >= 1
    assert len(result["draft"].citations) >= 1
```

### Why This Test Exists

这个测试不是为了追求覆盖率，而是为了守住最短主链路：

- graph 可以跑
- 分类结果合理
- 检索不是空的
- 草稿带有引用

## Interview Framing

今天做完后，你至少要能讲清楚这 5 个问题。

### 1. 为什么 Day2 先用规则分类和模板草稿，不直接上 LLM？

**高质量回答思路：**

- Day2 目标是先验证 graph 的状态流和节点边界
- 我先把 contract 稳定下来，再替换节点内部实现
- 这样能把“编排问题”和“模型问题”分开调试

**差回答：**

- 模型还没接好
- 先随便写一下

### 2. 为什么 graph state 用 TypedDict，而节点输出和 API 输出用 Pydantic？

**高质量回答思路：**

- state 是共享运行态，TypedDict 轻量
- 节点输出和 API 输出是契约边界，需要更强约束
- 这是“共享状态”和“边界契约”的分层建模

**差回答：**

- 两个都差不多，我随便选的

### 3. 为什么 retrieval 要抽成 service，而不是直接写在 node 里？

**高质量回答思路：**

- node 负责 orchestration，不负责底层文件读取细节
- 抽象之后，后续从本地 markdown 切到向量库时 graph 基本不用改
- 这是为了可替换性和可测试性

**差回答：**

- 我喜欢分文件

### 4. 为什么今天还没做人审 interrupt，却已经接 checkpointer 和 thread_id？

**高质量回答思路：**

- LangGraph 的 persistence 本来就是 thread-scoped checkpoint 模型
- 我希望 Day3 加 interrupt 时，不需要再改 compile 和调用方式
- 这是提前把未来最确定会用到的基础设施立住

**差回答：**

- 先接着，万一以后用得到

### 5. 为什么不把 classify / retrieve / draft 合成一个节点？

**高质量回答思路：**

- 合成一个节点当然能跑，但调试性、可见性、后续 checkpoint 粒度会变差
- 我刻意拆开，是为了分别暴露中间产物和错误归因
- 后续做前端展示、节点级评测、坏例归因都会更容易

**差回答：**

- LangGraph 就应该多拆几个节点

## Risks and Mitigations

### 风险 1：中文 ticket 命中不到英文 KB

**缓解：**

- 今天先统一 KB 语言

### 风险 2：把 node 写成“半 service 半 orchestration”混合体

**缓解：**

- 所有 IO 都尽量收进 service 层

### 风险 3：API 输出结构不稳定

**缓解：**

- 用 Pydantic `response_model`

### 风险 4：今天贪快直接接 LLM，导致调试维度过多

**缓解：**

- 先 deterministic stub，Day3/Day4 再替换

## Progress

- [ ] Move Day1 plan to `completed/`
- [ ] Create this Day2 ExecPlan
- [ ] Align KB docs to Chinese or bilingual
- [ ] Add `ticket_repo.py`
- [ ] Add `retrieval.py`
- [ ] Add `schemas/graph.py`
- [ ] Update `graph/state.py`
- [ ] Implement `load_ticket_context`
- [ ] Implement `classify_ticket`
- [ ] Implement `retrieve_knowledge`
- [ ] Implement `draft_reply`
- [ ] Add `graph/builder.py`
- [ ] Add `runs.py`
- [ ] Wire router in `main.py`
- [ ] Update frontend types and API client
- [ ] Add detail/result components
- [ ] Make `/tickets` show workflow result
- [ ] Add smoke test
- [ ] Update this plan before end of day

## Decision Log

- Decision: Day2 先做固定 happy path，不做条件路由  
  Why: 降低变量数，先验证 graph 最小闭环

- Decision: 今天先用规则分类和模板草稿  
  Why: 先稳住 orchestration 与 contract，再替换模型实现

- Decision: 今天接 `thread_id` 和 in-memory checkpointer  
  Why: 为 Day3 的 interrupt / resume 预留稳定调用方式

- Decision: retrieval 抽成 service  
  Why: 减少 node 复杂度，保留检索实现替换空间

## Surprises & Discoveries

- Observation:
- Evidence:

## End-of-Day Acceptance

今天收工前，必须满足：

- 可以从 `ticket_id` 触发一次完整 graph 执行
- 浏览器里能看到：
  - 分类结果
  - 检索到的 top-k 文档
  - 一版草稿回复
- 你能解释 4 个节点分别负责什么
- 你能解释为什么今天先不用 interrupt / routing / LangSmith
- 至少 1 个 smoke test 通过
- 本文档已更新，不是只写代码不记设计

## Outcomes & Retrospective

### What was completed

- To fill at end of day

### What I learned

- To fill at end of day

### What remains unclear

- To fill at end of day

### Next best step

Day3 最值得做的是：

**`risk_gate + human_review_interrupt + review queue`**
