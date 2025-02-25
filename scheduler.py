#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫调度器
定时执行爬虫任务
"""

import time
import subprocess
import datetime
import sys
from pathlib import Path


def run_scraper():
    """
    运行爬虫
    """
    print(f"[{datetime.datetime.now()}] 开始执行爬虫任务...")
    
    # 获取Python解释器路径
    python_exe = sys.executable
    
    # 运行爬虫脚本
    try:
        process = subprocess.run(
            [python_exe, "simple_scraper.py"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[{datetime.datetime.now()}] 爬虫输出: {process.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.datetime.now()}] 爬虫执行失败: {e}")
        print(f"错误输出: {e.stderr}")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] 执行过程中出错: {e}")
    
    print(f"[{datetime.datetime.now()}] 爬虫任务执行结束")


def main():
    """
    主函数
    """
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 设置日志文件
    log_file = log_dir / f"scheduler_{datetime.datetime.now().strftime('%Y%m%d')}.log"
    
    # 重定向输出到日志文件
    sys.stdout = open(log_file, "a", encoding="utf-8")
    sys.stderr = sys.stdout
    
    print(f"\n[{datetime.datetime.now()}] 调度器启动")
    
    try:
        # 立即执行一次
        run_scraper()
        
        # 设置执行间隔（秒）
        interval = 5 * 60  # 5分钟
        
        # 持续执行
        while True:
            print(f"[{datetime.datetime.now()}] 等待 {interval} 秒后再次执行...")
            time.sleep(interval)
            run_scraper()
            
    except KeyboardInterrupt:
        print(f"[{datetime.datetime.now()}] 调度器被用户中断")
    except Exception as e:
        print(f"[{datetime.datetime.now()}] 调度器出错: {e}")
    finally:
        print(f"[{datetime.datetime.now()}] 调度器关闭")
        # 恢复标准输出
        sys.stdout.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


if __name__ == "__main__":
    main()