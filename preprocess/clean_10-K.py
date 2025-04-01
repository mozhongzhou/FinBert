import os
import re
import sys
import glob
from bs4 import BeautifulSoup
import nltk
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('10k_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 下载必要的NLTK资源
nltk.download('punkt', quiet=True)

def extract_text_from_html(html_content):
    """从HTML内容中提取纯文本"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # 移除脚本和样式元素
        for element in soup(["script", "style"]):
            element.extract()
        text = soup.get_text()
        # 处理多余空白
        lines = (line.strip() for line in text.splitlines() if line.strip())
        text = '\n'.join(lines)
        return text
    except Exception as e:
        logging.error(f"HTML解析出错: {str(e)}")
        return ""

def clean_10k_report(file_path):
    """清理10-K报告文件"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            content = file.read()
        
        # 提取HTML部分
        html_match = re.search(r'<DOCUMENT>.*?<TEXT>(.*?)</TEXT>', content, re.DOTALL)
        html_content = html_match.group(1) if html_match else content
        
        # 提取纯文本
        cleaned_text = extract_text_from_html(html_content)
        if not cleaned_text:
            raise ValueError("无法提取有效文本")
        
        # 移除页码和页眉页脚
        cleaned_text = re.sub(r'^\s*\d+\s*$', '', cleaned_text, flags=re.MULTILINE)
        cleaned_text = re.sub(r'\n[^\n]{0,50}(?:Inc\.|Corporation|Corp\.|Company|Ltd\.)[^\n]{0,50}\n', '\n', cleaned_text, flags=re.IGNORECASE)
        # 合并多余空行
        cleaned_text = re.sub(r'\n\s*\n', '\n', cleaned_text).strip()
        
        return cleaned_text
    except Exception as e:
        logging.error(f"清理文件 {file_path} 时出错: {str(e)}")
        return ""

def extract_year(file_path, content):
    """从文件内容或路径中提取年份"""
    try:
        # 优先从文件内容提取
        year_match = re.search(r'CONFORMED PERIOD OF REPORT:\s*(\d{4})', content[:5000])
        if year_match:
            return year_match.group(1)
        # 从路径提取日期
        date_match = re.search(r'(\d{8})', file_path)
        if date_match:
            return date_match.group(1)[:4]
        # 默认值
        logging.warning(f"无法从 {file_path} 提取年份，使用默认值2000")
        return "2000"
    except Exception as e:
        logging.error(f"提取年份出错: {str(e)}")
        return "2000"

def extract_items(text):
    """提取10-K报告中的重要Item章节"""
    items = {}
    item_patterns = {
        'Item_1': r'Item\s+1[\.\-\s:]*Business(?:\s+Overview)?',
        'Item_1A': r'Item\s+1A[\.\-\s:]*Risk\s+Factors',
        'Item_7': r'Item\s+7[\.\-\s:]*Management[\'’]?s\s+Discussion(?:\s+and\s+Analysis)?',
        'Item_7A': r'Item\s+7A[\.\-\s:]*Quantitative\s+and\s+Qualitative(?:\s+Disclosures)?'
    }
    
    # 记录所有Item标题位置
    item_positions = []
    for item_key, pattern in item_patterns.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            item_positions.append((match.start(), match.group(0), item_key))
    
    # 按位置排序
    item_positions.sort(key=lambda x: x[0])
    
    # 提取章节内容
    for i, (pos, title, item_key) in enumerate(item_positions):
        end_pos = item_positions[i+1][0] if i < len(item_positions) - 1 else len(text)
        content = text[pos:end_pos].strip()
        # 清理内容，移除下一个Item标题之前的内容
        next_item = re.search(r'Item\s+\d+[A-Z]?[\.\-\s:]', content[len(title):], re.IGNORECASE)
        if next_item:
            content = content[:len(title) + next_item.start()]
        items[item_key] = content
    
    logging.info(f"提取到的章节: {list(items.keys())}")
    return items

def save_cleaned_text(ticker, year, text, items):
    """保存清理后的文本到processed目录"""
    processed_dir = os.path.join(config.PROCESSED_DATA_DIR, ticker, str(year))
    os.makedirs(processed_dir, exist_ok=True)
    
    try:
        # 保存完整文本
        with open(os.path.join(processed_dir, 'full_text.txt'), 'w', encoding='utf-8') as f:
            f.write(text)
        
        # 保存各章节
        for item_name, item_text in items.items():
            with open(os.path.join(processed_dir, f'{item_name}.txt'), 'w', encoding='utf-8') as f:
                f.write(item_text)
        
        # 提取并保存句子
        sentences = []
        for item_name in ['Item_7', 'Item_1A', 'Item_1', 'Item_7A']:
            if item_name in items:
                sentences.extend(nltk.sent_tokenize(items[item_name]))
        if not sentences:
            sentences = nltk.sent_tokenize(text)
        
        with open(os.path.join(processed_dir, 'sentences.txt'), 'w', encoding='utf-8') as f:
            for sentence in sentences:
                clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                if len(clean_sentence) >= 10 and len(clean_sentence.split()) >= 5:
                    f.write(clean_sentence + '\n')
    except Exception as e:
        logging.error(f"保存文件 {ticker}/{year} 时出错: {str(e)}")

def process_file(file_path):
    """处理单个10-K报告文件"""
    try:
        ticker = file_path.split(os.sep)[-4]
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        year = extract_year(file_path, content)
        
        logging.info(f"开始处理 {ticker} 的 {year} 年报告")
        cleaned_text = clean_10k_report(file_path)
        if not cleaned_text:
            raise ValueError("清理后的文本为空")
        
        items = extract_items(cleaned_text)
        save_cleaned_text(ticker, year, cleaned_text, items)
        logging.info(f"成功处理 {ticker} 的 {year} 年报告，提取 {len(items)} 个章节")
    except Exception as e:
        logging.error(f"处理 {file_path} 时出错: {str(e)}")

def process_all_reports():
    """处理所有下载的10-K报告"""
    raw_data_pattern = os.path.join(config.RAW_DATA_DIR, 'sec-edgar-filings', '*', '10-K', '*', 'full-submission.txt')
    report_files = glob.glob(raw_data_pattern)
    
    if not report_files:
        logging.warning(f"未找到任何10-K报告文件: {raw_data_pattern}")
        return
    
    logging.info(f"找到 {len(report_files)} 个10-K报告文件，开始处理...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(tqdm(executor.map(process_file, report_files), total=len(report_files)))

if __name__ == "__main__":
    process_all_reports()