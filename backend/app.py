import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import json
import glob
from typing import List, Dict, Optional
import pandas as pd

# 导入项目配置
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from preprocess.config import *
from sentiment_analysis.model import FinBertSentimentAnalyzer
from sentiment_analysis.predict import analyze_reports

# 创建FastAPI应用
app = FastAPI(
    title="金融报告分析API",
    description="提供10-K金融报告情感分析的API服务",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化情感分析模型
analyzer = None


@app.on_event("startup")
async def startup_event():
    """应用启动时加载模型"""
    global analyzer
    try:
        analyzer = FinBertSentimentAnalyzer(model_name="ProsusAI/finbert")
    except Exception as e:
        print(f"模型加载失败: {e}")


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "model_loaded": analyzer is not None}


@app.get("/api/tickers")
async def get_tickers():
    """获取所有可用的股票代码"""
    # 从处理后的文件中提取股票代码
    files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*.txt"))
    tickers = set()
    
    for file in files:
        filename = os.path.basename(file)
        parts = filename.split('_')
        if len(parts) >= 1:
            tickers.add(parts[0])
    
    return {"tickers": sorted(list(tickers))}


@app.get("/api/reports")
async def get_reports(ticker: Optional[str] = None):
    """获取所有可用的报告列表"""
    # 从处理后的文件中提取报告信息
    files = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*.txt"))
    reports = {}
    
    for file in files:
        filename = os.path.basename(file)
        parts = filename.split('_')
        if len(parts) >= 3:
            file_ticker = parts[0]
            
            # 如果指定了ticker且不匹配，则跳过
            if ticker and ticker != file_ticker:
                continue
                
            date = parts[2]
            report_key = f"{file_ticker}_{date}"
            
            if report_key not in reports:
                reports[report_key] = {
                    "ticker": file_ticker,
                    "date": date,
                    "sections": []
                }
            
            # 提取章节信息
            if len(parts) >= 4:
                section = '_'.join(parts[3:]).replace('.txt', '')
                if section not in reports[report_key]["sections"]:
                    reports[report_key]["sections"].append(section)
    
    return {"reports": list(reports.values())}


@app.get("/api/reports/{ticker}/{date}/analysis")
async def get_report_analysis(ticker: str, date: str, with_explanations: bool = False):
    """获取特定报告的情感分析结果"""
    report_key = f"{ticker}_{date}"
    
    if with_explanations:
        # 尝试加载带GPT解释的结果
        try:
            results_file = os.path.join(RESULTS_DIR, f"{ticker}_with_explanations.json")
            if not os.path.exists(results_file):
                results_file = os.path.join(RESULTS_DIR, f"all_with_explanations.json")
                
            with open(results_file, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
                
            if report_key in all_results:
                return {"analysis": all_results[report_key]}
        except Exception as e:
            print(f"加载GPT解释结果出错: {e}")
            # 如果加载GPT解释结果出错，回退到普通结果
    
    # 加载普通分析结果
    try:
        results_file = os.path.join(RESULTS_DIR, f"{ticker}_sentiment.json")
        if not os.path.exists(results_file):
            results_file = os.path.join(RESULTS_DIR, "all_sentiment.json")
            
        with open(results_file, 'r', encoding='utf-8') as f:
            all_results = json.load(f)
            
        if report_key in all_results:
            return {"analysis": all_results[report_key]}
        else:
            raise HTTPException(status_code=404, detail=f"未找到 {report_key} 的分析结果")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分析结果出错: {str(e)}")


@app.get("/api/report/{ticker}/{date}")
async def get_report_data(ticker: str, date: str):
    """获取特定报告的详细数据"""
    report_key = f"{ticker}_{date}"
    
    # 检查分析结果是否已存在
    result_file = os.path.join(RESULTS_DIR, f"{report_key}_analysis.json")
    
    if os.path.exists(result_file):
        # 读取已有的分析结果
        with open(result_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 如果结果不存在，进行实时分析
    if analyzer is None:
        raise HTTPException(status_code=500, detail="模型未加载，无法进行实时分析")
    
    # 执行分析
    results = analyze_reports(analyzer, ticker=ticker)
    
    if report_key in results:
        return results[report_key]
    else:
        raise HTTPException(status_code=404, detail=f"未找到报告 {report_key} 的数据")


@app.get("/api/summary")
async def get_summary(ticker: Optional[str] = None):
    """获取所有报告的情感分析摘要"""
    summary_file = os.path.join(RESULTS_DIR, "sentiment_summary.csv")
    
    if os.path.exists(summary_file):
        try:
            df = pd.read_csv(summary_file)
            
            # 如果指定了ticker，进行过滤
            if ticker:
                df = df[df['ticker'] == ticker]
                
            return {"summary": df.to_dict(orient='records')}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取摘要数据出错: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail="摘要数据不存在，请先运行分析")


@app.get("/api/report/{ticker}/{date}/section/{section}")
async def get_section_data(ticker: str, date: str, section: str):
    """获取特定报告章节的句子及其情感分析"""
    report_key = f"{ticker}_{date}"
    
    # 检查分析结果是否已存在
    result_file = os.path.join(RESULTS_DIR, f"{report_key}_analysis.json")
    
    if os.path.exists(result_file):
        try:
            # 读取已有的分析结果
            with open(result_file, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            if 'sections' in report_data and section in report_data['sections']:
                return report_data['sections'][section]
            else:
                raise HTTPException(status_code=404, detail=f"未找到章节 {section} 的数据")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"读取章节数据出错: {str(e)}")
    else:
        raise HTTPException(status_code=404, detail=f"未找到报告 {report_key} 的分析结果")


# 配置静态文件服务
@app.on_event("startup")
async def configure_static_files():
    """配置静态文件服务"""
    static_dir = os.path.join(PROJECT_ROOT, "frontend", "dist")
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# 如果直接运行此文件
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 