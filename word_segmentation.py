#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新闻数据分词处理脚本
功能：读取CSV新闻数据，进行分词处理，并输出到新的CSV文件
"""

import os
import csv
import jieba
import jieba.posseg as pseg
import pandas as pd
from collections import Counter
import re
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/word_segmentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 确保目录存在
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

# 文本预处理
def clean_text(text):
    if not isinstance(text, str):
        return ""
    
    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 去除URL
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # 去除特殊符号和数字
    text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z]', ' ', text)
    
    # 全角转半角
    text = ''.join([chr(ord(c) - 0xFEE0) if ord(c) >= 0xFF01 and ord(c) <= 0xFF5E else c for c in text])
    
    # 去除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

# 加载停用词
def load_stopwords(stopwords_file='stopwords.txt'):
    try:
        with open(stopwords_file, 'r', encoding='utf-8') as f:
            stopwords = [line.strip() for line in f]
        logger.info(f"已加载停用词 {len(stopwords)} 个")
        return set(stopwords)
    except FileNotFoundError:
        logger.warning(f"停用词文件 {stopwords_file} 不存在，将使用默认停用词")
        # 扩展默认停用词列表，包含更多常见无用词
        default_stopwords = set([
            '的', '了', '和', '是', '就', '都', '而', '及', '与', '这', '那', '有', '在', '中', '为', '对', '等', '上', '下',
            '我', '你', '他', '她', '它', '们', '我们', '你们', '他们', '她们', '它们', 
            '啊', '哦', '呢', '吧', '吗', '呀', '哈', '哎', '哟', '嗯', '嘛',
            '一个', '一些', '一样', '一直', '一切', '一边', '一面', '一点',
            '不', '不是', '不要', '不能', '不会', '不过', '不如', '不得', '不怕', '不敢',
            '没', '没有', '没什么', '没办法',
            '很', '太', '非常', '越', '更', '最', '极', '挺',
            '又', '也', '还', '仍', '再', '才', '刚', '就', '曾', '已', '已经',
            '能', '可以', '可能', '会', '要', '应该', '得', '必须',
            '这个', '这些', '这样', '这么', '这里', '这种',
            '那个', '那些', '那样', '那么', '那里', '那种',
            '什么', '怎么', '怎样', '怎么样', '为什么', '如何',
            '只', '只是', '只有', '只要', '只能',
            '但', '但是', '然而', '而', '而且', '并', '并且',
            '因为', '因此', '所以', '由于', '以便', '以免',
            '如果', '若', '若是', '如', '如此', '如何',
            '虽然', '虽', '尽管', '不过', '可是',
            '或', '或者', '或是', '是否', '还是',
            '啥', '咋', '咱', '咱们', '俺', '俺们',
            '某', '某个', '某些', '某种',
            '其', '其他', '其它', '其中', '其实',
            '之', '之一', '之中', '之所以',
            '每', '每个', '每种', '每次',
            '各', '各个', '各种', '各自',
            '从', '向', '于', '至', '到', '给', '让', '被',
            '说', '看', '想', '觉得', '认为', '表示', '指出', '介绍'
        ])
        logger.info(f"使用默认停用词 {len(default_stopwords)} 个")
        return default_stopwords

# 加载自定义词典
def load_custom_dict(dict_file='custom_dict.txt'):
    try:
        jieba.load_userdict(dict_file)
        logger.info(f"已加载自定义词典: {dict_file}")
        return True
    except Exception as e:
        logger.warning(f"加载自定义词典出错: {str(e)}")
        return False

# 动态更新词典（从高频词中提取可能的新词）
def update_dynamic_dict(word_freq_file, output_dict_file, min_freq=5, min_length=2):
    try:
        # 读取词频文件
        df = pd.read_csv(word_freq_file)
        
        # 筛选可能的新词（频率大于阈值且长度大于等于最小长度）
        potential_new_words = df[(df['frequency'] >= min_freq) & (df['word'].str.len() >= min_length)]
        
        # 将词性为n(名词)、v(动词)、a(形容词)的词添加到自定义词典
        valid_pos = ['n', 'v', 'a', 'an', 'vn', 'nr', 'ns', 'nt', 'nz']
        new_words = []
        
        for _, row in potential_new_words.iterrows():
            word = row['word']
            pos = row.get('pos', '')
            if pos in valid_pos:
                new_words.append(f"{word} {pos}")
        
        # 保存到自定义词典文件
        with open(output_dict_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_words))
        
        logger.info(f"已更新动态词典，添加 {len(new_words)} 个新词到 {output_dict_file}")
        
        # 重新加载词典
        jieba.load_userdict(output_dict_file)
        
        return len(new_words)
    
    except Exception as e:
        logger.error(f"更新动态词典出错: {str(e)}")
        return 0

# 分词处理
def segment_text(text, stopwords=None):
    if not text:
        return []
    
    # 清洗文本
    cleaned_text = clean_text(text)
    
    # 使用jieba进行分词
    words = jieba.cut(cleaned_text, cut_all=False)
    
    # 过滤停用词
    if stopwords:
        words = [word for word in words if word not in stopwords and len(word.strip()) > 0]
    else:
        words = [word for word in words if len(word.strip()) > 0]
    
    return words

# 词性标注
def pos_tagging(text):
    if not text:
        return []
    
    # 清洗文本
    cleaned_text = clean_text(text)
    
    # 使用jieba进行词性标注
    words_pos = pseg.cut(cleaned_text)
    
    # 返回词和词性的元组列表
    return [(word, flag) for word, flag in words_pos]

# 处理CSV文件
def process_csv(input_file, output_file, stopwords_file=None, custom_dict_file=None):
    try:
        # 加载自定义词典
        if custom_dict_file:
            load_custom_dict(custom_dict_file)
        
        # 加载停用词
        stopwords = load_stopwords(stopwords_file) if stopwords_file else None
        
        # 读取CSV文件
        df = pd.read_csv(input_file, encoding='utf-8')
        logger.info(f"已读取CSV文件: {input_file}, 共 {len(df)} 条记录")
        
        # 创建结果列表
        results = []
        
        # 处理每一行
        for index, row in df.iterrows():
            try:
                # 获取标题
                title = row.get('title', '')
                
                # 分词
                words = segment_text(title, stopwords)
                
                # 词性标注
                words_pos = pos_tagging(title)
                
                # 构建结果
                result = {
                    'news_id': row.get('news_id', ''),
                    'title': title,
                    'segmented_words': ' '.join(words),
                    'word_count': len(words),
                    'pos_tagging': ' '.join([f"{word}_{flag}" for word, flag in words_pos])
                }
                
                results.append(result)
                
                if (index + 1) % 100 == 0:
                    logger.info(f"已处理 {index + 1} 条记录")
                
            except Exception as e:
                logger.error(f"处理第 {index + 1} 行时出错: {str(e)}")
        
        # 创建DataFrame并保存
        result_df = pd.DataFrame(results)
        result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"分词结果已保存到: {output_file}, 共 {len(result_df)} 条记录")
        
        return result_df
    
    except Exception as e:
        logger.error(f"处理CSV文件时出错: {str(e)}")
        return None

# 生成词频统计
def generate_word_frequency(segmented_df, output_file):
    try:
        # 获取所有分词
        all_words = []
        pos_dict = {}  # 用于存储词性信息
        
        # 处理分词和词性标注
        for index, row in segmented_df.iterrows():
            # 处理分词
            words = row.get('segmented_words', '')
            if isinstance(words, str):
                all_words.extend(words.split())
            
            # 处理词性标注
            pos_tagging = row.get('pos_tagging', '')
            if isinstance(pos_tagging, str):
                for word_pos in pos_tagging.split():
                    if '_' in word_pos:
                        word, pos = word_pos.split('_', 1)
                        pos_dict[word] = pos
        
        # 计算词频
        word_freq = Counter(all_words)
        total_words = len(all_words)
        
        # 转换为DataFrame
        freq_df = pd.DataFrame({
            'word': list(word_freq.keys()),
            'frequency': list(word_freq.values())
        })
        
        # 添加百分比列
        freq_df['percentage'] = freq_df['frequency'] / total_words * 100
        freq_df['percentage'] = freq_df['percentage'].round(2)
        freq_df['percentage_str'] = freq_df['percentage'].apply(lambda x: f"{x:.2f}%")
        
        # 添加词性列
        freq_df['pos'] = freq_df['word'].map(lambda word: pos_dict.get(word, 'n'))  # 默认为名词
        
        # 按词频降序排序
        freq_df = freq_df.sort_values('frequency', ascending=False)
        
        # 保存到CSV
        freq_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        logger.info(f"词频统计已保存到: {output_file}, 共 {len(freq_df)} 个不同词汇")
        
        return freq_df
    
    except Exception as e:
        logger.error(f"生成词频统计时出错: {str(e)}")
        return None

# 创建停用词文件
def create_default_stopwords_file(output_file):
    default_stopwords = [
        '的', '了', '和', '是', '就', '都', '而', '及', '与', '这', '那', '有', '在', '中', 
        '为', '对', '等', '上', '下', '年', '月', '日', '时', '分', '秒', '来', '去', '到', 
        '说', '要', '看', '想', '会', '可以', '能', '得', '着', '过', '还', '没', '很', '再',
        '吗', '吧', '啊', '呢', '哦', '哪', '什么', '怎么', '如何', '为什么', '因为', '所以',
        '但是', '不过', '然而', '可是', '虽然', '如果', '只要', '无论', '或者', '以及', '并且',
        '不仅', '而且', '不但', '何况', '尚且', '甚至', '况且', '不管', '只有', '除了', '以外',
        '万', '亿', '个', '十', '百', '千', '万热度', '讨论', '热度'
    ]
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for word in default_stopwords:
                f.write(word + '\n')
        logger.info(f"已创建默认停用词文件: {output_file}, 共 {len(default_stopwords)} 个停用词")
    except Exception as e:
        logger.error(f"创建停用词文件时出错: {str(e)}")

# 创建自定义词典文件
def create_custom_dict_file(output_file):
    custom_words = [
        # 手机品牌和型号
        "小米15 Ultra n 100",
        "iPhone16ProMax n 100",
        "vivox200Ultra n 100",
        "骁龙8e n 100",
        "红米K70 n 100",
        "魅族21 n 100",
        "魅族21note n 100",
        "华为Mate70 n 100",
        "华为P70 n 100",
        "荣耀Magic7 n 100",
        "OPPO Find X8 n 100",
        "一加12 n 100",
        "三星S24Ultra n 100",
        "折叠屏 n 100",
        
        # 科技公司
        "特斯拉 n 100",
        "OpenAI n 100",
        "DeepSeek n 100",
        "百度 n 100",
        "阿里巴巴 n 100",
        "腾讯 n 100",
        "字节跳动 n 100",
        "微软 n 100",
        "谷歌 n 100",
        "苹果 n 100",
        "英伟达 n 100",
        "AMD n 100",
        "英特尔 n 100",
        "高通 n 100",
        "联发科 n 100",
        
        # 人物
        "尹锡悦 nr 100",
        "普京 nr 100",
        "拜登 nr 100",
        "马斯克 nr 100",
        "库克 nr 100",
        "黄仁勋 nr 100",
        "雷军 nr 100",
        "马化腾 nr 100",
        "张一鸣 nr 100",
        "李彦宏 nr 100",
        "马云 nr 100",
        "任正非 nr 100",
        
        # 技术术语
        "人工智能 n 100",
        "大模型 n 100",
        "机器学习 n 100",
        "深度学习 n 100",
        "神经网络 n 100",
        "自动驾驶 n 100",
        "fsd n 100",
        "元宇宙 n 100",
        "区块链 n 100",
        "量子计算 n 100",
        "边缘计算 n 100",
        "云计算 n 100",
        "大数据 n 100",
        "物联网 n 100",
        "5G n 100",
        "6G n 100",
        "WiFi7 n 100",
        
        # 热门话题
        "六姊妹 n 100",
        "ChatGPT n 100",
        "Claude n 100",
        "Gemini n 100",
        "Sora n 100",
        "AIGC n 100",
        "生成式AI n 100",
        "数字人民币 n 100",
        "碳中和 n 100",
        "碳达峰 n 100",
        "元宇宙 n 100",
        "Web3.0 n 100",
        "NFT n 100"
    ]
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(custom_words))
        logger.info(f"已创建自定义词典文件: {output_file}, 共 {len(custom_words)} 个词条")
        return True
    except Exception as e:
        logger.error(f"创建自定义词典文件时出错: {str(e)}")
        return False

# 主函数
def main():
    # 确保目录存在
    ensure_dir('logs')
    ensure_dir('word_segmentation')
    ensure_dir('word_segmentation/visualization')
    
    # 创建默认停用词文件
    stopwords_file = 'word_segmentation/stopwords.txt'
    create_default_stopwords_file(stopwords_file)
    
    # 创建自定义词典文件
    custom_dict_file = 'word_segmentation/custom_dict.txt'
    create_custom_dict_file(custom_dict_file)
    
    # 添加自定义词典
    jieba.load_userdict(custom_dict_file)
    
    # 输入和输出文件
    input_file = 'data/continuous_news_2025-02-25.csv'
    output_file = 'word_segmentation/segmented_news_2025-02-25.csv'
    freq_file = 'word_segmentation/word_frequency_2025-02-25.csv'
    
    # 处理CSV文件
    segmented_df = process_csv(input_file, output_file, stopwords_file, custom_dict_file)
    
    # 生成词频统计
    if segmented_df is not None:
        freq_df = generate_word_frequency(segmented_df, freq_file)
        
        # 更新动态词典
        if freq_df is not None:
            dynamic_dict_file = 'word_segmentation/dynamic_dict.txt'
            update_dynamic_dict(freq_file, dynamic_dict_file, min_freq=3, min_length=2)
    
    logger.info("分词处理完成")

if __name__ == "__main__":
    main()