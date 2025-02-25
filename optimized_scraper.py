import os
import csv
import time
import datetime
from playwright.sync_api import sync_playwright
import logging
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_dir(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

def get_current_date():
    """获取当前日期，格式为YYYY-MM-DD"""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def timestamp():
    """生成当前时间戳，格式为YYYYMMDD_HHMMSS"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def clean_text(text):
    """清理文本，去除多余空格和换行符"""
    if text:
        # 删除多余空格和换行符
        text = re.sub(r'\s+', ' ', text.strip())
        return text
    return ""

def extract_news_number(title):
    """从标题中提取新闻序号"""
    match = re.match(r'^(\d+)', title)
    if match:
        return match.group(1)
    return ""

def scrape_news():
    """爬取新闻数据"""
    # 创建必要的目录
    data_dir = os.path.join(os.getcwd(), 'data')
    screenshots_dir = os.path.join(os.getcwd(), 'screenshots')
    ensure_dir(data_dir)
    ensure_dir(screenshots_dir)
    
    # CSV文件路径
    csv_filename = os.path.join(data_dir, f'news_{get_current_date()}.csv')
    
    # 检查CSV文件是否已存在
    file_exists = os.path.exists(csv_filename)
    
    # 当前时间作为采集时间
    collect_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with sync_playwright() as p:
        try:
            logger.info("开始爬取流程")
            
            # 启动浏览器
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = context.new_page()
            
            # 访问目标网页
            url = "https://newsnow.busiyi.world/c/hottest"
            logger.info(f"正在访问: {url}")
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 等待页面加载完成
            page.wait_for_load_state("networkidle")
            logger.info("页面加载完成")
            
            # 滚动页面以加载更多内容
            logger.info("滚动页面以加载更多内容")
            for _ in range(5):  # 滚动5次
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(1)
            
            # 保存页面截图
            screenshot_path = os.path.join(screenshots_dir, f'page_state_{timestamp()}.png')
            page.screenshot(path=screenshot_path)
            logger.info(f"页面截图已保存至: {screenshot_path}")
            
            # 保存页面HTML
            html_path = os.path.join(data_dir, f'page_content_{timestamp()}.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(page.content())
            logger.info(f"页面HTML已保存至: {html_path}")
            
            # 提取新闻数据
            news_items = []
            
            # 使用CSS选择器选择新闻块
            news_elements = page.query_selector_all(".flex.flex-col.items-start.w-full")
            logger.info(f"找到 {len(news_elements)} 个可能的新闻元素")
            
            for news_el in news_elements:
                title_el = news_el.query_selector("a.line-clamp-2")
                if title_el:
                    title = title_el.inner_text()
                    link = title_el.get_attribute("href")
                    
                    # 获取来源元素
                    source_el = news_el.query_selector(".text-sm.text-black/30")
                    source = source_el.inner_text() if source_el else "未知来源"
                    
                    # 提取序号
                    number = extract_news_number(title)
                    
                    # 清理文本
                    title = clean_text(title)
                    source = clean_text(source)
                    
                    # 如果链接不是以http开头，则补全
                    if link and not link.startswith(('http://', 'https://')):
                        link = f"https://newsnow.busiyi.world{link}"
                    
                    if title and link:
                        news_items.append({
                            'number': number,
                            'title': title,
                            'source': source,
                            'link': link,
                            'collect_time': collect_time
                        })
            
            logger.info(f"成功提取 {len(news_items)} 条新闻数据")
            
            # 写入CSV文件
            with open(csv_filename, 'a', newline='', encoding='utf-8') as f:
                fieldnames = ['number', 'title', 'source', 'link', 'collect_time']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                # 如果文件不存在，写入表头
                if not file_exists:
                    writer.writeheader()
                
                # 写入数据
                writer.writerows(news_items)
            
            logger.info(f"数据已保存至: {csv_filename}")
            
            # 关闭浏览器
            browser.close()
            logger.info("浏览器已关闭")
            
            return len(news_items)
        
        except Exception as e:
            logger.error(f"爬取过程中发生错误: {str(e)}")
            # 在发生错误时创建错误截图
            try:
                error_screenshot_path = os.path.join(screenshots_dir, f'error_{timestamp()}.png')
                page.screenshot(path=error_screenshot_path)
                logger.info(f"错误截图已保存至: {error_screenshot_path}")
            except:
                logger.error("无法保存错误截图")
            
            # 关闭浏览器
            try:
                browser.close()
                logger.info("浏览器已关闭")
            except:
                pass
            
            return 0

if __name__ == "__main__":
    logger.info("开始执行爬虫")
    news_count = scrape_news()
    logger.info(f"爬虫执行完毕，共爬取 {news_count} 条新闻")