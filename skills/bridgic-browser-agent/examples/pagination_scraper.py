"""
循环翻页抓取示例

适用：需要遍历多页数据的任务（分页按钮 / URL 分页）。
"""

import asyncio
import json
import os

from bridgic.browser.tools import ToolPreset
from base_class import BrowserAgentBase


class PaginationScraper(BrowserAgentBase):

    TOOL_PRESET = ToolPreset.SCRAPING
    TARGET_URL = os.environ.get("TARGET_URL", "https://example.com/list")

    def __init__(self, headless: bool = False):
        super().__init__(headless=headless)
        self.all_items = []

    async def extract_current_page(self) -> list:
        """从当前页提取数据，子类按需覆盖。"""
        tree = await self.snapshot(interactive=False)
        # 示例：用 LLM 或 regex 从全量树提取数据
        # 实际使用时替换为具体提取逻辑
        return []

    async def scrape_all_pages(self):
        self.logger.info("Step: 开始翻页抓取")
        await self.execute_tool("navigate_to_url", url=self.TARGET_URL)
        await self.browser.page.wait_for_load_state("networkidle")

        page_num = 1
        while True:
            self.logger.info(f"  抓取第 {page_num} 页")
            items = await self.extract_current_page()
            self.all_items.extend(items)
            self.logger.info(f"  当前页 {len(items)} 条，累计 {len(self.all_items)} 条")
            await self.screenshot(f"page-{page_num:03d}")

            # 查找下一页按钮（优先标签定位）
            tree = await self.snapshot(interactive=True)
            next_ref = (
                self.find_ref_near_label(tree, "下一页", role="button")
                or self.find_ref_near_label(tree, "Next", role="button")
                or self.find_ref_near_label(tree, ">")
            )
            if not next_ref:
                self.logger.info("  无更多页面，抓取完成")
                break

            await self.execute_tool("click_element_by_ref", ref=next_ref)
            await self.browser.page.wait_for_load_state("networkidle")
            page_num += 1

    def save_results(self, output_path: str = "scraped.json"):
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.all_items, f, ensure_ascii=False, indent=2)
        self.logger.info(f"数据已保存: {output_path}，共 {len(self.all_items)} 条")

    async def run(self):
        await self.setup_run("pagination-scraper")
        self.logger.info("任务开始")
        try:
            await self.scrape_all_pages()
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
    asyncio.run(PaginationScraper(headless=False).run())
