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

def load_processed_files(ticker: Optional[str] = None, year: Optional[str] = None) -> Dict[str, Dict]:
    """
    加载处理后的文本文件
    
    Args:
        ticker: 可选的股票代码筛选
        year: 可选的年份筛选
        
    Returns:
        按公司和报告日期组织的文本字典
    """
    files_dict = {}
    
    # 扫描processed目录寻找所有公司文件夹
    company_dirs = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*"))
    company_dirs = [d for d in company_dirs if os.path.isdir(d)]
    
    # 如果指定了股票代码，只处理对应公司
    if ticker:
        company_dirs = [d for d in company_dirs if os.path.basename(d) == ticker]
    
    for company_dir in company_dirs:
        ticker_name = os.path.basename(company_dir)
        # 获取该公司的所有年份目录
        year_dirs = glob.glob(os.path.join(company_dir, "*"))
        year_dirs = [d for d in year_dirs if os.path.isdir(d)]
        
        # 如果指定了年份，只处理对应年份
        if year:
            year_dirs = [d for d in year_dirs if os.path.basename(d) == year]
        
        for year_dir in year_dirs:
            year_value = os.path.basename(year_dir)
            report_key = f"{ticker_name}_{year_value}"
            
            # 查找Items文件
            items = {}
            sentences_file = os.path.join(year_dir, "sentences.txt")
            
            # 加载Item文件内容
            for item_name in ["Item_1", "Item_1A", "Item_7", "Item_7A"]:
                item_file = os.path.join(year_dir, f"{item_name}.txt")
                if os.path.exists(item_file):
                    try:
                        with open(item_file, 'r', encoding='utf-8', errors='replace') as f:
                            items[item_name] = f.read()
                    except Exception as e:
                        print(f"读取文件 {item_file} 出错: {e}")
            
            # 加载sentences文件
            sentences = []
            if os.path.exists(sentences_file):
                try:
                    with open(sentences_file, 'r', encoding='utf-8', errors='replace') as f:
                        sentences = [line.strip() for line in f if line.strip()]
                except Exception as e:
                    print(f"读取文件 {sentences_file} 出错: {e}")
            
            files_dict[report_key] = {
                'items': items,
                'sentences': sentences
            }
    
    return files_dict
def analyze_reports(analyzer, ticker: Optional[str] = None, year: Optional[str] = None, batch_size: int = 8) -> Dict:
    """
    分析报告文本的情感
    
    Args:
        analyzer: 情感分析器实例
        ticker: 可选的股票代码筛选
        year: 可选的年份筛选
        batch_size: 批处理大小
        
    Returns:
        分析结果字典
    """
    # 加载文本文件
    files_dict = load_processed_files(ticker, year)
    
    results = {}
    
    # 对每个报告进行分析
    for report_key, report_data in tqdm(files_dict.items(), desc="分析报告"):
        report_results = {
            'summary': {'positive': 0, 'neutral': 0, 'negative': 0},
            'items': {}
        }
        
        total_sentences = 0
        
        # 首先分析句子文件
        sentences = report_data['sentences']
        if sentences:
            sentence_results = analyzer.analyze_batch(sentences, batch_size)
            
            # 保存句子分析结果
            report_results['sentences'] = sentence_results
            
            # 更新总结
            for result in sentence_results:
                label = result['label']
                report_results['summary'][label] += 1
                total_sentences += 1
        
        # 分析各个Item章节
        for item_name, item_text in report_data['items'].items():
            if not item_text.strip():
                continue
            
            # 直接分析整个章节
            item_result = analyzer.analyze_text(item_text)
            
            # 保存章节结果
            report_results['items'][item_name] = item_result
        
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

def main(ticker: Optional[str] = None, year: Optional[str] = None, model_name: str = 'ProsusAI/finbert'):
    """主函数"""
    print(f"初始化FinBERT情感分析器 (模型: {model_name})...")
    analyzer = FinBertSentimentAnalyzer(model_name=model_name)
    
    print("开始分析报告...")
    results = analyze_reports(analyzer, ticker=ticker, year=year)
    
    print("保存分析结果...")
    save_analysis_results(results)
    generate_summary_csv(results)
    
    print("分析完成!")
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="分析10-K报告的情感")
    parser.add_argument("--ticker", type=str, help="股票代码筛选", default=None)
    parser.add_argument("--year", type=str, help="年份筛选", default=None)
    parser.add_argument("--model", type=str, help="模型名称", default="ProsusAI/finbert")
    
    args = parser.parse_args()
    
    main(ticker=args.ticker, year=args.year, model_name=args.model)