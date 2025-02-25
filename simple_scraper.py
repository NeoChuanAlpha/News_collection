#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
简单爬虫示例
展示如何使用Playwright访问指定网站并获取基础数据
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
            for _ in range(3):  # 滚动3次
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)  # 等待2秒加载
            
            # 截图保存当前页面状态
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            await page.screenshot(path=screenshots_dir / f"page_state_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            
            # 提取新闻标题和链接
            print("提取新闻数据...")
            news_data = await page.evaluate("""
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
            with open(data_dir / f"page_content_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            
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