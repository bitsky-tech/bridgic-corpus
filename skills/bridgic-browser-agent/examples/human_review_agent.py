"""
人类介入型 Agent 示例（Human-in-the-Loop）

适用：需要人工审批、二次确认或 CAPTCHA 处理的任务。

流程：
  execute_worker → review_worker（抛出 Interaction 暂停）
    → 调用方收集人类输入 → load_from_snapshot 恢复执行
    → finalize_worker
"""

import asyncio

from bridgic.asl import ASLAutoma, graph
from bridgic.core.automa import worker
from bridgic.core.automa.interaction import (
    Interaction,
    InteractionException,
    InteractionFeedback,
)
from base_class import BrowserAgentBase


# ── Worker 定义 ───────────────────────────────────────────────────────────────

async def execute_worker(url: str) -> dict:
    """执行主要业务逻辑，返回需要人类确认的数据。"""
    # 示例：此处替换为实际操作
    return {"order_id": "12345", "amount": "100.00", "action": "approve"}


async def review_worker(data: dict) -> dict:
    """触发人类介入，暂停流程等待确认。"""
    raise Interaction(
        message=f"请确认操作：订单 {data['order_id']}，金额 {data['amount']}，操作 {data['action']}",
        data=data,
    )


async def finalize_worker(data: dict, feedback: str) -> str:
    """根据人类反馈完成最终操作。"""
    # 示例：此处替换为实际操作
    return f"已完成：{feedback}"


# ── Workflow 定义 ─────────────────────────────────────────────────────────────

class ReviewWorkflow(ASLAutoma):
    with graph as g:
        execute = execute_worker
        review = review_worker
        finalize = finalize_worker
        +execute >> review >> ~finalize


# ── Agent ─────────────────────────────────────────────────────────────────────

class HumanReviewAgent(BrowserAgentBase):

    async def run(self, url: str):
        await self.setup_run("human-review")
        self.logger.info("任务开始")
        try:
            result = await ReviewWorkflow().arun(url=url)
        except InteractionException as e:
            await self.screenshot("waiting-human")
            for interaction in e.interactions:
                self.logger.info(f"等待人类确认: {interaction.message}")
                print(f"\n需要确认: {interaction.message}")

            human_input = input("请输入确认内容（approve/reject）: ").strip()
            self.logger.info(f"人类输入: {human_input}")

            feedback = [
                InteractionFeedback(interaction_id=e.interactions[0].id, data=human_input)
            ]
            restored = ReviewWorkflow.load_from_snapshot(e.snapshot)
            result = await restored.arun(feedback_data=feedback)

        await self.screenshot("done")
        self.logger.info(f"任务完成: {result}")
        return result


if __name__ == "__main__":
    asyncio.run(HumanReviewAgent(headless=False).run(url="https://example.com"))
