# BrowserAgentBase — API 参考

所有生成的 bridgic Agent 必须继承此基类。完整实现见 `examples/base_class.py`。

## 初始化

```python
agent = MyAgent(headless=False)
```

构造函数自动初始化 `self.browser`（Browser）和 `self.llm`（OpenAILlm），
LLM 凭据从环境变量读取：`LLM_API_KEY` / `LLM_API_BASE` / `LLM_MODEL`。

子类可覆盖 `TOOL_PRESET` 类变量控制工具集：

```python
class MyAgent(BrowserAgentBase):
    TOOL_PRESET = ToolPreset.COMPLETE  # 默认 INTERACTIVE
```

## 方法

### `await setup_run(task_name: str)`
**每次 `run()` 入口必须首先调用。**
创建带时间戳的日志目录 `logs/<task_name>/<时间戳>/`，初始化 logger 和浏览器工具集。
调用后可用：`self.run_dir`、`self.logger`、`self._browser_tools`。

---

### `await screenshot(name: str)`
关键步骤后截图，保存为 `step-<序号>-<name>.png`。
**出错时也必须调用**（截图名用 `"error"`）。

---

### `await snapshot(interactive=True) -> str`
获取无障碍树文本。**每次页面变化后必须重新调用，不得复用旧 ref。**
- `interactive=True`：只返回可交互元素（操作时用）
- `interactive=False`：返回全量树（内容提取时用）

---

### `await execute_tool(tool_name: str, **params) -> str`
按名字直接执行浏览器工具，内置错误处理。

```python
await self.execute_tool("click_element_by_ref", ref="e5")
await self.execute_tool("select_dropdown_option_by_ref", ref="e12", text="Pending")
await self.execute_tool("navigate_to_url", url="https://example.com")
```

---

### `await smart_execute(description: str, preferred_tools: list[str] = None) -> str`
**当 ref 不确定时使用。** 让 LLM 看当前 snapshot，自动选择并执行合适的工具。
`preferred_tools` 限制可选工具范围，减少误选（推荐始终传入）。

```python
await self.smart_execute("点击登录按钮", ["click_element_by_ref"])
await self.smart_execute(f"在用户名输入框输入 {username}", ["input_text_by_ref"])
```

---

### `find_ref_near_label(snapshot_tree, label, role=None, search_range=15) -> str | None`
从 snapshot 文本中，按标签文字找附近元素的 ref。

```python
# 找 "Appeal status" 标签附近的 combobox
ref = self.find_ref_near_label(tree, "Appeal status", role="combobox")

# 找 "Search" 附近的 button
ref = self.find_ref_near_label(tree, "Search", role="button")
```

返回 `None` 时，降级到 `smart_execute`。

---

### `await click_and_get_new_tab(ref: str, wait_ms=1000) -> page | None`
点击可能新开 Tab 的元素，返回新 Tab 的 page 对象（若有），否则返回 `None`。
操作完新 Tab 后调用 `await self.browser.close_page(page)` 关闭。

```python
new_tab = await self.click_and_get_new_tab(order_ref)
if new_tab:
    data = await self.evaluate_js(new_tab, "() => document.title")
    await self.browser.close_page(new_tab)
```

---

### `await evaluate_js(page, js_code: str)`
直接执行 JS 提取页面内容，a11y 树不满足时使用（兜底手段）。
`js_code` 须为 `() => { return ...; }` 格式。失败时返回 `None` 并记录 warning。

```python
data = await self.evaluate_js(page, """
    () => ({
        title: document.title,
        amount: document.querySelector('.amount')?.innerText,
    })
""")
```
