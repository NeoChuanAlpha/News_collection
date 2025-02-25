# 新闻爬虫项目

## 项目概述

这是一个用于从指定网站实时获取热点新闻数据的爬虫项目。项目使用Playwright模拟浏览器行为，能够从动态加载的网页中提取新闻数据，并将结果保存为CSV和Excel格式。

## 主要特点

- **数据问题修复**：
  - 规范化序号，确保连续且不重复
  - 智能识别新闻来源，不再显示"未知来源"
  - 自动去重功能，避免重复采集同一新闻
  - 提取更多元数据（发布时间、摘要等）

- **运行模式**：
  - 单次采集模式：采集一次数据，保存为带时间戳的CSV和Excel文件
  - 持续采集模式：按指定时间间隔（默认5分钟）持续采集，增量更新同一个文件

- **其他功能**：
  - 完整的命令行参数支持，灵活配置运行参数
  - 详细的日志记录系统，记录运行状态和错误信息
  - 自动截图和HTML缓存，便于调试和问题分析
  - 执行摘要生成，记录每次采集的统计信息

## 目录结构

```
news_crawler/
│
├── data/                   # 保存爬取的数据
│   ├── news_*_*.csv        # 单次模式数据文件（CSV格式）
│   ├── news_*_*.xlsx       # 单次模式数据文件（Excel格式）
│   └── continuous_news_*.csv # 持续模式数据文件
│
├── screenshots/            # 页面截图
│   ├── page_state_*.png    # 正常页面状态截图
│   └── error_*.png         # 出错时的页面截图
│
├── logs/                   # 日志文件目录
│   ├── crawler_*.log       # 爬虫运行日志
│   └── summary_*.json      # 采集摘要信息
│
├── html_cache/            # HTML源码缓存
│   └── page_content_*.html # 保存的HTML源码
│
├── news_crawler.py         # 主程序脚本
├── start_crawler.bat       # Windows启动脚本
├── requirements.txt        # 项目依赖
└── README.md               # 项目说明
```

## 安装步骤

1. 克隆或下载本项目代码
2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```
3. 安装Playwright浏览器引擎
   ```bash
   playwright install
   ```

## 运行方法

### 使用启动脚本（推荐）

双击运行`start_crawler.bat`，根据提示选择运行模式：

```
1. 单次采集模式 - 采集一次数据并保存
2. 持续采集模式 - 每5分钟自动采集一次数据
3. 自定义间隔采集 - 指定时间间隔的持续采集模式
4. 退出
```

### 使用命令行直接运行

#### 单次采集模式：
```bash
python news_crawler.py --mode=single
```

#### 持续采集模式（默认5分钟间隔）：
```bash
python news_crawler.py --mode=continuous
```

#### 自定义间隔的持续采集模式：
```bash
python news_crawler.py --mode=continuous --interval=10
```

#### 指定输出文件（持续模式）：
```bash
python news_crawler.py --mode=continuous --output=data/my_news.csv
```

#### 启用调试日志：
```bash
python news_crawler.py --mode=single --debug
```

## 数据字段说明

生成的CSV/Excel文件包含以下字段：

| 字段名           | 说明                                    |
|-----------------|----------------------------------------|
| number          | 按顺序编号的序号（从1开始连续）          |
| original_number | 原始网页中的序号（如果有）              |
| title           | 新闻标题                                |
| source          | 新闻来源（网站名称）                    |
| link            | 新闻链接                                |
| summary         | 新闻摘要（如果能够提取）                |
| pub_time        | 发布时间（如果能够提取）                |
| collect_time    | 采集时间                                |
| news_id         | 新闻唯一标识（用于去重）                |

## 注意事项

- 请确保网络连接稳定
- 避免过于频繁的访问以防被目标网站限制
- 定期检查日志和截图，确保爬虫正常运行
- 持续模式下建议设置合理的采集间隔（建议不低于3分钟）

## 常见问题解决

1. **无法启动浏览器**：确保已正确安装Playwright及其浏览器引擎
   ```bash
   playwright install
   ```

2. **找不到新闻数据**：网页结构可能已更改，检查最新的截图和HTML缓存

3. **CSV文件编码问题**：程序使用UTF-8-SIG编码，如遇到乱码请检查打开方式

4. **持续模式中断**：检查日志文件了解中断原因，可能是网络问题或网站结构变化