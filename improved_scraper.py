#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
改进的爬虫示例
根据实际网站结构优化了选择器
"""

import os
import csv
import time
import asyncio
import datetime
from pathlib import Path

from playwright.async_api import async_playwright


async def run_scraper():
    """
    运行爬虫
    """
    # 当前日期（用于文件名）
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 创建数据目录
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 创建截图目录
    screenshots_dir = Path("screenshots")
    screenshots_dir.mkdir(exist_ok=True)
    
    # CSV文件路径
    csv_path = data_dir / f"news_{today}.csv"
    
    # 目标URL
    url = "https://newsnow.busiyi.world/c/hottest"
    
    print(f"正在开始爬取：{url}")
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)  # 设置为False以便可以看到浏览器操作
        page = await browser.new_page()
        
        try:
            # 访问页面
            print("正在访问页面...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 等待加载
            print("等待页面加载...")
            await page.wait_for_load_state("networkidle", timeout=60000)
            
            # 滚动页面以加载更多内容
            print("滚动页面加载更多内容...")
            for _ in range(5):  # 增加滚动次数
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(3000)  # 增加等待时间
            
            # 截图保存当前页面状态
            screenshot_path = screenshots_dir / f"page_state_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_path)
            print(f"页面截图保存至：{screenshot_path}")
            
            # 提取新闻标题和链接 - 使用更精确的选择器
            print("提取新闻数据...")
            news_data = await page.evaluate("""
            () => {
                const results = [];
                const currentTime = new Date().toISOString();
                
                // 查找所有卡片元素
                const cards = document.querySelectorAll('.card, .article-card, .news-card, article, .item');
                
                if (cards.length > 0) {
                    console.log("找到 " + cards.length + " 个卡片元素");
                    
                    for (const card of cards) {
                        // 获取标题
                        let title = '';
                        const titleElement = card.querySelector('h2, h3, h4, .title, [class*="title"], a');
                        if (titleElement) {
                            title = titleElement.textContent.trim();
                        }
                        
                        // 获取链接
                        let link = '';
                        const linkElement = card.querySelector('a');
                        if (linkElement && linkElement.href) {
                            link = linkElement.href;
                        }
                        
                        // 获取来源
                        let source = '';
                        const sourceElement = card.querySelector('.source, [class*="source"], .author, [class*="author"], .publisher');
                        if (sourceElement) {
                            source = sourceElement.textContent.trim();
                        }
                        
                        // 只有当标题不为空时才添加
                        if (title) {
                            results.push({
                                title: title,
                                link: link,
                                source: source || '未知来源'
                            });
                        }
                    }
                } else {
                    // 如果找不到卡片元素，尝试查找所有可能的链接
                    console.log("未找到卡片元素，尝试查找链接...");
                    const links = document.querySelectorAll('a');
                    
                    for (const link of links) {
                        // 过滤掉导航链接和空链接
                        if (link.textContent.trim() && 
                            !link.href.includes('#') && 
                            link.textContent.length > 10 &&
                            !link.href.includes('javascript:')) {
                            
                            results.push({
                                title: link.textContent.trim(),
                                link: link.href,
                                source: '未知来源'
                            });
                        }
                    }
                }
                
                // 去重，以标题为键
                const uniqueResults = [];
                const seenTitles = new Set();
                
                for (const item of results) {
                    if (!seenTitles.has(item.title)) {
                        seenTitles.add(item.title);
                        uniqueResults.push(item);
                    }
                }
                
                console.log("找到 " + uniqueResults.length + " 条唯一新闻");
                return uniqueResults;
            }
            """)
            
            # 保存数据到CSV
            if news_data:
                # 添加当前时间
                current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for item in news_data:
                    item["collect_time"] = current_time
                
                # 写入CSV
                file_exists = csv_path.exists()
                with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                    fieldnames = ['title', 'source', 'link', 'collect_time']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    
                    if not file_exists:
                        writer.writeheader()
                    
                    writer.writerows(news_data)
                
                print(f"成功保存 {len(news_data)} 条新闻到 {csv_path}")
            else:
                print("未找到新闻数据")
            
            # 保存页面HTML以供分析
            html_content = await page.content()
            html_path = data_dir / f"page_content_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"页面HTML保存至：{html_path}")
            
        except Exception as e:
            print(f"爬取过程中出错: {e}")
            
            # 如果出错，尝试保存页面状态
            try:
                await page.screenshot(path=screenshots_dir / f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            except:
                pass
        
        finally:
            # 关闭浏览器
            await browser.close()
            print("浏览器已关闭")


if __name__ == "__main__":
    # 运行爬虫
    print("开始执行爬虫...")
    asyncio.run(run_scraper())
    print("爬虫执行完成!")