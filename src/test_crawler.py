#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
爬虫测试脚本
用于测试爬虫的主要功能
"""

import asyncio
import pytest
from main import NewsCrawler


@pytest.mark.asyncio
async def test_crawler_setup():
    """测试爬虫浏览器初始化"""
    crawler = NewsCrawler()
    await crawler.setup()
    assert crawler.browser is not None
    assert crawler.page is not None
    await crawler.close()


@pytest.mark.asyncio
async def test_navigate_to_page():
    """测试页面导航"""
    crawler = NewsCrawler()
    await crawler.setup()
    await crawler.navigate_to_page()
    title = await crawler.page.title()
    assert "newsnow" in title.lower() or "news" in title.lower()
    await crawler.close()


@pytest.mark.asyncio
async def test_extract_news():
    """测试新闻提取"""
    crawler = NewsCrawler()
    await crawler.setup()
    await crawler.navigate_to_page()
    await crawler.scroll_to_bottom()
    news_data = await crawler.extract_news()
    assert len(news_data) > 0
    assert "title" in news_data[0]
    assert "collect_time" in news_data[0]
    await crawler.close()


if __name__ == "__main__":
    asyncio.run(test_extract_news())