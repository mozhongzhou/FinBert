import os
import json
import glob
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np
from tqdm import tqdm

from sentiment_analysis.model import FinBertSentimentAnalyzer

# 导入项目配置
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from preprocess.config import *


def load_processed_files(ticker: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
    """
    加载处理后的文本文件
    
    Args:
        ticker: 可选的股票代码筛选
        
    Returns:
        按公司和报告日期组织的文本字典
    """
    files_dict = {}
    
    # 获取所有处理后的文件
    section_files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*_md_and_a.txt"))
    section_files += glob.glob(os.path.join(PROCESSED_DATA_DIR, "*_risk_factors.txt"))
    
    # 按股票代码筛选
    if ticker:
        section_files = [f for f in section_files if f"/{ticker}_" in f.replace("\\", "/")]
    
    for file_path in section_files:
        filename = os.path.basename(file_path)
        # 解析文件名获取股票代码、报告日期和章节名称
        parts = filename.split('_')
        if len(parts) >= 4:
            ticker = parts[0]
            date = parts[2]
            section = '_'.join(parts[3:]).replace('.txt', '')
            
            key = f"{ticker}_{date}"
            if key not in files_dict:
                files_dict[key] = []
                
            # 读取文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    sentences = [line.strip() for line in f if line.strip()]
                
                files_dict[key].append({
                    'section': section,
                    'sentences': sentences
                })
            except Exception as e:
                print(f"读取文件 {file_path} 出错: {e}")
    
    return files_dict


def analyze_reports(analyzer, ticker: Optional[str] = None, batch_size: int = 8) -> Dict:
    """
    分析报告文本的情感
    
    Args:
        analyzer: 情感分析器实例
        ticker: 可选的股票代码筛选
        batch_size: 批处理大小
        
    Returns:
        分析结果字典
    """
    # 加载文本文件
    files_dict = load_processed_files(ticker)
    
    results = {}
    
    # 对每个报告进行分析
    for report_key, sections in tqdm(files_dict.items(), desc="分析报告"):
        report_results = {
            'summary': {'positive': 0, 'neutral': 0, 'negative': 0},
            'sections': {}
        }
        
        total_sentences = 0
        
        # 分析每个部分
        for section_data in sections:
            section_name = section_data['section']
            sentences = section_data['sentences']
            
            if not sentences:
                continue
                
            # 分析句子
            sentence_results = analyzer.analyze_batch(sentences, batch_size)
            
            # 统计情感分布
            section_stats = {'positive': 0, 'neutral': 0, 'negative': 0}
            section_sentences = []
            
            for result in sentence_results:
                label = result['label']
                section_stats[label] += 1
                
                # 记录句子级别的分析结果
                section_sentences.append({
                    'text': result['text'],
                    'label': label,
                    'confidence': result['confidence']
                })
            
            # 计算比例
            total = sum(section_stats.values())
            if total > 0:
                section_proportions = {
                    'positive': section_stats['positive'] / total,
                    'neutral': section_stats['neutral'] / total,
                    'negative': section_stats['negative'] / total
                }
            else:
                section_proportions = {'positive': 0, 'neutral': 0, 'negative': 0}
            
            # 更新报告总结果
            for label in ['positive', 'neutral', 'negative']:
                report_results['summary'][label] += section_stats[label]
            
            total_sentences += total
            
            # 保存部分结果
            report_results['sections'][section_name] = {
                'stats': section_stats,
                'proportions': section_proportions,
                'sentences': section_sentences
            }
        
        # 计算整体比例
        if total_sentences > 0:
            for label in ['positive', 'neutral', 'negative']:
                report_results['summary'][label + '_ratio'] = report_results['summary'][label] / total_sentences
        else:
            for label in ['positive', 'neutral', 'negative']:
                report_results['summary'][label + '_ratio'] = 0
        
        results[report_key] = report_results
    
    return results


def save_analysis_results(results: Dict, output_dir: str = RESULTS_DIR):
    """保存分析结果到JSON文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存整体结果
    with open(os.path.join(output_dir, 'analysis_results.json'), 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 为每个报告保存单独的JSON文件
    for report_key, report_data in results.items():
        output_file = os.path.join(output_dir, f"{report_key}_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    print(f"分析结果已保存到 {output_dir}")


def generate_summary_csv(results: Dict, output_dir: str = RESULTS_DIR):
    """生成摘要CSV文件，便于快速查看分析结果"""
    summary_data = []
    
    for report_key, report_data in results.items():
        parts = report_key.split('_')
        ticker = parts[0]
        date = parts[1]
        
        # 从摘要中提取比例
        positive_ratio = report_data['summary'].get('positive_ratio', 0)
        neutral_ratio = report_data['summary'].get('neutral_ratio', 0)
        negative_ratio = report_data['summary'].get('negative_ratio', 0)
        
        # 确定主要情感
        main_sentiment = "neutral"
        max_ratio = neutral_ratio
        
        if positive_ratio > max_ratio:
            main_sentiment = "positive"
            max_ratio = positive_ratio
        
        if negative_ratio > max_ratio:
            main_sentiment = "negative"
            max_ratio = negative_ratio
        
        summary_data.append({
            'ticker': ticker,
            'date': date,
            'main_sentiment': main_sentiment,
            'positive_ratio': positive_ratio,
            'neutral_ratio': neutral_ratio,
            'negative_ratio': negative_ratio,
            'positive_count': report_data['summary']['positive'],
            'neutral_count': report_data['summary']['neutral'],
            'negative_count': report_data['summary']['negative'],
        })
    
    # 创建DataFrame并保存
    if summary_data:
        df = pd.DataFrame(summary_data)
        output_file = os.path.join(output_dir, 'sentiment_summary.csv')
        df.to_csv(output_file, index=False)
        print(f"摘要CSV已保存到 {output_file}")


def main(ticker: Optional[str] = None, model_name: str = 'ProsusAI/finbert'):
    """主函数"""
    print(f"初始化FinBERT情感分析器 (模型: {model_name})...")
    analyzer = FinBertSentimentAnalyzer(model_name=model_name)
    
    print("开始分析报告...")
    results = analyze_reports(analyzer, ticker=ticker)
    
    print("保存分析结果...")
    save_analysis_results(results)
    generate_summary_csv(results)
    
    print("分析完成!")
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="分析10-K报告的情感")
    parser.add_argument("--ticker", type=str, help="股票代码筛选", default=None)
    parser.add_argument("--model", type=str, help="模型名称", default="ProsusAI/finbert")
    
    args = parser.parse_args()
    
    main(ticker=args.ticker, model_name=args.model) 