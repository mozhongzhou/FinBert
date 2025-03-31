import os

# 项目根目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')

# 结果目录
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

# NLTK数据目录
NLTK_DATA_DIR = os.path.join(PROJECT_ROOT, 'resources', 'nltk_data')

# 10-K报告重要章节的关键词和标记
SECTIONS = {
    "md_and_a": [
        r"item\s*[7]\s*[\.|\:]*\s*management'?s?\s*discussion\s*and\s*analysis",
        r"management'?s?\s*discussion\s*and\s*analysis\s*of\s*financial\s*condition",
    ],
    "risk_factors": [
        r"item\s*[1]a\s*[\.|\:]*\s*risk\s*factors",
        r"risk\s*factors",
    ],
    "business": [
        r"item\s*[1]\s*[\.|\:]*\s*business",
        r"business",
    ],
    "financial_statements": [
        r"item\s*[8]\s*[\.|\:]*\s*financial\s*statements",
        r"consolidated\s*financial\s*statements",
    ],
}

# 目录初始化函数
def setup_directories():
    """确保必要的目录结构存在"""
    directories = [RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
