# 常用模式参考

## 元素定位策略（按优先级降级）

| 优先级 | 方法 | 适用场景 |
|--------|------|----------|
| 1 | `find_ref_near_label(tree, "标签", role="combobox")` | 已知标签文字，ref 每次动态变化 |
| 2 | `execute_tool("click_element_by_ref", ref="e5")` | 已知固定 ref（探索阶段确认稳定） |
| 3 | `smart_execute("描述意图", ["tool_name"])` | ref 不确定，让 LLM 选择 |
| 4 | `evaluate_js(page, "() => ...")` | a11y 树无法定位，JS 直接操作 |

---

## 工具预设选择

| 预设 | 工具数 | 适用 |
|------|--------|------|
| `ToolPreset.MINIMAL` | 11 | 只需导航和快照 |
| `ToolPreset.SCRAPING` | 14 | 数据抓取 |
| `ToolPreset.FORM_FILLING` | 20 | 表单填写 |
| `ToolPreset.INTERACTIVE` | 39 | 完整交互（默认） |
| `ToolPreset.COMPLETE` | 69 | 全部功能 |

---

## 登录状态检测

页面无密码输入框则视为已登录，直接跳过：

```python
tree = await self.snapshot()
if "password" not in tree.lower():
    self.logger.info("已登录，跳过")
    return
```

---

## 等待策略

优先条件等待，不用固定 `sleep`：

```python
# 等待页面跳转
await self.browser.page.wait_for_url("**/dashboard**")

# 等待内容加载完成
await self.browser.page.wait_for_load_state("networkidle")

# 等待特定元素出现
await self.browser.page.wait_for_selector(".result-list")
```

---

## 副作用检查

**点击后检查是否开了新 Tab：**

```python
new_tab = await self.click_and_get_new_tab(ref)
if new_tab:
    # 在新 Tab 内操作
    await self.browser.close_page(new_tab)
else:
    # 当前页跳转，继续操作
    pass
```

**提交后监听 toast（静默成功场景）：**

```python
await self.execute_tool("click_element_by_ref", ref=submit_ref)
try:
    await self.browser.page.wait_for_selector(".toast", timeout=3000)
    self.logger.info("提交成功（toast 出现）")
except:
    self.logger.warning("未检测到 toast，检查页面状态")
```

---

## LLM 结构化内容提取

```python
from pydantic import BaseModel
from bridgic.core.model.types import Message, Role
from bridgic.core.model.protocols import PydanticModel

class Item(BaseModel):
    name: str
    price: str

class ItemList(BaseModel):
    items: list[Item]

async def extract_items(self) -> ItemList:
    tree = await self.snapshot(interactive=False)  # 全量树
    return await self.llm.astructured_output(
        messages=[
            Message.from_text("从以下无障碍树中提取列表。", role=Role.SYSTEM),
            Message.from_text(tree, role=Role.USER),
        ],
        constraint=PydanticModel(model=ItemList),
    )
```

---

## 单元测试模板

```python
# task-<名称>-v1-test.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path


@pytest.mark.asyncio
async def test_setup_run_creates_dir():
    """setup_run 应创建带时间戳的日志目录"""
    agent = MyTaskAgent()
    with patch.object(Path, "mkdir"):
        await agent.setup_run("test-task")
    assert agent.run_dir is not None
    assert "test-task" in str(agent.run_dir)


@pytest.mark.asyncio
async def test_find_ref_near_label():
    """find_ref_near_label 应能从 snapshot 中按标签找到 ref"""
    agent = MyTaskAgent()
    snapshot = '- generic "Appeal status"\n- combobox [ref=e42]'
    ref = agent.find_ref_near_label(snapshot, "Appeal status", role="combobox")
    assert ref == "e42"


@pytest.mark.asyncio
async def test_step_success():
    """核心步骤正常路径"""
    agent = MyTaskAgent()
    agent.browser = AsyncMock()
    agent.logger = MagicMock()
    agent.run_dir = MagicMock()
    agent.browser.get_snapshot.return_value = MagicMock(tree="- button [ref=e5]")
    agent.browser.get_element_by_ref.return_value = AsyncMock()
    # 调用被测方法，断言关键操作被调用
    ...


@pytest.mark.asyncio
async def test_step_element_not_found():
    """元素不存在时应记录错误并抛出异常"""
    agent = MyTaskAgent()
    agent.browser = AsyncMock()
    agent.logger = MagicMock()
    agent.run_dir = MagicMock()
    agent.browser.get_element_by_ref.return_value = None
    with pytest.raises(Exception):
        await agent.some_step()
```
