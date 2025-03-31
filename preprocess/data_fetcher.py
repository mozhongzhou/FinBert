import os
import argparse
import logging
from datetime import datetime
from sec_edgar_downloader import Downloader
import tempfile
import glob
import shutil
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "data_fetcher.log")) if os.path.exists("logs") else logging.StreamHandler(),
        logging.StreamHandler()
    ]
)

def setup_directories():
    """确保必要的目录结构存在"""
    directories = ["data/raw", "data/processed", "results", "logs"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def download_10k_reports(tickers, start_year=None, end_year=None, output_dir="data/raw"):
    """
    自动下载指定股票代码的10-K报告
    
    参数:
    tickers - 股票代码列表或单个股票代码
    start_year - 开始年份，默认为当前年份-5
    end_year - 结束年份，默认为当前年份
    output_dir - 输出目录
    """
    # 设置下载目录
    temp_dir = tempfile.mkdtemp()
    downloader = Downloader(temp_dir)
    
    # 处理时间范围
    current_year = datetime.now().year
    start_year = start_year or current_year - 5
    end_year = end_year or current_year
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 确保tickers是列表
    if isinstance(tickers, str):
        tickers = [tickers]
    
    success_count = 0
    total_count = 0
    
    # 下载每个股票的10-K报告
    for ticker in tickers:
        ticker = ticker.upper()
        logging.info(f"正在下载 {ticker} 的10-K报告 ({start_year}-{end_year})...")
        
        try:
            # 下载10-K报告
            dl_result = downloader.get("10-K", ticker, after=f"{start_year}-01-01", before=f"{end_year}-12-31")
            
            if not dl_result.file_count:
                logging.warning(f"未找到 {ticker} 的10-K报告")
                continue
                
            logging.info(f"下载了 {dl_result.file_count} 个 {ticker} 的文件")
            total_count += dl_result.file_count
            
            # 处理下载的文件
            downloaded_files = glob.glob(os.path.join(temp_dir, "sec-edgar-filings", ticker, "10-K", "*", "full-submission.txt"))
            
            for file_path in downloaded_files:
                # 提取文件日期
                match = re.search(r"/(\d{8})_", file_path)
                if match:
                    file_date = match.group(1)
                    new_filename = f"{ticker}_10-K_{file_date}.txt"
                    destination = os.path.join(output_dir, new_filename)
                    
                    # 复制并重命名文件
                    shutil.copy2(file_path, destination)
                    logging.info(f"保存文件: {new_filename}")
                    success_count += 1
        
        except Exception as e:
            logging.error(f"下载 {ticker} 的10-K报告时出错: {str(e)}")
    
    # 清理临时目录
    shutil.rmtree(temp_dir)
    
    logging.info(f"下载完成: 成功获取 {success_count}/{total_count} 个文件")
    logging.info(f"文件保存在 {os.path.abspath(output_dir)}")
    
    return success_count

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="下载公司10-K年报")
    parser.add_argument("--ticker", nargs="+", required=True, help="股票代码，可以提供多个")
    parser.add_argument("--start_year", type=int, help="开始年份")
    parser.add_argument("--end_year", type=int, help="结束年份")
    parser.add_argument("--output_dir", default="data/raw", help="输出目录")
    
    args = parser.parse_args()
    
    # 确保目录结构
    setup_directories()
    
    # 下载报告
    download_10k_reports(
        args.ticker,
        start_year=args.start_year,
        end_year=args.end_year,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main() 