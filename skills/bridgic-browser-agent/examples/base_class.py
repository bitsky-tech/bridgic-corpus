"""
BrowserAgentBase — 所有 bridgic 浏览器 Agent 的基类。

使用方式：
    from examples.base_class import BrowserAgentBase
    class MyAgent(BrowserAgentBase):
        ...
"""

import os
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from bridgic.browser.session import Browser
from bridgic.browser.tools import BrowserToolSetBuilder, ToolPreset, BrowserToolSpec
from bridgic.llms.openai import OpenAILlm, OpenAIConfiguration
from bridgic.core.model.types import Message, Role, Tool


class BrowserAgentBase:
    TOOL_PRESET = ToolPreset.INTERACTIVE

    def __init__(self, headless: bool = False):
        self.browser = Browser(
            headless=headless,
            user_data_dir=os.path.expanduser("~/.agent_data"),
        )
        self.llm = OpenAILlm(
            api_key=os.environ["LLM_API_KEY"],
            base_url=os.environ.get("LLM_API_BASE"),
            configuration=OpenAIConfiguration(
                model=os.environ.get("LLM_MODEL", "gpt-4o")
            ),
        )
        self._browser_tools: list[BrowserToolSpec] = []
        self._tool_func_map: dict = {}
        self._llm_tools: list[Tool] = []

        self.run_dir: Optional[Path] = None
        self.logger: Optional[logging.Logger] = None
        self._step: int = 0

    async def setup_run(self, task_name: str):
        """每次 run() 入口必须首先调用。"""
        run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.run_dir = Path(f"logs/{task_name}/{run_id}")
        self.run_dir.mkdir(parents=True, exist_ok=True)

        _logger = logging.getLogger(f"agent.{task_name}")
        _logger.setLevel(logging.INFO)
        h = logging.FileHandler(self.run_dir / "run.log", encoding="utf-8")
        h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        _logger.addHandler(h)
        self.logger = _logger

        await self.browser.start()

        self._browser_tools = BrowserToolSetBuilder.for_preset(self.browser, self.TOOL_PRESET)
        self._tool_func_map = {t.tool_name: t.func for t in self._browser_tools}
        self._llm_tools = [
            Tool(
                name=t.tool_name,
                description=t.tool_description,
                parameters=t.tool_parameters,
            )
            for t in self._browser_tools
        ]

    async def screenshot(self, name: str):
        self._step += 1
        path = self.run_dir / f"step-{self._step:02d}-{name}.png"
        page = await self.browser.get_current_page()
        if page:
            await page.screenshot(path=str(path))

    async def snapshot(self, interactive: bool = True) -> str:
        snap = await self.browser.get_snapshot(interactive=interactive)
        return snap.tree

    async def execute_tool(self, tool_name: str, **params) -> str:
        func = self._tool_func_map.get(tool_name)
        if not func:
            return f"未知工具: {tool_name}"
        try:
            return await func(self.browser, **params)
        except Exception as e:
            return f"执行失败: {e}"

    async def smart_execute(self, description: str, preferred_tools: list[str] = None) -> str:
        tree = await self.snapshot()
        page_info = await self.browser.get_current_page_info()

        tools = self._llm_tools
        if preferred_tools:
            tools = [t for t in tools if t.name in preferred_tools]

        messages = [
            Message.from_text(
                f"当前页面：{page_info.url}\n\n可交互元素：\n{tree}\n\n"
                f"指令：{description}\n\n根据 [ref=eN] 定位元素，选择合适工具执行。",
                role=Role.SYSTEM,
            ),
            Message.from_text("执行", role=Role.USER),
        ]
        tool_calls, _ = await self.llm.aselect_tool(messages=messages, tools=tools)
        if not tool_calls:
            return "未选择工具"
        results = [await self.execute_tool(tc.name, **tc.arguments) for tc in tool_calls]
        return "\n".join(results)

    def find_ref_near_label(
        self,
        snapshot_tree: str,
        label: str,
        role: str = None,
        search_range: int = 15,
    ) -> Optional[str]:
        lines = snapshot_tree.split("\n")
        for i, line in enumerate(lines):
            if f'"{label}"' in line:
                for j in range(i + 1, min(i + search_range, len(lines))):
                    if role and role not in lines[j]:
                        continue
                    m = re.search(r"\[ref=(e\d+)\]", lines[j])
                    if m:
                        return m.group(1)
        return None

    async def click_and_get_new_tab(self, ref: str, wait_ms: int = 1000):
        pages_before = len(self.browser.get_pages())
        await self.execute_tool("click_element_by_ref", ref=ref)
        await self.browser.page.wait_for_timeout(wait_ms)
        pages_after = self.browser.get_pages()
        if len(pages_after) > pages_before:
            return pages_after[-1]
        return None

    async def evaluate_js(self, page, js_code: str):
        try:
            return await page.evaluate(js_code)
        except Exception as e:
            self.logger.warning(f"JS 执行失败: {e}")
            return None
