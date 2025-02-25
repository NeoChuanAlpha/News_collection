import os
import csv
import time
import datetime
import asyncio
import argparse
import pandas as pd
from playwright.async_api import async_playwright
import logging
from pathlib import Path
import re
import hashlib
import json
import glob
import shutil

# 配置日志
def setup_logger(log_level=logging.INFO):
    """设置日志记录器"""
    logger = logging.getLogger("news_crawler")
    logger.setLevel(log_level)
    
    # 防止重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建文件处理器
    log_file = log_dir / f"crawler_{datetime.datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def create_dirs():
    """创建必要的目录"""
    dirs = ["data", "screenshots", "logs", "html_cache"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    return {name: Path(name) for name in dirs}

def get_current_time():
    """获取当前时间，格式为YYYY-MM-DD HH:MM:SS"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_timestamp():
    """获取当前时间戳，格式为YYYYMMDD_HHMMSS"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def clean_text(text):
    """清理文本，去除多余的空格和换行符"""
    if not text:
        return ""
    # 替换所有空白字符为单个空格
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def extract_domain(url):
    """从URL中提取域名作为来源"""
    if not url:
        return "未知来源"
    
    try:
        # 尝试解析URL获取域名
        import urllib.parse
        domain = urllib.parse.urlparse(url).netloc
        
        # 提取主域名
        parts = domain.split('.')
        if len(parts) >= 2:
            if parts[-2] in ['com', 'net', 'org', 'gov', 'edu'] and len(parts) > 2:
                main_domain = parts[-3]
            else:
                main_domain = parts[-2]
                
            # 映射常见域名到更友好的名称
            domain_mapping = {
                'zhihu': '知乎',
                'weibo': '微博',
                'baidu': '百度',
                'douyin': '抖音',
                'toutiao': '今日头条',
                'bilibili': 'B站',
                'wallstreetcn': '华尔街见闻',
                'thepaper': '澎湃新闻',
                'github': 'GitHub',
                'coolapk': '酷安'
            }
            
            return domain_mapping.get(main_domain, domain)
    except:
        pass
    
    return "未知来源"

def generate_news_id(title, link):
    """生成新闻ID，用于去重"""
    if not title or not link:
        return None
    
    # 使用标题和链接生成唯一ID
    content = f"{title}{link}".encode("utf-8")
    return hashlib.md5(content).hexdigest()

def cleanup_cache_files(dirs, logger, max_files=100, keep_days=3):
    """清理缓存文件，保留最新的文件
    
    参数:
        dirs: 目录映射
        logger: 日志记录器
        max_files: 每个目录保留的最大文件数
        keep_days: 保留多少天以内的文件
    """
    logger.info("开始清理缓存文件...")
    
    # 计算截止日期
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=keep_days)
    
    # 需要清理的目录
    cache_dirs = ["screenshots", "html_cache", "logs"]
    
    for dir_name in cache_dirs:
        if dir_name not in dirs:
            continue
            
        dir_path = dirs[dir_name]
        logger.info(f"清理 {dir_name} 目录...")
        
        # 获取所有文件
        all_files = []
        for ext in ["*.*", "*.png", "*.html", "*.log", "*.json"]:
            all_files.extend(glob.glob(str(dir_path / ext)))
        
        # 如果文件数量少于最大值，不需要清理
        if len(all_files) <= max_files:
            logger.info(f"{dir_name} 目录文件数量 ({len(all_files)}) 未超过上限 ({max_files})，无需清理")
            continue
        
        # 获取文件信息
        file_info = []
        for file_path in all_files:
            try:
                file_stat = os.stat(file_path)
                file_date = datetime.datetime.fromtimestamp(file_stat.st_mtime)
                file_info.append((file_path, file_date))
            except Exception as e:
                logger.warning(f"获取文件信息出错: {file_path}, {str(e)}")
        
        # 按修改时间排序
        file_info.sort(key=lambda x: x[1], reverse=True)
        
        # 删除超过保留天数的文件和超过数量限制的文件
        deleted_count = 0
        for file_path, file_date in file_info:
            # 保留最近的文件
            if file_info.index((file_path, file_date)) < max_files and file_date > cutoff_date:
                continue
                
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception as e:
                logger.warning(f"删除文件出错: {file_path}, {str(e)}")
        
        logger.info(f"已清理 {dir_name} 目录中的 {deleted_count} 个文件")
    
    logger.info("缓存文件清理完成")

async def scrape_news(logger, dirs, save_mode="single", output_file=None, screenshot_enabled=True, save_html=True):
    """爬取新闻数据
    
    参数:
        logger: 日志记录器
        dirs: 目录映射
        save_mode: 保存模式，'single'（单次）或'continuous'（连续）
        output_file: 输出文件路径（仅在连续模式下使用）
        screenshot_enabled: 是否保存页面截图
        save_html: 是否保存HTML内容
    """
    # 获取当前日期和时间
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    timestamp = get_timestamp()
    
    # 设置输出文件
    if save_mode == "continuous" and output_file:
        csv_path = Path(output_file)
    else:
        # 单次模式下，使用时间戳生成唯一文件名
        csv_path = dirs["data"] / f"news_{current_date}_{timestamp}.csv"
    
    # 检查文件是否存在（用于判断是否需要写入表头）
    is_new_file = not csv_path.exists()
    
    # 读取现有数据（用于去重和确定起始序号）
    existing_ids = set()
    next_idx = 1  # 默认从1开始
    
    if not is_new_file and save_mode == "continuous":
        try:
            df_existing = pd.read_csv(csv_path, encoding="utf-8-sig")
            if "news_id" in df_existing.columns:
                existing_ids = set(df_existing["news_id"].dropna().tolist())
            
            # 确定下一个序号
            if "number" in df_existing.columns and not df_existing.empty:
                # 找到最大序号并加1
                next_idx = int(df_existing["number"].max()) + 1
            
            logger.info(f"读取到 {len(existing_ids)} 条现有记录用于去重")
        except Exception as e:
            logger.warning(f"读取现有数据失败: {str(e)}")
    
    # 当前采集时间
    collect_time = get_current_time()
    
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
            await page.wait_for_timeout(3000)
            
            # 截图保存当前页面状态
            if screenshot_enabled:
                screenshot_path = dirs["screenshots"] / f"page_state_{timestamp}.png"
                await page.screenshot(path=screenshot_path)
                logger.info(f"页面截图保存至：{screenshot_path}")
            
            # 保存HTML内容
            if save_html:
                html_path = dirs["html_cache"] / f"page_content_{timestamp}.html"
                html_content = await page.content()
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                logger.info(f"HTML内容保存至：{html_path}")
            
            # 提取新闻标题和链接
            logger.info("提取新闻数据...")
            news_data = await page.evaluate("""
            () => {
                const results = [];
                
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
                        
                        // 获取来源（尝试更多的选择器）
                        let source = '';
                        const sourceElement = card.querySelector('.source, [class*="source"], .author, [class*="author"], .publisher, .site, .domain, .hostname, [class*="hostname"], [class*="domain"], [class*="site"]');
                        if (sourceElement) {
                            source = sourceElement.textContent.trim();
                        }
                        
                        // 获取发布时间
                        let pubTime = '';
                        const timeElement = card.querySelector('time, .time, .date, [class*="time"], [class*="date"], [datetime]');
                        if (timeElement) {
                            if (timeElement.hasAttribute('datetime')) {
                                pubTime = timeElement.getAttribute('datetime');
                            } else {
                                pubTime = timeElement.textContent.trim();
                            }
                        }
                        
                        // 获取摘要/简介
                        let summary = '';
                        const summaryElement = card.querySelector('.summary, .description, .abstract, .content, [class*="summary"], [class*="description"], [class*="abstract"], [class*="content"]');
                        if (summaryElement && summaryElement !== titleElement) {
                            summary = summaryElement.textContent.trim();
                        }
                        
                        // 只有当标题不为空时才添加
                        if (title) {
                            results.push({
                                title: title,
                                link: link,
                                source: source || '',
                                pubTime: pubTime || '',
                                summary: summary || ''
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
                                source: '',
                                pubTime: '',
                                summary: ''
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
            
            # 处理数据并保存
            if news_data:
                # 准备数据
                formatted_data = []
                
                for item in news_data:
                    # 清理文本字段
                    title = clean_text(item['title'])
                    link = item['link']
                    
                    # 从标题中提取序号并移除
                    match = re.match(r'^(\d+)[.、\s]*(.+)$', title)
                    if match:
                        original_number = match.group(1)
                        cleaned_title = clean_text(match.group(2))
                    else:
                        original_number = ""
                        cleaned_title = title
                    
                    # 尝试获取有意义的来源
                    source = clean_text(item['source'])
                    if not source:
                        source = extract_domain(link)
                    
                    # 生成新闻ID用于去重
                    news_id = generate_news_id(cleaned_title, link)
                    
                    # 检查是否为重复新闻
                    if news_id in existing_ids:
                        continue
                    
                    # 格式化数据
                    formatted_data.append({
                        'number': next_idx,  # 使用连续的序号
                        'original_number': original_number,
                        'title': cleaned_title,
                        'source': source,
                        'link': link,
                        'summary': clean_text(item.get('summary', '')),
                        'pub_time': clean_text(item.get('pubTime', '')),
                        'collect_time': collect_time,
                        'news_id': news_id
                    })
                    
                    next_idx += 1  # 递增序号
                
                # 创建DataFrame
                df = pd.DataFrame(formatted_data)
                
                # 保存为CSV
                if is_new_file or save_mode == "single":
                    # 新文件或单次模式：写入表头
                    df.to_csv(
                        csv_path, 
                        index=False, 
                        encoding='utf-8-sig',
                        quoting=csv.QUOTE_ALL
                    )
                else:
                    # 增量模式：追加数据
                    df.to_csv(
                        csv_path, 
                        mode='a', 
                        index=False, 
                        encoding='utf-8-sig',
                        header=False,
                        quoting=csv.QUOTE_ALL
                    )
                
                # 生成摘要信息
                summary_info = {
                    "timestamp": collect_time,
                    "total_news": len(news_data),
                    "new_news": len(formatted_data),
                    "file_path": str(csv_path)
                }
                
                # 保存执行摘要
                summary_path = dirs["logs"] / f"summary_{timestamp}.json"
                with open(summary_path, "w", encoding="utf-8") as f:
                    json.dump(summary_info, f, ensure_ascii=False, indent=2)
                
                logger.info(f"成功保存 {len(formatted_data)} 条新闻数据到: {csv_path}")
                
                # 单次模式下，同时保存Excel格式以便查看
                if save_mode == "single":
                    excel_path = csv_path.with_suffix(".xlsx")
                    df.to_excel(excel_path, index=False, engine='openpyxl')
                    logger.info(f"成功保存Excel格式数据到: {excel_path}")
                
                # 返回爬取摘要
                return {
                    "success": True,
                    "news_count": len(formatted_data),
                    "file_path": str(csv_path)
                }
            else:
                logger.warning("未找到新闻数据，请检查网页结构是否改变")
                return {
                    "success": False,
                    "news_count": 0,
                    "file_path": None
                }
                
        except Exception as e:
            logger.error(f"爬取过程中发生错误: {str(e)}")
            # 尝试截图保存错误状态
            try:
                if screenshot_enabled:
                    error_screenshot_path = dirs["screenshots"] / f"error_{timestamp}.png"
                    await page.screenshot(path=error_screenshot_path)
                    logger.info(f"错误状态截图保存至: {error_screenshot_path}")
            except:
                logger.error("无法保存错误状态截图")
            
            # 关闭浏览器
            try:
                await browser.close()
            except:
                pass
            
            return {
                "success": False,
                "news_count": 0,
                "file_path": None,
                "error": str(e)
            }
        finally:
            # 确保浏览器关闭
            try:
                await browser.close()
                logger.info("浏览器已关闭")
            except:
                pass

async def run_continuous_mode(args, logger, dirs):
    """持续运行模式"""
    # 设置输出文件名
    if args.output:
        output_file = args.output
    else:
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        output_file = str(dirs["data"] / f"continuous_news_{current_date}.csv")
    
    logger.info(f"启动持续采集模式，数据将保存至: {output_file}")
    logger.info(f"采集间隔: {args.interval} 分钟")
    
    # 缓存和截图设置
    screenshot_enabled = not args.no_screenshots
    save_html = not args.no_html_cache
    
    # 自动清理频率（每N次采集执行一次清理）
    cleanup_frequency = 10
    
    cycle_count = 0
    try:
        while True:
            cycle_count += 1
            start_time = time.time()
            
            logger.info(f"开始第 {cycle_count} 次采集")
            
            # 定期清理缓存文件
            if cycle_count % cleanup_frequency == 0:
                cleanup_cache_files(dirs, logger, max_files=args.max_cache_files, keep_days=args.cache_days)
            
            result = await scrape_news(
                logger=logger,
                dirs=dirs,
                save_mode="continuous",
                output_file=output_file,
                screenshot_enabled=screenshot_enabled,
                save_html=save_html
            )
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            logger.info(f"第 {cycle_count} 次采集完成，耗时: {elapsed_time:.2f} 秒")
            
            if result["success"]:
                logger.info(f"成功采集 {result['news_count']} 条新新闻")
            else:
                logger.warning("本次采集未获取到新数据")
            
            # 计算下一次执行的等待时间
            wait_time = max(1, args.interval * 60 - elapsed_time)
            next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=wait_time)
            logger.info(f"等待 {wait_time:.2f} 秒后开始下一次采集，预计时间: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            await asyncio.sleep(wait_time)
    
    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    except Exception as e:
        logger.error(f"持续模式运行时发生错误: {str(e)}")

async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="新闻爬虫")
    parser.add_argument(
        "--mode", 
        type=str, 
        choices=["single", "continuous"], 
        default="single",
        help="运行模式：single（单次运行）或continuous（持续运行）"
    )
    parser.add_argument(
        "--interval", 
        type=float, 
        default=5.0,
        help="连续模式下的运行间隔，单位分钟（默认：5分钟）"
    )
    parser.add_argument(
        "--output", 
        type=str,
        help="连续模式下的输出文件路径"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="启用调试日志"
    )
    parser.add_argument(
        "--no-screenshots", 
        action="store_true",
        help="禁用页面截图功能"
    )
    parser.add_argument(
        "--no-html-cache", 
        action="store_true",
        help="禁用HTML缓存功能"
    )
    parser.add_argument(
        "--max-cache-files", 
        type=int,
        default=100,
        help="每种缓存类型保留的最大文件数（默认：100）"
    )
    parser.add_argument(
        "--cache-days", 
        type=int,
        default=3,
        help="缓存文件保留天数（默认：3天）"
    )
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    logger = setup_logger(log_level)
    logger.info("爬虫程序启动")
    
    # 创建必要目录
    dirs = create_dirs()
    
    try:
        if args.mode == "continuous":
            await run_continuous_mode(args, logger, dirs)
        else:
            logger.info("执行单次采集模式")
            result = await scrape_news(
                logger=logger,
                dirs=dirs,
                save_mode="single",
                screenshot_enabled=not args.no_screenshots,
                save_html=not args.no_html_cache
            )
            
            if result["success"]:
                logger.info(f"采集完成，共获取 {result['news_count']} 条新闻")
                logger.info(f"数据已保存至: {result['file_path']}")
            else:
                logger.error("采集失败，未获取到数据")
    
    except Exception as e:
        logger.error(f"程序运行时发生错误: {str(e)}")
    
    finally:
        logger.info("爬虫程序结束")

if __name__ == "__main__":
    asyncio.run(main())