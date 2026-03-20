"""
LLM 自主决策型 Agent 示例

适用：操作路径不固定、需要 LLM 动态规划每步操作的任务。
ReCentAutoma 自动循环：snapshot → LLM 选工具 → 执行 → 再 snapshot，直到 stop_condition 满足。
"""

import asyncio

from bridgic.browser.tools import ToolPreset
from bridgic.core.agentic.recent import ReCentAutoma, StopCondition
from base_class import BrowserAgentBase


class AutoDecisionAgent(BrowserAgentBase):

    TOOL_PRESET = ToolPreset.INTERACTIVE

    async def run(self, goal: str):
        await self.setup_run("auto-decision")
        self.logger.info(f"目标: {goal}")
        try:
            agent = ReCentAutoma(
                llm=self.llm,
                tools=self._browser_tools,
                stop_condition=StopCondition(
                    max_iteration=30,
                    max_consecutive_no_tool_selected=3,
                ),
            )
            result = await agent.arun(goal=goal)
            self.logger.info(f"完成: {result}")
            await self.screenshot("done")
            return result
        except Exception as e:
            self.logger.error(f"失败: {e}")
            await self.screenshot("error")
            raise
        finally:
            self.logger.info(f"日志已保存至 {self.run_dir}")
            await self.browser.kill()


if __name__ == "__main__":
    asyncio.run(AutoDecisionAgent(headless=False).run(goal="在示例网站上完成 XXX 任务"))
