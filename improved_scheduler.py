import os
import time
import datetime
import logging
import subprocess
import sys
from logging.handlers import RotatingFileHandler

# 配置日志
def setup_logger():
    """设置日志记录器"""
    # 创建日志目录
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 创建日志记录器
    logger = logging.getLogger("scheduler")
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 创建文件处理器（按大小轮换）
    log_file = os.path.join(log_dir, 'scheduler.log')
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8'
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

def run_scraper(logger):
    """运行爬虫脚本"""
    try:
        logger.info("开始执行爬虫任务")
        start_time = time.time()
        
        # 执行爬虫脚本
        script_path = os.path.join(os.getcwd(), 'optimized_scraper.py')
        process = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # 记录输出
        if process.stdout:
            logger.info(f"爬虫输出: {process.stdout}")
        if process.stderr:
            logger.warning(f"爬虫错误输出: {process.stderr}")
        
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"爬虫任务完成，耗时: {execution_time:.2f}秒")
        
        return True
    
    except subprocess.CalledProcessError as e:
        logger.error(f"爬虫脚本执行失败: {str(e)}")
        if e.stdout:
            logger.error(f"输出: {e.stdout}")
        if e.stderr:
            logger.error(f"错误: {e.stderr}")
        return False
    
    except Exception as e:
        logger.error(f"运行爬虫时发生错误: {str(e)}")
        return False

def main():
    """主函数"""
    logger = setup_logger()
    logger.info("调度器启动")
    
    # 间隔时间（分钟）
    interval_minutes = 5
    interval_seconds = interval_minutes * 60
    
    # 计数器
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.info(f"开始第 {cycle_count} 个爬取周期")
            
            # 运行爬虫
            success = run_scraper(logger)
            
            # 记录当前时间
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if success:
                logger.info(f"第 {cycle_count} 个爬取周期成功完成于 {current_time}")
            else:
                logger.warning(f"第 {cycle_count} 个爬取周期失败于 {current_time}")
            
            # 等待到下一个周期
            logger.info(f"等待 {interval_minutes} 分钟后开始下一周期...")
            time.sleep(interval_seconds)
    
    except KeyboardInterrupt:
        logger.info("用户中断，调度器停止")
    
    except Exception as e:
        logger.error(f"调度器运行时发生错误: {str(e)}")
    
    finally:
        logger.info("调度器已停止")

if __name__ == "__main__":
    main()