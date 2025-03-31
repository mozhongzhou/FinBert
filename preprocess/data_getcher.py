# 创建新文件: data_fetcher.py
import os
from sec_edgar_downloader import Downloader
import datetime

def download_10k_reports(tickers, start_year=None, end_year=None):
    """
    自动下载指定股票代码的10-K报告
    
    参数:
    tickers - 股票代码列表或单个股票代码
    start_year - 开始年份，默认为当前年份-5
    end_year - 结束年份，默认为当前年份
    """
    # 设置下载目录
    downloader = Downloader("./data/raw")
    
    # 处理时间范围
    current_year = datetime.datetime.now().year
    start_year = start_year or current_year - 5
    end_year = end_year or current_year
    
    # 确保tickers是列表
    if isinstance(tickers, str):
        tickers = [tickers]
    
    # 下载每个股票的10-K报告
    for ticker in tickers:
        print(f"正在下载 {ticker} 的10-K报告...")
        downloader.get("10-K", ticker, after=f"{start_year}-01-01", before=f"{end_year}-12-31")
        
    print("下载完成，文件保存在 ./data/raw 目录")