"""
步骤固定型 Agent 示例：登录 → 筛选状态 → 抓取列表 → 进入详情页提取数据

适用：操作路径明确、步骤固定的任务。
"""

import asyncio
import os
import json

from bridgic.browser.tools import ToolPreset
from base_class import BrowserAgentBase


class OrderScraperAgent(BrowserAgentBase):

    TOOL_PRESET = ToolPreset.COMPLETE
    TARGET_URL = os.environ.get("TARGET_URL", "https://example.com")

    def __init__(self, headless: bool = False):
        super().__init__(headless=headless)
        self.orders_data = []

    async def step1_login(self):
        self.logger.info("Step: 登录")
        await self.execute_tool("navigate_to_url", url=self.TARGET_URL)
        await self.browser.page.wait_for_load_state("networkidle")

        tree = await self.snapshot()
        if "password" not in tree.lower():
            self.logger.info("已登录，跳过")
            await self.screenshot("already-logged-in")
            return

        await self.smart_execute(
            f"在用户名输入框输入 {os.environ['SITE_USERNAME']}", ["input_text_by_ref"]
        )
        await self.smart_execute(
            f"在密码输入框输入 {os.environ['SITE_PASSWORD']}", ["input_text_by_ref"]
        )
        await self.smart_execute("点击登录按钮", ["click_element_by_ref"])
        await self.browser.page.wait_for_url("**/dashboard**")
        await self.screenshot("after-login")

    async def step2_filter(self, status: str = "Pending"):
        self.logger.info(f"Step: 筛选状态 = {status}")
        tree = await self.snapshot()

        # 优先标签定位，找不到降级到 smart_execute
        dropdown_ref = self.find_ref_near_label(tree, "Appeal status", role="combobox")
        if dropdown_ref:
            await self.execute_tool("select_dropdown_option_by_ref", ref=dropdown_ref, text=status)
        else:
            await self.smart_execute(
                f"选择 Appeal status 下拉框中的 {status}", ["select_dropdown_option_by_ref"]
            )

        tree = await self.snapshot()
        search_ref = self.find_ref_near_label(tree, "Search", role="button")
        if search_ref:
            await self.execute_tool("click_element_by_ref", ref=search_ref)
        else:
            await self.smart_execute("点击 Search 按钮", ["click_element_by_ref"])

        await self.browser.page.wait_for_load_state("networkidle")
        await self.screenshot("after-filter")

    async def step3_collect_orders(self) -> list:
        self.logger.info("Step: 收集订单列表")
        import re
        tree = await self.snapshot()
        orders = [
            {"order_id": m[0], "ref": m[1]}
            for m in re.findall(r'button "(\d{20,})" \[ref=(e\d+)\]', tree)
        ]
        self.logger.info(f"找到 {len(orders)} 条订单")
        await self.screenshot("order-list")
        return orders

    async def step4_extract_details(self, orders: list):
        self.logger.info("Step: 提取订单详情")
        for i, order in enumerate(orders, 1):
            self.logger.info(f"  [{i}/{len(orders)}] {order['order_id']}")
            new_tab = await self.click_and_get_new_tab(order["ref"])
            if new_tab:
                detail = await self.evaluate_js(new_tab, """
                    () => {
                        const t = document.body.innerText;
                        const get = (label) => {
                            const m = t.match(new RegExp(label + '[:\\s]+([^\\n]+)', 'i'));
                            return m ? m[1].trim() : null;
                        };
                        return JSON.stringify({
                            product: get('Product'),
                            amount: get('Order amount'),
                            url: location.href,
                        });
                    }
                """)
                self.orders_data.append({"order_id": order["order_id"], "detail": detail})
                await self.browser.close_page(new_tab)
            else:
                self.logger.warning(f"  未打开新 Tab: {order['order_id']}")
        await self.screenshot("details-done")

    def save_results(self, output_path: str = "output.json"):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.orders_data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"数据已保存: {output_path}")

    async def run(self, status: str = "Pending"):
        await self.setup_run("order-scraper")
        self.logger.info("任务开始")
        try:
            await self.step1_login()
            await self.step2_filter(status)
            orders = await self.step3_collect_orders()
            if orders:
                await self.step4_extract_details(orders)
            self.save_results()
            self.logger.info("任务完成")
        except Exception as e:
            self.logger.error(f"任务失败: {e}")
            await self.screenshot("error")
            raise
        finally:
            self.logger.info(f"日志已保存至 {self.run_dir}")
            await self.browser.kill()


if __name__ == "__main__":
    asyncio.run(OrderScraperAgent(headless=False).run())
