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
    增强版：使用多种模式匹配和启发式方法来提高准确率
    """
    text_lower = text.lower()
    
    # 查找章节开始
    start_pos = -1
    start_match = None
    
    # 尝试使用精确模式匹配
    for pattern in section_patterns:
        matches = list(re.finditer(pattern, text_lower))
        if matches:
            # 多个匹配时取最合适的一个（通常是第一个，但有时需要更复杂的判断）
            # 例如，正文内容引用的时候也会出现"Item 1A. Risk Factors"，但这些不是章节标题
            for match in matches:
                # 检查上下文判断是否为章节标题（例如，前面有换行，后面也有换行）
                context_start = max(0, match.start() - 50)
                context_end = min(len(text_lower), match.end() + 50)
                context = text_lower[context_start:context_end]
                
                # 判断是否可能是章节标题（检查是否位于行首或前面有明显分隔）
                if '\n' in context[:50] and ('\n' in context[-50:] or '.' in context[-50:]):
                    start_match = match
                    start_pos = match.end()
                    break
            
            if start_pos != -1:
                break
    
    # 如果精确匹配失败，尝试使用更宽松的模式
    if start_pos == -1:
        # 创建更宽松的模式
        relaxed_patterns = []
        for pattern in section_patterns:
            # 移除模式中的空格限制
            relaxed = pattern.replace(r"\s*", r"\s+")
            relaxed_patterns.append(relaxed)
            
            # 仅匹配核心关键词
            core_keywords = re.sub(r"[\(\)\\\.|\:\?\s\*\+]+", ".*", pattern)
            relaxed_patterns.append(core_keywords)
        
        # 使用宽松模式再次尝试
        for pattern in relaxed_patterns:
            match = re.search(pattern, text_lower)
            if match:
                start_pos = match.end()
                start_match = match
                break
    
    if start_pos == -1:
        return None  # 未找到章节
    
    # 查找章节结束
    end_pos = len(text)
    
    # 尝试查找下一个章节标题作为当前章节的结束
    for pattern in end_patterns:
        matches = list(re.finditer(pattern, text_lower[start_pos:]))
        if matches:
            # 验证匹配是否为有效的章节标题（不是正文中的引用）
            for match in matches:
                match_pos = start_pos + match.start()
                # 检查上下文
                context_start = max(0, match_pos - 30)
                context_end = min(len(text_lower), match_pos + 30)
                context = text_lower[context_start:context_end]
                
                # 判断是否是章节标题而不是引用
                if '\n' in context[:30]:
                    end_pos = match_pos
                    break
            
            if end_pos != len(text):
                break
    
    # 如果找不到明确的结束标记，尝试使用启发式方法找到合理的结束位置
    if end_pos == len(text):
        # 查找可能表示章节结束的模式，如连续多个空行
        end_candidates = re.finditer(r"\n\s*\n\s*\n", text_lower[start_pos:])
        for end_match in end_candidates:
            # 查看后面是否紧跟着可能是标题的文本
            potential_end = start_pos + end_match.end()
            next_50_chars = text_lower[potential_end:potential_end+50]
            if re.search(r"(item|part)\s+[0-9ivx]+", next_50_chars, re.IGNORECASE):
                end_pos = potential_end
                break
    
    # 添加额外的日志用于调试
    extracted_text = text[start_pos:end_pos]
    logging.debug(f"提取章节: 从位置 {start_pos} 到 {end_pos}")
    logging.debug(f"章节开始: {text[start_pos:start_pos+100]}...")
    logging.debug(f"章节结束: ...{text[end_pos-100:end_pos]}")
    
    # 检查提取的文本是否合理（至少包含几段文字）
    if len(re.findall(r"\n\n", extracted_text)) < 2 and len(extracted_text.split()) < 100:
        logging.warning(f"提取的章节可能不完整: 仅包含 {len(extracted_text.split())} 个词")
        
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
    
    # 先在整个文档中寻找章节标记
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
    
    # 如果未找到任何章节，尝试搜索整个文档并匹配更多可能的模式
    if not sections_found:
        logging.warning(f"文件 {filename} 中未找到标准章节格式，尝试使用备用方法")
        
        # 尝试使用更广泛的搜索
        for section_name, patterns in SECTIONS.items():
            # 创建更宽松的搜索模式
            broad_patterns = patterns.copy()
            # 添加更简单的模式 - 仅核心关键词
            for pattern in patterns:
                simplified = re.sub(r"(item|part)\s*[0-9ivx]+[a-z]*\s*[\.|\:]*\s*", "", pattern)
                if simplified and simplified not in patterns:
                    broad_patterns.append(simplified)
            
            boundaries = find_section_boundaries(content, broad_patterns, SECTION_END_MARKERS)
            if boundaries:
                start_pos, end_pos = boundaries
                section_text = content[start_pos:end_pos]
                cleaned_section = clean_text(section_text)
                
                # 保存章节
                section_file = get_processed_file_path(filename, section_name)
                with open(section_file, 'w', encoding='utf-8') as f:
                    f.write(cleaned_section)
                
                sections_found[section_name] = True
                logging.info(f"已使用备用方法提取并保存章节 {section_name}")
    
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