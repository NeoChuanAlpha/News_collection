#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
新闻分析Web应用
功能：提供Web界面展示新闻分词、词频统计和主题聚类结果
"""

import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_from_directory
import logging
from datetime import datetime
import topic_clustering
import word_segmentation
import word_visualization
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/web_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 确保目录存在
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

# 创建Flask应用
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

# 配置
app.config.update(
    SECRET_KEY='news_analysis_web_app',
    JSON_AS_ASCII=False,
    TEMPLATES_AUTO_RELOAD=True
)

# 确保必要的目录存在
ensure_dir('templates')
ensure_dir('static')
ensure_dir('static/js')
ensure_dir('static/css')
ensure_dir('static/images')
ensure_dir('logs')

# 主页
@app.route('/')
def index():
    return render_template('index.html')

# 分词页面
@app.route('/segmentation')
def segmentation():
    return render_template('segmentation.html')

# 词频统计页面
@app.route('/word_frequency')
def word_frequency():
    return render_template('word_frequency.html')

# 主题聚类页面
@app.route('/topic_clustering')
def topic_clustering_page():
    return render_template('topic_clustering.html')

# API: 获取分词结果
@app.route('/api/segmentation', methods=['GET'])
def get_segmentation():
    try:
        # 获取分词结果文件路径
        file_path = 'word_segmentation/segmented_news_2025-02-25.csv'
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '分词结果文件不存在'}), 404
        
        # 读取分词结果
        df = pd.read_csv(file_path)
        
        # 返回前100条记录
        result = df.head(100).to_dict('records')
        
        return jsonify({
            'success': True,
            'data': result,
            'total': len(df)
        })
    
    except Exception as e:
        logger.error(f"获取分词结果出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API: 获取词频统计
@app.route('/api/word_frequency', methods=['GET'])
def get_word_frequency():
    try:
        # 获取词频统计文件路径
        file_path = 'word_segmentation/word_frequency_2025-02-25.csv'
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '词频统计文件不存在'}), 404
        
        # 读取词频统计
        df = pd.read_csv(file_path)
        
        # 获取请求参数
        limit = request.args.get('limit', default=100, type=int)
        
        # 返回前N条记录
        result = df.head(limit).to_dict('records')
        
        return jsonify({
            'success': True,
            'data': result,
            'total': len(df)
        })
    
    except Exception as e:
        logger.error(f"获取词频统计出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API: 获取主题聚类结果
@app.route('/api/topic_clustering', methods=['GET'])
def get_topic_clustering():
    try:
        # 获取聚类结果文件路径
        file_path = 'word_segmentation/visualization/cluster_data.json'
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': '聚类结果文件不存在'}), 404
        
        # 读取聚类结果
        with open(file_path, 'r', encoding='utf-8') as f:
            cluster_data = json.load(f)
        
        return jsonify({
            'success': True,
            'data': cluster_data
        })
    
    except Exception as e:
        logger.error(f"获取主题聚类结果出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API: 执行主题聚类
@app.route('/api/run_topic_clustering', methods=['POST'])
def run_topic_clustering():
    try:
        # 检查Content-Type
        if request.content_type != 'application/json':
            logger.warning(f"请求Content-Type不正确: {request.content_type}, 应为application/json")
            # 尝试从表单数据或查询参数获取数据
            if request.form:
                data = request.form.to_dict()
            else:
                data = request.args.to_dict()
                
            # 转换数据类型
            if 'n_clusters' in data:
                data['n_clusters'] = int(data['n_clusters'])
            if 'max_features' in data:
                data['max_features'] = int(data['max_features'])
        else:
            # 正常获取JSON数据
            data = request.get_json()
        
        # 设置默认值
        n_clusters = data.get('n_clusters', 10)
        max_features = data.get('max_features', 1000)
        reduction_method = data.get('reduction_method', 'pca')
        
        logger.info(f"执行主题聚类: n_clusters={n_clusters}, max_features={max_features}, reduction_method={reduction_method}")
        
        # 检查输入文件是否存在
        input_file = 'word_segmentation/segmented_news_2025-02-25.csv'
        if not os.path.exists(input_file):
            logger.error(f"输入文件不存在: {input_file}")
            return jsonify({'error': f"输入文件不存在: {input_file}"}), 404
        
        # 执行主题聚类
        result = topic_clustering.perform_topic_clustering(
            input_file=input_file,
            output_dir='word_segmentation/visualization',
            n_clusters=n_clusters,
            max_features=max_features,
            reduction_method=reduction_method
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except Exception as e:
        logger.error(f"执行主题聚类出错: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API: 获取可视化图片
@app.route('/api/visualization/<path:filename>')
def get_visualization(filename):
    return send_from_directory('word_segmentation/visualization', filename)

# 启动应用
if __name__ == '__main__':
    # 确保可视化目录存在
    ensure_dir('word_segmentation/visualization')
    
    # 检查是否已有聚类结果，如果没有则尝试执行聚类
    cluster_data_path = 'word_segmentation/visualization/cluster_data.json'
    if not os.path.exists(cluster_data_path):
        logger.info("未找到聚类结果，尝试执行主题聚类...")
        try:
            topic_clustering.main()
        except Exception as e:
            logger.error(f"执行主题聚类出错: {str(e)}")
            logger.info("创建默认聚类结果...")
            
            # 确保目录存在
            ensure_dir('word_segmentation/visualization')
            
            # 创建一个简单的默认聚类结果
            dummy_cluster_data = {
                "0": {
                    "size": 1,
                    "keywords": [{"word": "示例", "weight": 1.0}],
                    "news": [{"news_id": "example", "title": "示例新闻"}],
                    "points": [[0, 0]]
                }
            }
            
            # 保存默认聚类结果
            with open(cluster_data_path, 'w', encoding='utf-8') as f:
                json.dump(dummy_cluster_data, f, ensure_ascii=False, indent=2)
            
            # 创建一个简单的可视化图片
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8, 6))
            plt.text(0.5, 0.5, "聚类处理出错，请通过API重新运行聚类", ha='center', va='center', fontsize=14)
            plt.axis('off')
            vis_path = 'word_segmentation/visualization/clusters_2d.png'
            plt.savefig(vis_path)
            plt.close()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=5000, debug=True) 