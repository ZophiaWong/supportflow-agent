---
name: supportflow-review
description: Review a SupportFlow-style AI workflow project to help a developer understand the current system, assess readiness, find gaps, and plan or implement the next feature. Use for architecture review, code review, onboarding review, feature-readiness review, LangGraph/workflow review, backend/frontend/API review, eval/observability review, demo/readiness review, or interview-oriented project review. Prefer Chinese output unless the user asks otherwise.
---

# SupportFlow Review

## 目标

这个 skill 用于做“能帮助人继续推进项目”的 review，而不是写静态项目介绍。

Review 的产出应该帮助使用者回答：

- 现在系统真实做了什么？
- 新人要从哪里开始读？
- 当前改动或新功能会碰到哪些边界？
- 哪些风险会影响后续实现、演示、面试或生产化？
- 下一步最小可执行改动是什么？

默认使用中文。只有当用户明确要求英文、面试英文稿、PR 英文评论时，才切换语言。

## 核心原则

- 先读再评，不凭记忆或文件名猜测。
- 少写死路径，多用仓库发现命令动态定位代码。
- 区分：已实现、部分实现、仅文档设计、缺失、未知需验证。
- 每个关键判断都要有证据：文件、函数、类、路由、组件、schema、测试、命令输出或文档段落。
- Review 目标是提升长期可维护性和下一步执行力，不是为了显得项目完美。
- Review 不是追求完美代码；当改动整体改善系统健康且风险可控时，优先帮助项目继续前进。
- 不默认重构，不默认实现功能；如果用户要求实现，再从 review 结论转成执行计划。
- 对 AI workflow 项目，优先关注流程控制、状态边界、人工审核、安全动作、可观测性和 eval 证据。

## 适用场景

使用本 skill，当用户要求：

- review 当前项目、模块、PR、功能设计或实现质量
- 让新人快速上手并准备实现一个新功能
- 判断某个能力是否真的实现
- 梳理 LangGraph / workflow / API / frontend / eval / trace / persistence
- 找 production-like gap、demo risk、面试表达风险
- 生成上手路线、改动建议、hardening plan、review comments
- 设计文档树、ExecPlan、任务拆分，但先给建议，等用户确认后再落文件

不适用：

- 用户只要你直接实现一个明确小改动，且不需要审阅上下文
- 泛泛写营销文案
- 脱离代码证据的项目包装

## 默认工作流

### 1. 确认 review 类型

如果用户没有指定，先判断最接近哪一种：

- **Onboarding review**：帮助新人理解项目并找到入口。
- **Architecture review**：审查模块边界、数据流、状态流和扩展性。
- **Feature-readiness review**：判断实现某个新功能前需要知道什么、改哪里、风险是什么。
- **Code review**：审查具体 diff、bug、回归风险、测试缺口。
- **Demo/interview review**：判断项目表达是否可信，哪些话能说，哪些不能说。
- **Hardening review**：找最小生产化增强点。

### 2. 先看整体，再看细节

Review 顺序：

1. 先判断目标是否合理：这个改动或计划是否应该发生，是否符合项目方向。
2. 找主路径：先看最影响系统行为的文件、路由、节点、schema 或组件。
3. 再看支撑面：测试、文档、数据、配置、迁移、生成物。
4. 最后看局部质量：命名、注释、重复、格式、轻微可读性问题。

如果一开始就发现方向性问题，先反馈方向和替代路径，不要花大量篇幅纠结局部代码。

### 3. 动态发现项目结构

优先使用这些命令，不要依赖固定目录：

```bash
rg --files
git status --short
find . -maxdepth 3 -name AGENTS.md -o -name README.md -o -name ARCHITECTURE.md
find docs -maxdepth 4 -type f 2>/dev/null
```

如果是代码 review：

```bash
git diff --stat
git diff --name-only
git diff
```

如果是功能/架构 review，先寻找：

- 项目入口：README、AGENTS、ARCHITECTURE、product specs、active plans
- 后端入口：API routes、app/main、schemas、services
- workflow 入口：graph builder、state、nodes、routing
- 前端入口：pages、components、API client、types
- 质量入口：tests、eval scripts、trace/observability code
- 数据入口：sample tickets、KB、eval fixtures

### 4. 建立“证据地图”

不要把完整路径硬编码进 skill；在每次 review 时生成当前项目的证据地图。

建议格式：

```md
| 关注点        | 当前证据 | 说明                             |
| ------------- | -------- | -------------------------------- |
| workflow 入口 | `...`    | 节点和路由定义位置               |
| 状态 schema   | `...`    | run state / API contract         |
| 人工审核      | `...`    | interrupt/resume 或 review queue |
| 安全动作      | `...`    | proposed/executed action 分离    |
| 持久化        | `...`    | checkpoint/store/timeline        |
| eval          | `...`    | 数据集、runner、scoring          |
```

### 5. 做 review

按 review 类型选择关注点：

**Onboarding review**

- 项目一句话
- 最先读哪 5-8 个文件
- 一条主流程如何穿过 backend / workflow / frontend
- 哪些概念必须先懂
- 新人第一个小任务建议

**Architecture review**

- 模块边界是否清楚
- 数据结构和状态流是否稳定
- workflow 路由是否可解释
- API contract 是否和 UI 一致
- 是否存在隐式耦合或重复状态源

**Feature-readiness review**

- 新功能要改哪些区域
- 当前设计支持点和阻碍点
- 最小实现路径
- 需要新增或更新的测试/eval/docs
- 是否需要 ExecPlan 或文档树调整

**Code review**

- 先列 bug、回归风险、安全风险和缺测试
- 再列可维护性问题
- 最后给小范围修复建议
- 不把风格问题放在功能问题前面
- 标注评论级别：`Blocker`、`Should fix`、`Consider`、`Nit`、`FYI`
- 明确 review 范围：如果只看了 backend、workflow、UI 或 tests，要说明

**Demo/interview review**

- 哪些能力可以有把握地说
- 哪些只是 demo-level
- 哪些说法容易被追问击穿
- 用代码证据支撑 30 秒回答和深挖回答

## Review Checklist

参考成熟工程组织的 review 实践，除非用户只要求很窄的审阅，否则至少扫过这些点：

| 维度     | 关注问题                                                         |
| -------- | ---------------------------------------------------------------- |
| 设计     | 这个改动是否属于当前系统，是否和已有边界一致，是否过度抽象       |
| 功能     | 是否满足用户目标，边界条件和失败路径是否清楚                     |
| 复杂度   | 是否比需求需要的更泛化、更隐式、更难读                           |
| 测试     | 测试是否会在行为坏掉时失败，是否覆盖核心路径和风险路径           |
| 文档     | 改变运行、使用、API、状态、eval 或 demo 行为时是否更新文档       |
| 安全     | 是否涉及凭证、权限、外部副作用、用户数据、注入、依赖或供应链风险 |
| 可观测性 | 出错后是否能定位节点、请求、run、决策或动作                      |
| 用户影响 | UI/API/审核员流程是否可理解，错误是否可恢复                      |
| 可维护性 | 命名、注释、模块边界、重复逻辑、未来改动成本                     |

## Review 维度

优先检查这些维度，按项目实际情况取舍：

- Workflow control：节点、路由、终止状态、失败状态、resume 语义
- State and contracts：Pydantic/schema/types/API response 是否一致
- Retrieval/RAG：数据来源、检索策略、citation、低置信度处理
- Guardrails：策略规则、风险分类、缺失证据时的行为
- Human review：审核入口、approve/edit/reject、状态恢复、审计记录
- Action safety：proposed vs executed、副作用、幂等、失败记录
- Persistence：checkpoint、业务状态、运行事件、重启恢复
- Observability：timeline、trace、错误定位、可回放性
- Evals：fixture 质量、指标、bad case、回归门槛
- Frontend UX：主流程是否能完成、状态是否清楚、错误是否可理解
- Demo readiness：启动路径、数据重置、可复现性、说明是否可信
- Maintainability：模块边界、重复逻辑、隐式依赖、扩展成本

## 输出模板

### 快速 review

```md
## 结论

一句话判断。

## 证据

| 结论 | 证据 | 说明 |
| ---- | ---- | ---- |

## 主要问题

1. `[Blocker|Should fix|Consider|Nit|FYI]` ...

## 下一步

1. 最小可执行改动
2. 需要补的测试或文档
```

### 新人上手 review

```md
## 上手路线

1. 先读 ...
2. 再跑 ...
3. 跟一条请求看 ...

## 核心心智模型

- ...

## 第一个可做任务

- 目标：
- 涉及区域：
- 风险：
- 验证：
```

### 功能准备 review

```md
## 功能目标

## 当前支持度

| 区域 | 当前状态 | 对新功能的影响 |
| ---- | -------- | -------------- |

## 最小实现路径

1. ...

## 风险和测试

- 风险：
- 测试：
- 文档/ExecPlan：
```

### 面试/演示 review

```md
## 可以稳定表达

- ...

## 谨慎表达

- ...

## 不建议声称

- ...

## 30 秒回答

## 深挖回答
```

## 文档树建议

如果 review 发现需要新文档，不要直接创建一整套目录。先提出建议，等待用户确认。

建议格式：

```md
我建议新增/调整这些文档：

| 文档 | 目的 | 为什么现在需要 | 是否必须 |
| ---- | ---- | -------------- | -------- |

确认后我再创建或迁移。
```

可以建议新文档树，不必严格服从当前结构；但必须说明迁移成本、查找成本和维护成本。

## Review 评论规则

评论要让作者知道：问题是什么、为什么重要、怎么收敛。

推荐格式：

```md
- [级别] 位置：`path` / 函数 / 组件
  问题：...
  影响：...
  建议：...
```

级别定义：

- `Blocker`：会导致错误行为、安全风险、数据破坏、demo 失败或核心设计走偏。
- `Should fix`：不一定立即坏，但会明显增加回归、维护或误解风险。
- `Consider`：建议改进，有合理替代方案，不应阻塞。
- `Nit`：轻微命名、格式、局部可读性问题。
- `FYI`：背景知识或后续可考虑事项，不要求本次处理。

不要把所有评论都写成必须修改。风格偏好如果没有项目规则支撑，最多作为 `Nit` 或 `Consider`。

## 修改建议分级

- P0：当前说法或实现会误导使用者、导致 demo/测试失败、安全风险、数据破坏，或让新人走错入口。
- P1：影响核心 workflow、安全动作、人工审核、状态恢复、API contract。
- P2：影响 eval、trace、错误定位、测试覆盖或长期维护。
- P3：文档组织、命名、开发体验、演示 polish。
- P4：生产化增强，如真实集成、auth、多租户、部署、监控、向量库。

## AI Review 边界

这个 skill 可以作为第一轮或第二轮 review，但不能替代人类判断。

- 对高风险结论要给证据，不能只给模型判断。
- 对安全、权限、外部副作用、数据持久化、并发、部署和依赖变更，要建议人工复核。
- 对自动化输出要验证：运行相关测试、读关键路径、必要时手动 smoke。
- 当上下文不足时，明确写“未知，需要验证”，不要补完故事。
- 如果用户要实现修复，先把 review 结论转成最小任务和验证标准。

## 验证

根据 review 范围选择验证，不要机械全跑。

常见验证类型：

```bash
pytest
npm test -- --run
npm run build
python scripts/run_offline_eval.py
python scripts/draw_langgraph.py
```

如果命令和当前项目不匹配，先通过 README、package files、pyproject 或 Makefile 查找真实命令。

## 风格

- 默认中文。
- 先给结论，再给证据。
- 发现问题要具体到文件/函数/行为。
- 不夸大项目成熟度。
- 不用“可能很复杂”这类空话；说明复杂在哪里、影响什么、怎么降风险。
- 最终建议要能转成一个小任务、一个测试或一个文档更新。
