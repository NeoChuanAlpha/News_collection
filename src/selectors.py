#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
选择器配置模块
用于管理网页元素选择器
"""

# 网站特定选择器
class Selectors:
    """网站元素选择器类"""
    
    # 新闻列表和项目
    NEWS_CONTAINER = ".news-list"
    NEWS_ITEM = ".news-item"
    
    # 新闻元素
    NEWS_TITLE = ".news-title"
    NEWS_SOURCE = ".news-source"
    NEWS_TIME = ".news-time"
    NEWS_SUMMARY = ".news-summary"
    NEWS_LINK = ".news-link"
    
    # 加载更多
    LOAD_MORE_BUTTON = ".load-more-btn"
    
    # 分类标签
    CATEGORY_TABS = ".category-tabs"
    
    # 登录相关
    LOGIN_BUTTON = ".login-btn"
    USERNAME_INPUT = "#username"
    PASSWORD_INPUT = "#password"
    SUBMIT_BUTTON = ".submit-btn"
    
    @classmethod
    def get_selector_dict(cls):
        """返回所有选择器的字典
        
        Returns:
            dict: 选择器名称和值的字典
        """
        return {k: v for k, v in cls.__dict__.items() 
                if not k.startswith('_') and not callable(getattr(cls, k))}