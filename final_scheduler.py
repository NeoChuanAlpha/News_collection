import os
import time
import datetime
import logging
import asyncio
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 导入爬虫模块
try:
    from final_scraper import run_scraper
except ImportError:
    print("未找到爬虫模块，请确保final_scraper.py存在于当前目录")
    sys.exit(1)

# 配置日志
def setup_logger():
    """设置日志系统"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger("scheduler")
    logger.setLevel(logging.INFO)
    
    # 防止日志重复
    if logger.handlers:
        return logger
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器
    log_file = log_dir / "scheduler.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # 添加处理器到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

async def main():
    """主函数"""
    logger = setup_logger()
    logger.info("调度器启动")
    
    # 设置间隔时间（分钟）
    interval_minutes = 5
    interval_seconds = interval_minutes * 60
    
    # 计数器
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            start_time = time.time()
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            logger.info(f"开始第 {cycle_count} 个爬取周期，当前时间: {current_time}")
            
            try:
                # 运行爬虫
                news_count = await run_scraper()
                
                # 记录结果
                end_time = time.time()
                duration = end_time - start_time
                
                if news_count > 0:
                    logger.info(f"爬取成功，获取了 {news_count} 条新闻，耗时: {duration:.2f}秒")
                else:
                    logger.warning(f"爬取完成，但未获取到新闻数据，耗时: {duration:.2f}秒")
            
            except Exception as e:
                logger.error(f"爬虫执行过程中发生错误: {str(e)}")
            
            # 计算下一次运行的等待时间
            elapsed_time = time.time() - start_time
            wait_time = max(1, interval_seconds - elapsed_time)  # 至少等待1秒
            
            next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=wait_time)
            logger.info(f"等待 {wait_time:.2f} 秒后开始下一周期，预计时间: {next_run_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 等待到下一个周期
            await asyncio.sleep(wait_time)
    
    except KeyboardInterrupt:
        logger.info("用户中断，调度器停止")
    
    except Exception as e:
        logger.error(f"调度器运行时发生错误: {str(e)}")
    
    finally:
        logger.info("调度器已停止")

if __name__ == "__main__":
    asyncio.run(main())