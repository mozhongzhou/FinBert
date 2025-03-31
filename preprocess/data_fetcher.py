import os
import re
import requests
from bs4 import BeautifulSoup
from secedgar import CompanyFilings, FilingType
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, SECTIONS, setup_directories
import time
import random
# 配置日志
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_cik_from_ticker(ticker):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json"
    }
    url = "https://www.sec.gov/files/company_tickers.json"
    try:
        time.sleep(random.uniform(1, 3))  # 随机延时 1-3 秒
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        companies = response.json().values()
        for company in companies:
            if company["ticker"] == ticker.upper():
                return str(company["cik_str"]).zfill(10)
        raise ValueError(f"未找到股票代码 {ticker} 对应的 CIK")
    except Exception as e:
        raise RuntimeError(f"获取 CIK 失败: {str(e)}")

def download_10k_html(ticker, year, email):
    """下载指定年份的 10-K 报告 HTML 文件"""
    try:
        cik = get_cik_from_ticker(ticker)
        save_dir = os.path.join(RAW_DATA_DIR, ticker, str(year))
        os.makedirs(save_dir, exist_ok=True)
        
        filings = CompanyFilings(
            cik_lookup=cik,
            filing_type=FilingType.FILING_10K,
            start_date=f"{year}-01-01",
            end_date=f"{year}-12-31",
            user_agent=email
        )
        filings.save(save_dir)
        
        # 查找下载的 HTML 文件
        for root, _, files in os.walk(save_dir):
            for file in files:
                if file.endswith(".html") or file.endswith(".htm"):
                    return os.path.join(root, file)
        raise FileNotFoundError(f"未找到 {ticker} {year} 的 10-K HTML 文件")
    except Exception as e:
        logging.error(f"下载 {ticker} {year} 10-K 失败: {str(e)}")
        return None

def extract_sections(html_path):
    """从 HTML 文件中提取重要章节的文本"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    text = soup.get_text(separator=' ', strip=True)
    sections_text = {}
    
    for section, patterns in SECTIONS.items():
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = match.end()
                # 假设下一个章节开始于下一个 "item" 或文本结束
                end_pattern = r"item\s*\d+[a-z]?\s*[\.|\:]"
                end_match = re.search(end_pattern, text[start:], re.IGNORECASE)
                end = end_match.start() + start if end_match else len(text)
                sections_text[section] = text[start:end].strip()
                break
        if section not in sections_text:
            logging.warning(f"未找到 {section} 章节")
    
    return sections_text

def save_processed_data(ticker, year, sections_text):
    """将提取的章节文本保存到 processed 目录"""
    processed_dir = os.path.join(PROCESSED_DATA_DIR, ticker, str(year))
    os.makedirs(processed_dir, exist_ok=True)
    
    for section, text in sections_text.items():
        file_path = os.path.join(processed_dir, f"{section}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(text)
        logging.info(f"保存 {section} 到 {file_path}")

def process_10k(ticker, year, email):
    """处理指定公司和年份的 10-K 报告"""
    setup_directories()  # 确保目录存在
    html_path = download_10k_html(ticker, year, email)
    if html_path:
        sections_text = extract_sections(html_path)
        save_processed_data(ticker, year, sections_text)
        logging.info(f"处理完成: {ticker} {year}")
    else:
        logging.warning(f"跳过 {ticker} {year}，因下载失败")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="自动化下载和处理 10-K 报告")
    parser.add_argument("--email", required=True, help="你的邮箱（用于 SEC EDGAR）")
    parser.add_argument("--ticker", required=True, nargs="+", help="股票代码列表（如 AAPL MSFT）")
    parser.add_argument("--year", type=int, required=True, help="年份")
    args = parser.parse_args()
    
    for ticker in args.ticker:
        process_10k(ticker, args.year, args.email)