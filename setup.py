#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
安装脚本
用于安装项目依赖
"""

from setuptools import setup, find_packages

setup(
    name="news_crawler",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.35.0",
        "pandas>=2.0.3",
        "python-dotenv>=1.0.0",
        "pytest>=7.3.1",
        "loguru>=0.7.0",
        "schedule>=1.2.0",
    ],
)