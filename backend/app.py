import os
import uvicorn
import logging
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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="FinBert金融报告分析API",
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
    """应用启动时加载模型和检查目录"""
    global analyzer
    
    # 检查必要的目录结构
    required_dirs = [PROCESSED_DATA_DIR, RESULTS_DIR]
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"创建目录: {directory}")
        else:
            logger.info(f"目录已存在: {directory}")
    
    # 加载模型
    try:
        analyzer = FinBertSentimentAnalyzer(model_name="ProsusAI/finbert")
        logger.info("FinBERT模型加载成功")
    except Exception as e:
        logger.error(f"模型加载失败: {str(e)}")


@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "model_loaded": analyzer is not None}


@app.get("/api/tickers")
async def get_tickers():
    """获取所有可用的股票代码"""
    try:
        # 扫描processed目录寻找所有公司文件夹
        company_dirs = glob.glob(os.path.join(PROCESSED_DATA_DIR, "*"))
        company_dirs = [d for d in company_dirs if os.path.isdir(d)]
        
        tickers = [os.path.basename(d) for d in company_dirs]
        logger.info(f"找到 {len(tickers)} 个股票代码")
        
        return {"tickers": sorted(tickers)}
    except Exception as e:
        logger.error(f"获取股票代码时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取股票代码时出错: {str(e)}")


@app.get("/api/reports")
async def get_reports(ticker: Optional[str] = None):
    """获取所有可用的报告列表"""
    try:
        reports = []
        
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
            
            for year_dir in year_dirs:
                year_value = os.path.basename(year_dir)
                
                # 确定可用的章节
                sections = []
                for item_name in ["Item_1", "Item_1A", "Item_7", "Item_7A"]:
                    item_file = os.path.join(year_dir, f"{item_name}.txt")
                    if os.path.exists(item_file) and os.path.getsize(item_file) > 0:
                        sections.append(item_name)
                
                # 只有当至少有一个章节可用时才添加报告
                if sections:
                    reports.append({
                        "ticker": ticker_name,
                        "date": year_value,
                        "sections": sections
                    })
        
        logger.info(f"找到 {len(reports)} 个报告")
        return {"reports": reports}
    except Exception as e:
        logger.error(f"获取报告列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取报告列表时出错: {str(e)}")


@app.get("/api/report/{ticker}/{date}")
async def get_report_data(ticker: str, date: str, analyze: bool = False):
    """
    获取特定报告的详细数据
    
    Args:
        ticker: 股票代码
        date: 报告日期
        analyze: 是否强制重新分析 (默认False)
    """
    try:
        report_key = f"{ticker}_{date}"
        logger.info(f"获取报告数据: {report_key}")
        
        # 检查分析结果是否已存在
        result_file = os.path.join(RESULTS_DIR, f"{report_key}_analysis.json")
        
        if os.path.exists(result_file) and not analyze:
            # 读取已有的分析结果
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"从文件加载报告数据: {report_key}")
                    # 检查数据结构是否符合API要求
                    if 'sections' not in data:
                        logger.warning(f"报告数据格式不符合要求，将重新分析: {report_key}")
                        analyze = True
                    else:
                        return data
            except json.JSONDecodeError:
                logger.error(f"分析结果文件 {result_file} 格式错误，将重新分析")
                analyze = True
        
        # 如果结果不存在或需要重新分析
        if analyzer is None:
            raise HTTPException(status_code=500, detail="模型未加载，无法进行实时分析")
        
        logger.info(f"开始实时分析报告: {report_key}")
        
        # 加载报告文本
        processed_dir = os.path.join(PROCESSED_DATA_DIR, ticker, date)
        
        if not os.path.exists(processed_dir):
            raise HTTPException(status_code=404, detail=f"未找到处理后的报告: {report_key}")
        
        # 读取所有章节文件
        sections_content = {}
        for item_name in ["Item_1", "Item_1A", "Item_7", "Item_7A"]:
            item_file = os.path.join(processed_dir, f"{item_name}.txt")
            if os.path.exists(item_file) and os.path.getsize(item_file) > 0:
                try:
                    with open(item_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                        if content and len(content.strip()) > 10:  # 过滤空文件
                            sections_content[item_name] = content
                except Exception as e:
                    logger.error(f"读取文件 {item_file} 出错: {str(e)}")
        
        if not sections_content:
            raise HTTPException(status_code=404, detail=f"未找到有效的章节内容: {report_key}")
        
        # 使用新增的章节分析方法
        analysis_result = analyzer.analyze_report_sections(sections_content)
        
        # 添加报告基本信息
        result = {
            'ticker': ticker,
            'date': date,
            'summary': analysis_result['summary'],
            'sections': analysis_result['sections']
        }
        
        # 保存结果
        os.makedirs(RESULTS_DIR, exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析完成并保存: {report_key}")
        return result
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"获取报告数据时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取报告数据时出错: {str(e)}")


@app.get("/api/summary")
async def get_summary(ticker: Optional[str] = None):
    """获取所有报告的情感分析摘要"""
    try:
        # 直接从分析结果生成摘要
        summary_data = []
        
        # 查找所有分析结果
        result_files = glob.glob(os.path.join(RESULTS_DIR, "*_analysis.json"))
        
        for result_file in result_files:
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if not isinstance(data, dict) or 'ticker' not in data or 'date' not in data:
                    continue
                
                # 如果指定了ticker，跳过不匹配的
                if ticker and data['ticker'] != ticker:
                    continue
                
                # 计算主要情感
                if 'summary' in data:
                    summary = data['summary']
                    
                    # 确定主要情感
                    main_sentiment = "neutral"
                    if summary.get('positive_ratio', 0) > summary.get('neutral_ratio', 0) and summary.get('positive_ratio', 0) > summary.get('negative_ratio', 0):
                        main_sentiment = "positive"
                    elif summary.get('negative_ratio', 0) > summary.get('neutral_ratio', 0) and summary.get('negative_ratio', 0) > summary.get('positive_ratio', 0):
                        main_sentiment = "negative"
                    
                    summary_data.append({
                        'ticker': data['ticker'],
                        'date': data['date'],
                        'main_sentiment': main_sentiment,
                        'positive_ratio': summary.get('positive_ratio', 0),
                        'neutral_ratio': summary.get('neutral_ratio', 0),
                        'negative_ratio': summary.get('negative_ratio', 0),
                        'positive_count': summary.get('positive_count', 0),
                        'neutral_count': summary.get('neutral_count', 0),
                        'negative_count': summary.get('negative_count', 0)
                    })
            except Exception as e:
                logger.error(f"处理结果文件 {result_file} 时出错: {str(e)}")
        
        # 保存摘要
        if summary_data:
            summary_file = os.path.join(RESULTS_DIR, "sentiment_summary.csv")
            df = pd.DataFrame(summary_data)
            df.to_csv(summary_file, index=False, encoding='utf-8')
        
        logger.info(f"返回 {len(summary_data)} 条摘要数据")
        return {"summary": summary_data}
        
    except Exception as e:
        logger.error(f"获取摘要数据时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取摘要数据时出错: {str(e)}")


@app.get("/api/report/{ticker}/{date}/section/{section}")
async def get_section_data(ticker: str, date: str, section: str):
    """获取特定章节的详细数据"""
    try:
        report_key = f"{ticker}_{date}"
        logger.info(f"获取章节数据: {report_key}/{section}")
        
        # 从完整报告中提取章节数据
        report_data = await get_report_data(ticker, date)
        
        if section not in report_data.get("sections", {}):
            raise HTTPException(status_code=404, detail=f"未找到章节: {section}")
        
        return {
            "section": section,
            "data": report_data["sections"][section]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节数据时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取章节数据时出错: {str(e)}")


@app.get("/api/analyze-text")
async def analyze_text(text: str):
    """分析单个文本的情感"""
    try:
        if not text or len(text.strip()) < 5:
            raise HTTPException(status_code=400, detail="文本过短，请提供更长的文本")
            
        if analyzer is None:
            raise HTTPException(status_code=500, detail="模型未加载，无法进行分析")
            
        # 进行情感分析
        result = analyzer.analyze_text(text)
        
        logger.info(f"分析单个文本: '{text[:50]}...'")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析文本时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分析文本时出错: {str(e)}")


# 如果直接运行此文件
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)