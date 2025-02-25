import os
import csv
import time
import datetime
import asyncio
from playwright.async_api import async_playwright
import logging
from pathlib import Path
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_text(text):
    """清理文本，去除多余的空格和换行符"""
    if not text:
        return ""
    # 替换所有空白字符为单个空格
    text = re.sub(r'\s+', ' ', text.strip())
    return text

async def run_scraper():
    """爬取新闻数据"""
    # 创建必要的目录
    data_dir = Path("data")
    screenshots_dir = Path("screenshots")
    data_dir.mkdir(exist_ok=True)
    screenshots_dir.mkdir(exist_ok=True)
    
    # 获取当前日期
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # CSV文件路径
    csv_path = data_dir / f"enhanced_news_{current_date}.csv"
    
    # 检查CSV文件是否存在
    is_new_file = not csv_path.exists()
    
    # 当前时间
    collect_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    async with async_playwright() as p:
        try:
            logger.info("开始新闻爬取流程")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(viewport={"width": 1920, "height": 1080})
            page = await context.new_page()
            
            # 访问目标网站
            url = "https://newsnow.busiyi.world/c/hottest"
            logger.info(f"访问URL: {url}")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 等待页面加载完成
            await page.wait_for_load_state("networkidle")
            logger.info("页面加载完成")
            
            # 滚动页面加载更多内容
            logger.info("滚动页面加载更多内容")
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(1000)
                
            # 再滚动一次确保加载完全
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3000)  # 增加等待时间
            
            # 截图保存当前页面状态
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            screenshot_path = screenshots_dir / f"page_state_{timestamp}.png"
            await page.screenshot(path=screenshot_path)
            logger.info(f"页面截图保存至：{screenshot_path}")
            
            # 保存HTML内容
            html_path = data_dir / f"page_content_{timestamp}.html"
            html_content = await page.content()
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"HTML内容保存至：{html_path}")
            
            # 提取新闻标题和链接 - 使用更精确的选择器
            logger.info("提取新闻数据...")
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
                # 准备数据
                formatted_data = []
                for idx, item in enumerate(news_data, 1):
                    # 分离标题中可能包含的序号
                    title = item['title']
                    # 清理标题前的数字
                    match = re.match(r'^(\d+)[.、\s]*(.+)$', title)
                    if match:
                        number = match.group(1)
                        cleaned_title = match.group(2)
                    else:
                        number = str(idx)
                        cleaned_title = title
                    
                    # 清理文本字段
                    cleaned_title = clean_text(cleaned_title)
                    source = clean_text(item['source'])
                    link = item['link']
                    
                    # 格式化数据
                    formatted_data.append({
                        'number': number,
                        'title': cleaned_title,
                        'source': source or '未知来源',
                        'link': link,
                        'collect_time': collect_time
                    })
                
                # 写入CSV
                with open(csv_path, 'a', newline='', encoding='utf-8-sig') as f:
                    fieldnames = ['number', 'title', 'source', 'link', 'collect_time']
                    writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
                    
                    # 如果是新文件，写入表头
                    if is_new_file:
                        writer.writeheader()
                    
                    # 写入数据
                    writer.writerows(formatted_data)
                
                logger.info(f"成功保存 {len(formatted_data)} 条新闻数据到: {csv_path}")
            else:
                logger.warning("未找到新闻数据，请检查网页结构是否改变")
            
            # 关闭浏览器
            await browser.close()
            logger.info("浏览器已关闭")
            
            return len(news_data) if news_data else 0
            
        except Exception as e:
            logger.error(f"爬取过程中发生错误: {str(e)}")
            # 尝试截图保存错误状态
            try:
                error_screenshot_path = screenshots_dir / f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                await page.screenshot(path=error_screenshot_path)
                logger.info(f"错误状态截图保存至: {error_screenshot_path}")
            except:
                logger.error("无法保存错误状态截图")
            
            # 关闭浏览器
            try:
                await browser.close()
            except:
                pass
            
            return 0

async def main():
    logger.info("爬虫程序启动")
    news_count = await run_scraper()
    logger.info(f"爬虫程序结束，共爬取 {news_count} 条新闻")

if __name__ == "__main__":
    asyncio.run(main())