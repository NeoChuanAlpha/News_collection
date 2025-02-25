#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具模块
提供辅助功能
"""

import os
import csv
import json
import random
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

import pandas as pd
from loguru import logger


def get_data_file_path(date_str: Optional[str] = None) -> Path:
    """获取数据文件路径
    
    Args:
        date_str: 日期字符串，格式为YYYY-MM-DD，默认为当天
        
    Returns:
        Path: 数据文件路径
    """
    if date_str is None:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    return data_dir / f"news_{date_str}.csv"


def save_to_csv(data: List[Dict[str, Any]], file_path: Path) -> None:
    """保存数据到CSV文件
    
    Args:
        data: 要保存的数据列表
        file_path: CSV文件路径
    """
    if not data:
        logger.warning("没有数据可保存")
        return
        
    # 检查文件是否存在，决定是否写入表头
    file_exists = file_path.exists()
    
    try:
        with open(file_path, mode="a", newline="", encoding="utf-8") as f:
            fieldnames = list(data[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # 如果文件不存在，写入表头
            if not file_exists:
                writer.writeheader()
                
            # 写入数据
            writer.writerows(data)
            
        logger.info(f"成功将 {len(data)} 条数据保存到 {file_path}")
    except Exception as e:
        logger.error(f"保存数据时出错: {e}")


def read_csv_to_dataframe(file_path: Path) -> pd.DataFrame:
    """读取CSV文件到DataFrame
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        pd.DataFrame: 数据DataFrame
    """
    if not file_path.exists():
        logger.warning(f"文件不存在: {file_path}")
        return pd.DataFrame()
        
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
        logger.info(f"成功从 {file_path} 读取 {len(df)} 条数据")
        return df
    except Exception as e:
        logger.error(f"读取CSV文件时出错: {e}")
        return pd.DataFrame()


def get_random_user_agent() -> str:
    """获取随机User-Agent
    
    Returns:
        str: 随机User-Agent字符串
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    ]
    return random.choice(user_agents)


def deduplicate_news_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """去重新闻数据
    
    Args:
        data: 新闻数据列表
        
    Returns:
        List[Dict[str, Any]]: 去重后的数据列表
    """
    unique_titles = set()
    deduplicated_data = []
    
    for item in data:
        if item["title"] not in unique_titles:
            unique_titles.add(item["title"])
            deduplicated_data.append(item)
            
    logger.info(f"原始数据: {len(data)} 条，去重后: {len(deduplicated_data)} 条")
    return deduplicated_data