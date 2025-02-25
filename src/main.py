#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
资讯爬虫主程序
主要功能：从指定网站获取实时资讯，并保存到每日CSV文件中
"""

import os
import time
import asyncio
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

import schedule
from loguru import logger
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

from selectors import Selectors
from utils import get_data_file_path, save_to_csv, get_random_user_agent, deduplicate_news_data

# 配置日志
log_path = Path(__file__).parent.parent / "logs"
log_path.mkdir(exist_ok=True)
logger.add(
    log_path / "crawler_{time}.log",
    rotation="1 day",
    retention="7 days",
    level="INFO",
    encoding="utf-8",
)


class NewsCrawler:
    """资讯爬虫类"""

    def __init__(self, url: str = "https://newsnow.busiyi.world/c/hottest"):
        """初始化爬虫

        Args:
            url: 目标网站URL
        """
        self.url = url
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.selectors = Selectors()

    async def setup(self) -> None:
        """设置浏览器环境"""
        logger.info("正在初始化浏览器...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=get_random_user_agent(),
        )
        self.page = await self.context.new_page()
        
        # 设置超时
        self.page.set_default_timeout(30000)
        
        # 添加额外headers
        await self.context.set_extra_http_headers({
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        })
        
        logger.info("浏览器初始化完成")

    async def navigate_to_page(self) -> None:
        """导航到目标页面"""
        logger.info(f"正在访问页面: {self.url}")
        
        try:
            # 设置页面加载超时时间
            await self.page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待页面主要内容加载完成
            await self.page.wait_for_load_state("networkidle", timeout=60000)
            
            # 等待重要元素出现
            try:
                await self.page.wait_for_selector(".news-item", timeout=10000)
                logger.info("页面关键元素已加载")
            except Exception as e:
                logger.warning(f"等待关键元素超时: {e}")
                # 尝试截图保存当前页面状态
                await self.page.screenshot(path=log_path / f"page_state_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            logger.info("页面加载完成")
        except Exception as e:
            logger.error(f"页面导航失败: {e}")
            await self.page.screenshot(path=log_path / f"navigation_failed_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            raise

    async def scroll_to_bottom(self) -> None:
        """滚动到页面底部以加载更多内容"""
        logger.info("正在滚动页面以加载更多内容...")
        
        # 获取初始高度
        prev_height = await self.page.evaluate("document.body.scrollHeight")
        
        # 最大滚动尝试次数
        max_scroll_attempts = 10
        scroll_attempts = 0
        
        while scroll_attempts < max_scroll_attempts:
            # 滚动到底部
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            # 等待加载
            await self.page.wait_for_timeout(2000)
            
            # 检查是否有"加载更多"按钮并点击
            try:
                load_more_button = await self.page.query_selector(self.selectors.LOAD_MORE_BUTTON)
                if load_more_button:
                    await load_more_button.click()
                    await self.page.wait_for_timeout(2000)
                    logger.info("点击了'加载更多'按钮")
            except Exception as e:
                logger.debug(f"没有找到或无法点击'加载更多'按钮: {e}")
            
            # 获取新高度
            new_height = await self.page.evaluate("document.body.scrollHeight")
            
            # 如果高度没有变化，尝试再滚动几次或跳出循环
            if new_height == prev_height:
                scroll_attempts += 1
            else:
                scroll_attempts = 0  # 重置尝试次数
                
            prev_height = new_height
            
        logger.info("页面滚动完成")

    async def extract_news(self) -> List[Dict[str, Any]]:
        """提取新闻数据

        Returns:
            List[Dict[str, Any]]: 提取的新闻列表，每条包含标题和时间
        """
        logger.info("开始提取新闻数据...")
        
        # 等待新闻列表容器
        try:
            await self.page.wait_for_selector(".news-list, .article-list, .feed-list", timeout=10000)
        except Exception as e:
            logger.error(f"无法找到新闻列表容器: {e}")
            await self.page.screenshot(path=log_path / f"no_news_list_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            # 尝试获取页面内容以便调试
            page_content = await self.page.content()
            with open(log_path / f"page_content_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                f.write(page_content)
            return []
        
        # 使用JavaScript提取所有新闻项，更可靠的方式
        news_items = await self.page.evaluate("""
        () => {
            // 尝试多种可能的选择器
            const selectors = ['.news-item', '.article-item', '.feed-item', '.post-item'];
            let items = [];
            
            // 尝试每个选择器
            for (const selector of selectors) {
                const elements = document.querySelectorAll(selector);
                if (elements.length > 0) {
                    items = Array.from(elements);
                    break;
                }
            }
            
            // 如果没有找到任何元素，尝试更一般的方法
            if (items.length === 0) {
                // 查找所有可能包含新闻的列表项
                const possibleItems = document.querySelectorAll('div[class*="news"], div[class*="article"], div[class*="post"], div[class*="item"]');
                items = Array.from(possibleItems);
            }
            
            return items.map(item => {
                // 尝试多种可能的标题选择器
                const titleSelectors = ['h2', 'h3', '.title', '[class*="title"]', 'a', 'p'];
                let title = '';
                
                for (const selector of titleSelectors) {
                    const titleElem = item.querySelector(selector);
                    if (titleElem && titleElem.textContent.trim()) {
                        title = titleElem.textContent.trim();
                        break;
                    }
                }
                
                // 尝试获取链接
                let link = '';
                const linkElem = item.querySelector('a');
                if (linkElem) {
                    link = linkElem.href;
                }
                
                // 尝试获取来源
                let source = '';
                const sourceSelectors = ['.source', '[class*="source"]', '.author', '[class*="author"]', '.publisher', '[class*="publisher"]'];
                
                for (const selector of sourceSelectors) {
                    const sourceElem = item.querySelector(selector);
                    if (sourceElem && sourceElem.textContent.trim()) {
                        source = sourceElem.textContent.trim();
                        break;
                    }
                }
                
                return {
                    title: title || '无标题',
                    link: link || '',
                    source: source || '未知来源'
                };
            }).filter(item => item.title !== '无标题'); // 过滤掉没有标题的项
        }
        """)
        
        results = []
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for item in news_items:
            try:
                results.append({
                    "title": item.get("title", "无标题").strip(),
                    "source": item.get("source", "未知来源").strip(),
                    "link": item.get("link", "").strip(),
                    "collect_time": current_time
                })
            except Exception as e:
                logger.error(f"处理新闻项时出错: {e}")
        
        # 去重
        results = deduplicate_news_data(results)
        
        logger.info(f"成功提取 {len(results)} 条新闻")
        return results

    def save_to_csv(self, news_data: List[Dict[str, Any]]) -> None:
        """保存数据到CSV文件

        Args:
            news_data: 新闻数据列表
        """
        if not news_data:
            logger.warning("没有数据可保存")
            return
            
        # 获取当前日期对应的文件路径
        file_path = get_data_file_path()
        
        # 保存数据
        save_to_csv(news_data, file_path)

    async def close(self) -> None:
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            logger.info("浏览器已关闭")

    async def run(self) -> None:
        """运行爬虫流程"""
        start_time = time.time()
        logger.info("开始爬取任务")
        
        try:
            await self.setup()
            await self.navigate_to_page()
            await self.scroll_to_bottom()
            news_data = await self.extract_news()
            self.save_to_csv(news_data)
            
            # 记录任务完成情况
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"任务完成，耗时: {duration:.2f}秒，获取数据: {len(news_data)} 条")
            
        except Exception as e:
            logger.error(f"爬虫运行出错: {e}")
            
            # 如果页面已加载，尝试保存页面状态以便调试
            if self.page:
                try:
                    await self.page.screenshot(path=log_path / f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    page_content = await self.page.content()
                    with open(log_path / f"error_content_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                        f.write(page_content)
                except Exception as screenshot_err:
                    logger.error(f"保存错误状态截图失败: {screenshot_err}")
        finally:
            await self.close()


async def main():
    """主函数"""
    logger.info("开始执行爬虫任务")
    crawler = NewsCrawler()
    await crawler.run()
    logger.info("爬虫任务执行完成")


def scheduled_task():
    """定时任务"""
    asyncio.run(main())


if __name__ == "__main__":
    # 设置定时任务，每5分钟执行一次
    schedule.every(5).minutes.do(scheduled_task)
    
    # 立即执行一次
    scheduled_task()
    
    # 持续运行定时任务
    logger.info("爬虫已启动，每5分钟执行一次")
    while True:
        schedule.run_pending()
        time.sleep(1)