import os
import re
import glob
import nltk
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
import logging

from config import *

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, 'clean_10k.log')),
        logging.StreamHandler()
    ]
)

# 确保NLTK资源存在
nltk.data.path.append(NLTK_DATA_DIR)
try:
    nltk.download('punkt', download_dir=NLTK_DATA_DIR, quiet=True)
except:
    logging.warning("无法下载NLTK资源，将使用现有资源或简单分句")

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

# 章节结束标记
SECTION_END_MARKERS = [
    r"item\s*[1-9][0-9a-z]*\s*[\.|\:]", 
    r"part\s*[i,ii]{1,2}\s*[\.|\:]"
]

# 文本清理模式
CLEAN_PATTERNS = [
    (r'\s+', ' '),                       # 多个空白字符合并为一个空格
    (r'- ', ''),                         # 移除连字符+空格
    (r'\([Tt]able\s+of\s+[Cc]ontents\)', ''),  # 移除目录表标记
    (r'[Tt]able\s+of\s+[Cc]ontents', ''),      # 移除目录表标记
    (r'Page\s+\d+', ''),                 # 移除页码
    (r'\d+\s+of\s+\d+', ''),             # 移除页码格式 (X of Y)
    (r'(?<!\w)www\.\w+\.\w+(?:\.\w+)*', ''),  # 移除网址
    (r'®|©|™|℠', ''),                    # 移除商标符号
    (r'†|‡|§|¶', ''),                    # 移除特殊符号
]

# 垃圾信息特征检测
def is_boilerplate(text):
    """检测文本是否为样板文字/垃圾信息"""
    if len(text.strip()) < 20:  # 太短的文本可能无意义
        return True
        
    # 检测典型的页眉页脚和样板文字
    boilerplate_patterns = [
        r"^\s*\d+\s*$",  # 仅包含数字（页码）
        r"^(.*[Cc]onfidential.*|.*[Pp]roprietary.*)$",  # 保密/专有信息声明
        r"^.*[Cc]opyright.*\d{4}.*$",  # 版权声明
        r"^.*\([Cc]ontinued\).*$",  # "继续"文本
        r"^.*[Ff]orm\s+10-?[Kk].*$",  # 表格标签
    ]
    
    for pattern in boilerplate_patterns:
        if re.match(pattern, text):
            return True
    
    return False


def find_section_boundaries(text, section_patterns, end_patterns):
    """
    寻找章节边界，返回(开始, 结束)位置
    """
    text_lower = text.lower()
    
    # 查找章节开始
    start_pos = -1
    for pattern in section_patterns:
        match = re.search(pattern, text_lower)
        if match:
            start_pos = match.end()
            break
    
    if start_pos == -1:
        return None  # 未找到章节
    
    # 查找章节结束
    end_pos = len(text)
    for pattern in end_patterns:
        matches = list(re.finditer(pattern, text_lower[start_pos:]))
        if matches:
            # 找到的第一个结束标记
            end_pos = start_pos + matches[0].start()
            break
    
    return (start_pos, end_pos)


def clean_text(text):
    """
    清理文本，删除垃圾信息
    """
    # 应用清理模式
    for pattern, replacement in CLEAN_PATTERNS:
        text = re.sub(pattern, replacement, text)
    
    # 分割成句子并过滤垃圾信息
    try:
        sentences = nltk.sent_tokenize(text)
    except:
        # 如果NLTK分句失败，使用简单的分句规则
        sentences = [s.strip() + '.' for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
    
    # 过滤掉样板文字/垃圾句子
    clean_sentences = [s for s in sentences if not is_boilerplate(s)]
    
    return '\n'.join(clean_sentences)


def process_file(file_path):
    """处理单个10-K文本文件"""
    filename = os.path.basename(file_path)
    
    logging.info(f"处理文件: {filename}")
    
    try:
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            # 尝试不同编码
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"无法读取文件 {filename}: {e}")
            return
    except Exception as e:
        logging.error(f"处理文件 {filename} 时发生错误: {e}")
        return
        
    # 创建一个基本的清理版本
    cleaned_text = clean_text(content)
    cleaned_file = get_processed_file_path(filename)
    with open(cleaned_file, 'w', encoding='utf-8') as f:
        f.write(cleaned_text)
    
    # 提取并保存各个章节
    sections_found = {}
    for section_name, patterns in SECTIONS.items():
        boundaries = find_section_boundaries(content, patterns, SECTION_END_MARKERS)
        if boundaries:
            start_pos, end_pos = boundaries
            section_text = content[start_pos:end_pos]
            cleaned_section = clean_text(section_text)
            
            # 保存章节
            section_file = get_processed_file_path(filename, section_name)
            with open(section_file, 'w', encoding='utf-8') as f:
                f.write(cleaned_section)
            
            sections_found[section_name] = True
            logging.info(f"已提取并保存章节 {section_name}: {os.path.basename(section_file)}")
    
    # 记录处理结果
    if not sections_found:
        logging.warning(f"文件 {filename} 中未找到任何重要章节")
    
    return sections_found


def main():
    """主函数"""
    txt_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.txt"))
    if not txt_files:
        logging.warning(f"在 {RAW_DATA_DIR} 中未找到TXT文件。请先运行 pdf_to_txt.py")
        return
    
    # 使用多进程处理文件
    logging.info(f"开始处理 {len(txt_files)} 个文件")
    results = defaultdict(int)
    
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
        for result in executor.map(process_file, txt_files):
            if result:
                for section in result:
                    results[section] += 1
    
    # 输出统计信息
    logging.info("处理完成，章节提取统计:")
    for section, count in results.items():
        logging.info(f"- {section}: {count} 个文件")


if __name__ == "__main__":
    main()