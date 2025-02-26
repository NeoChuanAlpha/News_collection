#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新闻主题聚类模块
功能：对分词后的新闻数据进行主题聚类，并生成可视化结果
"""

import os
import pandas as pd
import numpy as np
import jieba
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from collections import Counter
import json
from datetime import datetime
import re
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/topic_clustering_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 确保目录存在
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

# 加载分词后的数据
def load_segmented_data(file_path):
    logger.info(f"加载分词数据: {file_path}")
    df = pd.read_csv(file_path)
    return df

# 将分词列表转换为空格分隔的字符串（用于TF-IDF向量化）
def prepare_text_for_vectorization(df):
    logger.info("准备文本向量化")
    # 将分词列表转换为空格分隔的字符串
    df['text_for_vectorization'] = df['segmented_words'].apply(
        lambda x: ' '.join(x.split()) if isinstance(x, str) else ''
    )
    # 确保文本不为空
    non_empty_texts = df['text_for_vectorization'].str.strip().str.len() > 0
    logger.info(f"有效文本数量: {non_empty_texts.sum()}/{len(df)}")
    return df

# 使用TF-IDF进行文本向量化
def vectorize_text(texts, max_features=1000):
    logger.info(f"文本向量化，最大特征数: {max_features}")
    # 添加更多参数以处理空词汇表问题
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        min_df=1,  # 至少出现在1个文档中
        max_df=0.95,  # 最多出现在95%的文档中
        stop_words=None,  # 不使用内置停用词
        token_pattern=r'(?u)\b\w+\b'  # 匹配任何单词
    )
    
    # 确保文本不为空
    valid_texts = [text for text in texts if text and text.strip()]
    if not valid_texts:
        raise ValueError("没有有效的文本进行向量化")
    
    logger.info(f"有效文本数量: {len(valid_texts)}")
    X = vectorizer.fit_transform(valid_texts)
    logger.info(f"向量化完成，形状: {X.shape}")
    return X, vectorizer

# 使用K-means进行聚类
def kmeans_clustering(X, n_clusters=10):
    logger.info(f"K-means聚类，聚类数: {n_clusters}")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X)
    logger.info("K-means聚类完成")
    return clusters, kmeans

# 使用DBSCAN进行聚类
def dbscan_clustering(X, eps=0.5, min_samples=5):
    logger.info(f"DBSCAN聚类，eps: {eps}, min_samples: {min_samples}")
    dbscan = DBSCAN(eps=eps, min_samples=min_samples)
    clusters = dbscan.fit_predict(X)
    logger.info("DBSCAN聚类完成")
    return clusters, dbscan

# 降维用于可视化
def dimensionality_reduction(X, method='pca', n_components=2):
    logger.info(f"使用{method}进行降维到{n_components}维")
    
    if method.lower() == 'pca':
        reducer = PCA(n_components=n_components, random_state=42)
        X_reduced = reducer.fit_transform(X.toarray())
    elif method.lower() == 'svd':
        reducer = TruncatedSVD(n_components=n_components, random_state=42)
        X_reduced = reducer.fit_transform(X)
    elif method.lower() == 'tsne':
        reducer = TSNE(n_components=n_components, random_state=42)
        X_reduced = reducer.fit_transform(X.toarray())
    else:
        raise ValueError(f"不支持的降维方法: {method}")
    
    logger.info(f"降维完成，形状: {X_reduced.shape}")
    return X_reduced, reducer

# 提取每个聚类的关键词
def extract_cluster_keywords(vectorizer, kmeans, n_terms=10):
    logger.info(f"提取每个聚类的前{n_terms}个关键词")
    
    # 获取特征名称（词汇）
    terms = vectorizer.get_feature_names_out()
    
    # 获取聚类中心
    centers = kmeans.cluster_centers_
    
    # 为每个聚类提取关键词
    keywords = {}
    for i in range(centers.shape[0]):
        # 获取该聚类中心的词汇权重
        indices = centers[i].argsort()[::-1][:n_terms]
        keywords[i] = [(terms[j], centers[i][j]) for j in indices]
    
    logger.info("关键词提取完成")
    return keywords

# 生成聚类可视化
def visualize_clusters(X_reduced, clusters, output_dir='word_segmentation/visualization', filename='cluster_visualization.png'):
    ensure_dir(output_dir)
    
    plt.figure(figsize=(12, 10))
    
    # 获取唯一的聚类标签
    unique_clusters = np.unique(clusters)
    
    # 为每个聚类分配不同的颜色
    colors = plt.cm.rainbow(np.linspace(0, 1, len(unique_clusters)))
    
    # 绘制每个聚类
    for cluster_id, color in zip(unique_clusters, colors):
        # 对于噪声点（DBSCAN中的-1），使用灰色
        if cluster_id == -1:
            color = [0.7, 0.7, 0.7, 1.0]  # 灰色
        
        # 获取该聚类的所有点
        mask = clusters == cluster_id
        plt.scatter(X_reduced[mask, 0], X_reduced[mask, 1], 
                   c=[color], label=f'Cluster {cluster_id}',
                   alpha=0.7, s=50)
    
    plt.title('新闻主题聚类可视化')
    plt.xlabel('Dimension 1')
    plt.ylabel('Dimension 2')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path)
    plt.close()
    logger.info(f"已保存聚类可视化: {output_path}")
    
    return output_path

# 生成聚类结果数据
def generate_cluster_data(df, clusters, keywords, X_reduced):
    logger.info("生成聚类结果数据")
    
    # 添加聚类标签到原始数据
    df['cluster'] = clusters
    
    # 创建聚类结果数据
    cluster_data = {}
    
    # 获取唯一的聚类标签
    unique_clusters = np.unique(clusters)
    
    for cluster_id in unique_clusters:
        # 获取该聚类的所有新闻
        cluster_news = df[df['cluster'] == cluster_id]
        
        # 获取该聚类的关键词
        if cluster_id in keywords:
            cluster_keywords = keywords[cluster_id]
        else:
            # 对于DBSCAN可能没有聚类中心
            cluster_keywords = []
        
        # 获取该聚类的坐标点
        cluster_points = X_reduced[clusters == cluster_id].tolist()
        
        # 创建聚类数据
        cluster_data[int(cluster_id)] = {
            'size': len(cluster_news),
            'keywords': [{'word': word, 'weight': float(weight)} for word, weight in cluster_keywords],
            'news': cluster_news[['news_id', 'title']].to_dict('records'),
            'points': cluster_points
        }
    
    logger.info(f"聚类结果数据生成完成，共{len(unique_clusters)}个聚类")
    return cluster_data

# 保存聚类结果为JSON
def save_cluster_data(cluster_data, output_dir='word_segmentation/visualization', filename='cluster_data.json'):
    ensure_dir(output_dir)
    
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(cluster_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"已保存聚类结果数据: {output_path}")
    return output_path

# 主题聚类处理
def perform_topic_clustering(input_file, output_dir='word_segmentation/visualization', 
                            n_clusters=10, max_features=1000, reduction_method='pca'):
    # 确保输出目录存在
    ensure_dir(output_dir)
    
    try:
        # 加载分词数据
        df = load_segmented_data(input_file)
        
        # 准备文本向量化
        df = prepare_text_for_vectorization(df)
        
        # 检查有效文本数量
        valid_texts = df['text_for_vectorization'].str.strip().str.len() > 0
        valid_df = df[valid_texts].copy()
        
        if len(valid_df) < n_clusters:
            logger.warning(f"有效文本数量({len(valid_df)})小于聚类数({n_clusters})，调整聚类数")
            n_clusters = max(2, len(valid_df) // 2)  # 至少2个聚类
        
        # 文本向量化
        X, vectorizer = vectorize_text(valid_df['text_for_vectorization'], max_features=max_features)
        
        # K-means聚类
        clusters, kmeans = kmeans_clustering(X, n_clusters=n_clusters)
        
        # 提取聚类关键词
        keywords = extract_cluster_keywords(vectorizer, kmeans)
        
        # 降维用于可视化
        X_reduced, reducer = dimensionality_reduction(X, method=reduction_method)
        
        # 可视化聚类
        vis_path = visualize_clusters(X_reduced, clusters, output_dir=output_dir, filename='clusters_2d.png')
        
        # 将聚类结果映射回原始数据
        valid_df['cluster'] = clusters
        
        # 生成聚类结果数据
        cluster_data = generate_cluster_data(valid_df, clusters, keywords, X_reduced)
        
        # 保存聚类结果
        json_path = save_cluster_data(cluster_data, output_dir=output_dir)
        
        return {
            'visualization_path': vis_path,
            'data_path': json_path,
            'cluster_count': len(np.unique(clusters)),
            'news_count': len(valid_df)
        }
    
    except Exception as e:
        logger.error(f"主题聚类处理出错: {str(e)}")
        
        # 创建一个简单的备用聚类结果
        dummy_cluster_data = {
            "0": {
                "size": 1,
                "keywords": [{"word": "示例", "weight": 1.0}],
                "news": [{"news_id": "example", "title": "示例新闻"}],
                "points": [[0, 0]]
            }
        }
        
        # 保存备用聚类结果
        json_path = save_cluster_data(dummy_cluster_data, output_dir=output_dir)
        
        # 创建一个简单的可视化图片
        plt.figure(figsize=(8, 6))
        plt.text(0.5, 0.5, "聚类处理出错，请检查日志", ha='center', va='center', fontsize=14)
        plt.axis('off')
        vis_path = os.path.join(output_dir, 'clusters_2d.png')
        plt.savefig(vis_path)
        plt.close()
        
        return {
            'visualization_path': vis_path,
            'data_path': json_path,
            'cluster_count': 1,
            'news_count': 0,
            'error': str(e)
        }

# 主函数
def main():
    input_file = 'word_segmentation/segmented_news_2025-02-25.csv'
    output_dir = 'word_segmentation/visualization'
    
    # 执行主题聚类
    result = perform_topic_clustering(
        input_file=input_file,
        output_dir=output_dir,
        n_clusters=10,
        max_features=1000,
        reduction_method='pca'
    )
    
    logger.info(f"主题聚类处理完成: {result}")

if __name__ == "__main__":
    main() 