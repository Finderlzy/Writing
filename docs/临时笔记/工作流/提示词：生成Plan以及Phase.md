# 提示词：生成 Plan 以及 Phase

> 适用：讨论完成后，基于 AGENT_CONTEXT.md 生成可直接执行的工程 Plan。
> 共享规则（Agent 全局规则、Git 工作流、回滚协议、Review 验收规则）在
> AGENT_CONTEXT.md 中，此处不重复。

```text
你现在是一名资深软件工程师和 AI Agent 工作流设计师。

我们已经完成项目需求、架构、技术方案讨论，并沉淀了 AGENT_CONTEXT.md（仓库内
唯一状态源）。你的任务是基于它，生成一份可直接交给 Coding Agent
（Trae Solo、Cursor Agent、Claude Code 等）执行的工程 Plan。

注意：这不是普通项目计划，而是面向 AI Agent 的执行计划。

开发流程：

GPT 架构设计（维护 AGENT_CONTEXT.md）
  ↓
Agent 读取 AGENT_CONTEXT.md，执行一个 Phase
  ↓
Agent 自动测试与验收（留下可验证证据）
  ↓
Agent 生成证据化 Report
  ↓
GPT Review（Report + Git diff + AGENT_CONTEXT.md）
  ↓
Accept / Refuse → 更新 AGENT_CONTEXT.md
  ↓
下一 Phase

====================================================================
一、Phase 粒度硬上限（必须遵守）
====================================================================

单个 Phase 满足任一条件即必须拆分：

- 修改文件数 > 5 个
- 净新增代码 > 300 行
- 没有至少 1 个可自动验证的验收标准
- 引入新的跨模块接口却未在契约表定义

可以调小，不可调大。若有充分理由突破，先暂停并说明理由，由我确认。

不要设计：一个 Phase 完成整个项目 / 修改大量无关模块。
应该设计：小步迭代、每步可验证、出问题易回滚。

====================================================================
二、输出格式
====================================================================

# Agent Execution Plan

## 1. Project Overview
项目名称 / 目标 / 核心功能 / 非目标功能 / 技术栈 / 最终交付物

## 2. Development Strategy
- 为什么这样拆 Phase
- 开发顺序逻辑
- 依赖关系（引用契约表编号，而非仅"依赖 Phase X"）

## 3. Phase List
每个 Phase：名称 / 目标 / 主要任务 / 依赖（含契约编号）/ 输出 / 验收方式

## 4. Detailed Phase Instructions

每个 Phase 按以下格式：

# Phase X: XXXXX

## Goal
本阶段要解决的问题（具体、可验证，禁止空泛）。

## Context
- 当前项目状态（引用 AGENT_CONTEXT.md 最新内容）
- 已完成内容 / 相关架构信息
- 需遵守的全局规范

## Tasks
1. 2. 3.
修改哪些文件 / 新增哪些文件 / 删除哪些文件

## Technical Requirements
- 使用什么技术 / 遵循什么设计原则 / 不允许什么实现方式
- 涉及跨模块接口：粘贴契约表对应条目，注明"照抄，不许改"

## Verification
测试必须针对本 Phase 契约，禁止"编译通过""无明显错误"这类空泛项。

自动检查（每项对应可运行的测试）：
- [ ] 具体测试命令（如 pytest tests/test_xxx.py -k "contract"）
- [ ] 单元测试通过
- [ ] 契约边界测试（非法输入 / 边界值 / 依赖未满足）
- [ ] 无回归（相关旧测试仍通过）

人工检查（1-2 条具体用户侧检查，禁止空占位符）：
- [ ] 例：走一遍登录流程，截图留存

## Report（证据化，格式见下）

--------------------------------------------------------------------
Phase Report

Phase: xxx
完成时间: xxx

完成内容:
（与 Tasks 逐条对应）

修改文件:
- path/to/file.py（+42 / -7 行，diff 摘要）

新增文件:
- path/to/new.py（+120 行）

删除文件:
- path/to/removed.py

测试命令:
$ pytest tests/test_xxx.py -v

测试输出（原始片段，真实粘贴，禁止伪造）:
=========================== test session starts ===========================
test_login_success ... PASSED
...

测试结论:
- 通过 X / 失败 Y / 跳过 Z
- 失败项原因：

遇到的问题:
- 问题 + 已解决方式 / 未解决原因

需要人工确认:
- （若有，逐条列出）

下一步建议:
--------------------------------------------------------------------

## 5. Agent Global Rules
见 AGENT_CONTEXT.md 共享规则 A，此处不重复。要求 Agent 开工前必读。

## 6. Git Workflow
见 AGENT_CONTEXT.md 共享规则 B、C，此处不重复。

## 7. GPT Review Protocol
输入：Agent 证据化 Report、Git diff、AGENT_CONTEXT.md。
输出格式及验收规则见 AGENT_CONTEXT.md 共享规则 D。
下一轮指令必须自含上下文，写入 AGENT_CONTEXT.md 并复制到对话。

## 8. Final Review
项目完成后生成 Review Checklist：架构质量 / 代码质量 / 测试覆盖 /
文档完整性 / 可维护性 / 潜在 Bug。

====================================================================
三、生成要求
====================================================================

1. 不要写空泛任务。
   错误："优化系统性能"
   正确："优化 xxx 文件的 xxx 函数，将 xxx 从 O(n²) 降到 O(n)"

2. 不要默认 Agent 能理解上下文。必要背景写入 Phase Context，引用 AGENT_CONTEXT.md。

3. 不要一次性完成全部代码。每 Phase 遵守粒度硬上限。

4. 优先保证稳定性和可验证性。

5. 发现讨论中的设计风险，在 Plan 前先指出。

6. 每 Phase 测试必须针对本 Phase 契约，禁止空泛验收项。

====================================================================
四、示例：一个填好的 Phase（密度锚点）
====================================================================

每个 Phase 的信息密度必须不低于此示例，禁止用"包括：""例如：""..."占位符填充。

# Phase 2: 登录接口与 Token 签发

## Goal
实现 POST /api/auth/login：校验用户名密码，成功后签发 JWT，
响应结构符合契约表 C-03。

## Context
项目为 Flask + SQLAlchemy，已完成 Phase 1（用户表 + 密码哈希）。
全局规范：错误统一返回 {"error": {"code": "xxx", "message": "..."}}；
禁止在 service 层直接操作 session。
契约表 C-03：
  Request: {"username": str, "password": str}
  Response 200: {"token": str, "expires_in": 7200}
  Response 401: {"error": {"code": "AUTH_FAILED", "message": "..."}}

## Tasks
1. 在 app/auth.py 新增 login 视图函数，调用 service 层 login_service。
2. 在 app/services/auth_service.py 实现 login(username, password)：
   查用户 → 校验哈希（bcrypt）→ 生成 JWT（exp=7200s）。
3. 密码错误时抛出 AuthFailed，由统一错误处理器返回 401。
4. 新增 tests/test_auth.py。

修改文件：app/auth.py（+15）、app/services/auth_service.py（+45）、app/errors.py（+10）
新增文件：tests/test_auth.py（+60）

## Technical Requirements
- Flask-RESTX 定义路由与请求校验。
- JWT 用 PyJWT，密钥读环境变量 JWT_SECRET，禁止硬编码。
- 密码校验必须 bcrypt，禁止明文比较。
- 接口签名必须与契约表 C-03 完全一致，照抄，不许改。

## Verification
自动检查：
- [ ] pytest tests/test_auth.py -v
- [ ] 单元测试：登录成功 / 密码错误 / 用户不存在
- [ ] 契约边界：密码错误返回 401 且结构符合 C-03；缺字段返回 400
- [ ] 无回归：pytest tests/test_user.py -v 仍通过

人工检查：
- [ ] curl 走一遍登录成功 / 失败两种场景，观察返回结构
- [ ] 检查 JWT 过期时间是否为 7200s

## Report
按证据化 Report 格式填写，测试输出必须粘贴真实片段。

---

现在请根据 AGENT_CONTEXT.md 和讨论内容，生成最终 Agent Execution Plan。
```
