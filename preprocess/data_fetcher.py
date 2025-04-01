import argparse
from sec_edgar_downloader import Downloader
import sys
import os

# 添加项目根目录到路径，以便导入config模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def download_10k_reports(email, user_agent=None):
    """
    下载指定股票的10-K年报
    
    参数:
        email (str): SEC要求的用户邮箱
        user_agent (str, optional): 用户代理标识
    """
    if user_agent is None:
        user_agent = f"FinBert Data Fetcher ({email})"
    
    # 初始化下载器
    dl = Downloader(email, user_agent, config.RAW_DATA_DIR)
    
    # 遍历所有股票代码，下载对应的10-K报告
    for ticker in config.TICKERS:
        print(f"正在下载 {ticker} 的10-K报告...")
        try:
            dl.get("10-K", ticker, 
                   after=config.START_DATE, 
                   before=config.END_DATE)
            print(f"{ticker} 的10-K报告下载完成")
        except Exception as e:
            print(f"下载 {ticker} 的10-K报告时出错: {str(e)}")
    
    print("所有下载任务已完成！")

if __name__ == "__main__":
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='下载SEC EDGAR中的10-K年报')
    parser.add_argument('--email', type=str, required=True, 
                        help='SEC要求的用户邮箱地址')
    parser.add_argument('--user-agent', type=str, 
                        help='用户代理标识（可选）')
    
    args = parser.parse_args()
    
    # 调用下载函数
    download_10k_reports(args.email, args.user_agent)