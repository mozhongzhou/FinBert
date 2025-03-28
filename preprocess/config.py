import os
from pathlib import Path

# 基本路径设置
BASE_DIR = Path(__file__).parent  # preprocess目录
PROJECT_ROOT = BASE_DIR.parent  # 项目根目录

# 数据目录结构（移动到根目录）
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
DEBUG_DIR = os.path.join(DATA_DIR, "debug")

# NLTK资源目录（移动到根目录的resources）
RESOURCES_DIR = os.path.join(PROJECT_ROOT, "resources")
NLTK_DATA_DIR = os.path.join(RESOURCES_DIR, "nltk_data")

# 其他输出目录
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
MODEL_DIR = os.path.join(PROJECT_ROOT, "models")


# 确保所有必要的目录都存在
def ensure_directories():
    """创建所有配置的目录"""
    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        DEBUG_DIR,
        RESOURCES_DIR,
        NLTK_DATA_DIR,
        RESULTS_DIR,
        LOGS_DIR,
        MODEL_DIR,
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"目录已确认: {directory}")


# 构建完整路径的助手函数
def get_processed_file_path(filename, section=None):
    """获取处理后文件的路径"""
    base_name = os.path.basename(filename).replace(".txt", "")
    if section:
        return os.path.join(PROCESSED_DATA_DIR, f"{base_name}_{section}.txt")
    return os.path.join(PROCESSED_DATA_DIR, f"{base_name}_cleaned.txt")


def get_debug_file_path(filename, debug_type):
    """获取调试文件的路径"""
    base_name = os.path.basename(filename).replace(".txt", "")
    return os.path.join(DEBUG_DIR, f"{base_name}_{debug_type}.txt")


# 在导入模块时自动创建目录
ensure_directories()
