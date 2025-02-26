import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.font_manager import FontProperties
import numpy as np
from wordcloud import WordCloud
import jieba
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 确保目录存在
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"创建目录: {directory}")

# 加载词频数据
def load_word_frequency(file_path):
    logging.info(f"加载词频数据: {file_path}")
    df = pd.read_csv(file_path)
    return df

# 绘制词频柱状图
def plot_top_words(df, top_n=20, output_dir='word_segmentation/visualization'):
    ensure_dir(output_dir)
    
    # 获取前N个高频词
    top_words = df.head(top_n)
    
    plt.figure(figsize=(12, 8))
    plt.barh(top_words['word'][::-1], top_words['frequency'][::-1])
    plt.xlabel('频率')
    plt.ylabel('词汇')
    plt.title(f'前{top_n}个高频词汇')
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, f'top_{top_n}_words.png')
    plt.savefig(output_path)
    plt.close()
    logging.info(f"已保存柱状图: {output_path}")

# 绘制词云
def generate_wordcloud(df, output_dir='word_segmentation/visualization'):
    ensure_dir(output_dir)
    
    # 创建词频字典
    word_freq = dict(zip(df['word'], df['frequency']))
    
    # 生成词云
    wordcloud = WordCloud(
        font_path='simhei.ttf',  # 使用系统中文字体
        width=800, 
        height=400, 
        background_color='white',
        max_words=100
    ).generate_from_frequencies(word_freq)
    
    plt.figure(figsize=(16, 8))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    
    output_path = os.path.join(output_dir, 'wordcloud.png')
    plt.savefig(output_path)
    plt.close()
    logging.info(f"已保存词云图: {output_path}")

# 绘制词频分布图
def plot_frequency_distribution(df, output_dir='word_segmentation/visualization'):
    ensure_dir(output_dir)
    
    # 计算词频分布
    freq_counts = df['frequency'].value_counts().sort_index()
    
    plt.figure(figsize=(12, 8))
    plt.bar(freq_counts.index, freq_counts.values)
    plt.xlabel('词频')
    plt.ylabel('词汇数量')
    plt.title('词频分布')
    plt.yscale('log')  # 使用对数刻度更好地显示分布
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'frequency_distribution.png')
    plt.savefig(output_path)
    plt.close()
    logging.info(f"已保存词频分布图: {output_path}")

# 主函数
def main():
    word_freq_file = 'word_segmentation/word_frequency_2025-02-25.csv'
    output_dir = 'word_segmentation/visualization'
    
    # 确保输出目录存在
    ensure_dir(output_dir)
    
    # 加载词频数据
    df = load_word_frequency(word_freq_file)
    
    # 绘制前20个高频词柱状图
    plot_top_words(df, top_n=20, output_dir=output_dir)
    
    # 绘制前50个高频词柱状图
    plot_top_words(df, top_n=50, output_dir=output_dir)
    
    # 生成词云
    generate_wordcloud(df, output_dir=output_dir)
    
    # 绘制词频分布图
    plot_frequency_distribution(df, output_dir=output_dir)
    
    logging.info("可视化处理完成")

if __name__ == "__main__":
    main()