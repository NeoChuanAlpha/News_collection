@echo off
echo 新闻爬虫启动脚本
echo ====================
echo 1. 单次采集模式 - 采集一次数据并保存
echo 2. 持续采集模式 - 每5分钟自动采集一次数据
echo 3. 自定义间隔采集 - 指定时间间隔的持续采集模式
echo 4. 退出
echo ====================

set /p choice=请选择运行模式 (1/2/3/4): 

if "%choice%"=="1" (
    echo 正在启动单次采集模式...
    python news_crawler.py --mode=single
    goto end
)

if "%choice%"=="2" (
    echo 正在启动持续采集模式，每5分钟自动采集一次...
    python news_crawler.py --mode=continuous
    goto end
)

if "%choice%"=="3" (
    set /p interval=请输入采集间隔(分钟): 
    echo 正在启动自定义间隔采集模式，每%interval%分钟采集一次...
    python news_crawler.py --mode=continuous --interval=%interval%
    goto end
)

if "%choice%"=="4" (
    echo 退出程序
    goto end
)

echo 无效的选择，请重新运行脚本
pause

:end
echo 程序已结束运行
pause