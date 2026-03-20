---
name: bridgic-browser-agent
description: |
  Activates when the user asks to build a browser automation agent with Bridgic,
  convert a browser workflow into reusable code, explore a web page via CLI and
  generate an agent, or automate any web task using bridgic-browser and the
  Bridgic agent framework (ASLAutoma, ReCentAutoma). Covers the full workflow:
  CLI exploration, static/dynamic element analysis, execution path documentation,
  robust bridgic Agent code generation (runtime ref resolution, never hardcoded),
  logging, screenshots, versioning, unit tests, and privacy/env-var handling.
---

# bridgic-browser-agent

## 收到任务后，立即执行以下命令【不得推迟】

```bash
bridgic-browser open <用户提供的 URL>
bridgic-browser snapshot -i
```

**在拿到真实的 snapshot 输出（含 `[ref=eN]` 的无障碍树）之前，禁止进行任何分析、规划或编码。**
不允许凭用户描述、常识或推断来假设页面结构。页面的真实结构只能来自 CLI 的实际输出。

---

## 强制交付物【任务未完成的判定依据】

- [ ] `task-<名称>-path.md` — 基于真实 CLI 探索的执行路径落盘文档（含动静态分析）
- [ ] `task-<名称>-vN.py` — bridgic Agent 代码（继承 `BrowserAgentBase`，含日志 + 截图；首次为 v1，每次迭代递增）
- [ ] `task-<名称>-vN-test.py` — 对应单元测试（产出时机由用户确认，见步骤 7）
- [ ] 隐私审查已落盘 — 审查结论写入 `task-<名称>-path.md` 的「前提条件」区块，并同步至 `README.md` 的「必需环境变量」，同时向用户口头确认
- [ ] `README.md` — 任务档案，追加记录本次任务信息（见步骤 8 格式）

**以上五项全部完成，才算任务结束。**

---

## 界面理解优先级

```
无障碍树（a11y tree）> 视觉截图 + 视觉模型 > 人类介入
```

- 优先：`bridgic-browser snapshot -i`，观察元素的**标签文字、角色、层级关系**
- 其次：`bridgic-browser screenshot page.png`，截图发给视觉模型理解后指导操作
- 兜底：暂停 + 截图上报，请求人类介入

---

## 动态 vs 静态识别【编码前必须完成此分析】

探索页面时，必须区分哪些是静态的、哪些是动态的，这决定了代码如何定位元素和处理数据。

### 静态（跨多次运行保持不变，可作为代码中的定位锚点）
- 元素的**标签文字**（如 `"Appeal status"`、`"Search"`、`"Login"`）
- 元素的**角色/类型**（如 `button`、`combobox`、`textbox`）
- 页面的**结构和层级**（标签与其下方输入框的相邻关系）
- **URL 的路径结构**（如 `/dashboard`、`/orders`）
- **等待信号的文字**（如加载完成后出现的固定文本）

### 动态（每次运行都会变化，禁止在代码中硬编码）
- **`[ref=eN]` 的 ref 值**：每次 snapshot 都会重新生成，**绝对不能硬编码到代码里**
- **数据内容**：订单号、金额、日期、用户名等
- **分页/计数信息**：当前页码、总条数
- **URL 中的 ID 参数**：如 `/order/12345`

### 识别结果如何影响编码
| 元素类型 | 代码中的处理方式 |
|----------|-----------------|
| 静态标签 + 动态 ref | 运行时用 `find_ref_near_label("标签文字", role="...")` 动态获取 ref |
| 静态按钮文字 | 运行时用 `find_ref_near_label("按钮文字", role="button")` |
| 完全不确定的元素 | 运行时用 `smart_execute("描述意图", ["tool_name"])` 让 LLM 定位 |
| 数据内容提取 | 用 `astructured_output` 或 `evaluate_js` 提取，结果参数化 |
| 用户输入参数 | 做成函数入参，从环境变量或调用方传入 |

**核心原则：代码里只写静态的"描述"，运行时动态解析出 ref，再执行操作。**

---

## 执行顺序【严格按序，上一步没有真实产出则不得进入下一步】

### 步骤 1 — CLI 探索【必须先于一切动作执行】

**门控条件：必须拿到含真实 `[ref=eN]` 的 snapshot 输出，才能进入步骤 2。**

用 `bridgic-browser` CLI 亲手走完整个业务流程，每步都要实际执行并观察结果：

```bash
bridgic-browser open <URL>
bridgic-browser snapshot -i              # 了解页面结构，注意元素标签和角色
bridgic-browser snapshot -i -F           # 仅视口内可交互元素
bridgic-browser snapshot -s 30000        # 输出截断时继续

bridgic-browser fill @eN "value"
bridgic-browser click @eN
bridgic-browser select @eN "option"
bridgic-browser wait-for "文字"
bridgic-browser wait-for "文字" --gone
bridgic-browser snapshot -i              # 每次操作后必须重新获取

bridgic-browser screenshot page.png     # 无障碍树无法理解时截图
bridgic-browser tabs                    # 点击后检查是否开了新 Tab
bridgic-browser switch-tab <page_id>
bridgic-browser press "Enter"
bridgic-browser scroll --dy 300
bridgic-browser info
```

探索时重点观察并记录：
- 每个操作目标元素的**标签文字和角色**（这是代码中的定位锚）
- 操作后页面的**真实变化**（URL / 元素出现消失 / 内容更新）
- **等待信号**（出现什么文字或元素代表操作完成）
- **动态 vs 静态**（对照上方分析框架逐一标注）
- 点击后是否开了新 Tab

---

### 步骤 2 — 执行路径落盘

**门控条件：步骤 1 必须已完成，落盘内容必须来自真实 CLI 探索，不得凭空填写。**

保存为 `task-<名称>-path.md`：

```
# 任务名称：[XXX]

## 前提条件
- 登录状态 / 需要预设的环境变量列表

## 动态 vs 静态分析
### 静态元素（代码中用作定位锚）
- "Appeal status" 标签 + 其下方 combobox → 用 find_ref_near_label("Appeal status", role="combobox")
- "Search" button → 用 find_ref_near_label("Search", role="button")
- 登录后跳转 URL 含 /dashboard → 用 wait_for_url("**/dashboard**")

### 动态元素（运行时变化，禁止硬编码）
- 所有 [ref=eN] 值 → 每次运行时动态获取
- 订单号、金额、日期等数据字段 → 运行时提取
- [其他动态内容...]

## 执行路径
### Step 1: [描述]
- 定位方式: find_ref_near_label("标签文字", role="角色")（不写具体 ref 值）
- 等待信号: wait-for "实际出现的文字"
- 验证: snapshot 确认元素 X 出现 / URL 变为 /xxx
- 副作用: 是否新开 Tab / 是否触发下载

### Step 2: ...

## 可能的错误点与处理方式
## LLM 参与点（哪些步骤需要理解判断）
```

---

### 步骤 3 — 生成 bridgic Agent 代码

**门控条件：`task-<名称>-path.md` 必须已存在，代码必须遵守以下规则。**

**元素操作强制规则：**
- **禁止在代码中硬编码任何 ref 值**（如 `ref="e5"` 这类写法绝对禁止）
- 所有 ref 必须在运行时通过静态锚点动态获取：

```python
# 正确：运行时动态找 ref
tree = await self.snapshot()
ref = self.find_ref_near_label(tree, "Appeal status", role="combobox")
await self.execute_tool("select_dropdown_option_by_ref", ref=ref, text=status)

# 错误：硬编码 ref（绝对禁止）
await self.execute_tool("click_element_by_ref", ref="e42")  # ❌ 每次运行 ref 都会变
```

**其他编码要求：**
- 所有代码**必须使用 OOP，继承 `BrowserAgentBase`**，步骤拆为独立方法，入口为 `run()`
- 基类完整实现见 `examples/base_class.py`，API 说明见 `references/base-class.md`
- 各场景代码示例见 `examples/` 目录
- LLM 初始化固定从环境变量读取：`LLM_API_KEY` / `LLM_API_BASE` / `LLM_MODEL`

**元素定位方法选择（按优先级）：**

| 优先级 | 方法 | 适用场景 |
|--------|------|----------|
| 1 | `find_ref_near_label(tree, "标签", role="角色")` | 有固定标签文字的元素 |
| 2 | `smart_execute("操作描述", ["tool"])` | 标签不固定或结构复杂 |
| 3 | `evaluate_js(page, "() => ...")` | a11y 树无法覆盖的数据提取 |

---

### 步骤 4 — 静态检查

- [ ] 代码中是否有任何硬编码的 ref 值（如 `ref="e5"`）？有则必须修改
- [ ] 所有元素操作是否都先获取新 snapshot、动态解析 ref？
- [ ] 动态等待是否有超时上限（不用固定 `sleep`）
- [ ] LLM 调用是否有 fallback
- [ ] 非幂等操作是否有前置验证
- [ ] `setup_run()` 是否在 `run()` 入口调用
- [ ] 每个关键步骤后是否调用 `self.screenshot(name)`（含异常路径）
- [ ] 所有敏感信息是否通过环境变量注入，无硬编码

---

### 步骤 5 — 初步执行验证

**实际运行代码**，确认日志目录创建、截图生成、核心路径通过。

若执行失败：
- **禁止直接修改当前版本文件**
- 回到步骤 1 重新 CLI 探索，确认页面真实状态，不得凭猜测改代码
- 找到根因后，创建下一个版本（vN+1.py），走完步骤 2→3→4→5 的完整流程

---

### 步骤 6 — 隐私审查（必须向用户确认）

1. 列出已用环境变量处理的信息
2. 列出建议抽离为环境变量的信息（附建议变量名）
3. 询问用户：是否有额外需要保护的信息或补充？

根据反馈更新代码，并将所有环境变量同步到落盘文档「前提条件」中。

---

### 步骤 7 — 编写单元测试（`task-<名称>-vN-test.py`）

**测试产出时机：在生成代码后，先询问用户：**

> "是否现在生成对应的单元测试？还是等您确认最终版本后再统一生成？"

- 用户选择**立即生成**：针对当前版本生成 `vN-test.py`，后续每个新版本迭代时同步更新测试
- 用户选择**最终版本后生成**：跳过本步骤，在用户明确表示「当前版本是最终版本」后，再生成 `vN-test.py`；迭代期间不产出测试文件

覆盖内容：核心步骤正常路径、关键错误场景（元素找不到 / LLM 返回异常格式）、`setup_run()` 正确创建日志目录。
测试模板见 `references/patterns.md`。

---

### 步骤 8 — 版本管理与 README 落档

**版本规则（强制）：**
- **任何时候都不得直接修改已有版本的 `.py` 文件**
- 初次交付为 `v1`；每次迭代递增版本号，产生 `v(N+1).py`，以此类推
- `task-<名称>-path.md` 在每个版本迭代时同步更新

**两种触发场景：**

| 场景 | 触发条件 | 完整流程 |
|------|---------|---------|
| 首次运行 | 任务初次交付 | 步骤 1→2→3→4→5→6→7→8 |
| 迭代运行 | 执行失败 / 用户反馈问题 | 步骤 1→2→3→4→5→6→（7，若需要）→8 |

迭代时的完整步骤：
1. 回到步骤 1，CLI 重新探索，确认页面当前真实状态（若页面无变化可快速过）
2. 更新 `task-<名称>-path.md`（记录本次迭代原因和变化点）
3. 创建新版本 `v(N+1).py`，**禁止修改旧版本文件**
4. 重走步骤 4（静态检查）+ 步骤 5（执行验证）
5. 若涉及新的敏感信息，重走步骤 6（隐私审查）
6. 若已确定此版本为最终版本且测试尚未生成，执行步骤 7

**README.md 落档（每次任务完成或迭代后必须执行）：**

在工作目录下维护一个 `README.md`（不存在时创建，存在时追加）。每次任务完成后追加一条记录，格式如下：

```markdown
## [任务名称] — vN  （YYYY-MM-DD）

- **目标 URL**：<URL>
- **任务描述**：<一句话说明自动化了什么>
- **交付文件**：
  - `task-<名称>-path.md`
  - `task-<名称>-vN.py`
  - `task-<名称>-vN-test.py`（若已生成，否则标注「待生成」）
- **必需环境变量**：
  - `VAR_NAME` — 用途说明
- **关键执行路径摘要**：<2-4 行，描述主要步骤>
- **已知注意事项 / 坑**：<本次探索中发现的页面特殊行为>
- **版本变更记录**：
  - v1：初始版本
  - vN：<本次改动原因>
```

README.md 的作用是让下次打开项目时，无需重新探索即可快速了解历史任务的背景、配置和注意事项。

---

## 任务完成判定

1. `task-<名称>-path.md` 已创建，含动静态分析和完整执行路径
2. `task-<名称>-vN.py` 已创建，无硬编码 ref，OOP 结构，实际执行通过（每次迭代产生新版本，旧版本不得修改）
3. `task-<名称>-vN-test.py` 已创建（针对最终确认版本），覆盖正常路径和关键错误场景
4. 已向用户完成隐私审查汇报并得到确认
5. `README.md` 已追加本次任务记录，含 URL、交付文件列表、环境变量、关键路径摘要、版本变更记录

---

## 编码原则

1. **OOP 优先**：继承 `BrowserAgentBase`，步骤拆为独立方法，入口为 `run()`
2. **禁止硬编码 ref**：ref 每次 snapshot 都会变，代码里只写静态锚点，运行时动态解析
3. **定位优先级**：`find_ref_near_label(静态标签)` → `smart_execute(意图描述)` → `evaluate_js`
4. **等待策略**：条件等待，不用固定 `sleep`
5. **副作用检查**：点击后用 `click_and_get_new_tab()` 检测新 Tab，提交后监听 toast
6. **LLM 调用**：内容提取用 `astructured_output`；操作决策用 `smart_execute(preferred_tools=[...])`
7. **错误分层**：可重试 → 重新 snapshot + 重试；需判断 → 截图 + 有意义异常；不可恢复 → 终止上报

> **参考文档：** `references/base-class.md`（API）| `references/patterns.md`（模式与测试模板）
> **代码示例：** `examples/base_class.py` | `examples/fixed_steps_agent.py` | `examples/auto_decision_agent.py` | `examples/human_review_agent.py` | `examples/pagination_scraper.py`
> **浏览器操作通识：** `browser-operation-knowledge` Skill
