import os
import re
import sys
import glob
import nltk
from nltk.tokenize import sent_tokenize
from tqdm import tqdm
from config import *


# 改进NLTK资源安装和验证
def setup_nltk_resources():
    """确保NLTK资源正确完整下载并可用"""
    # 确保NLTK数据目录存在
    os.makedirs(NLTK_DATA_DIR, exist_ok=True)
    nltk.data.path.insert(0, NLTK_DATA_DIR)

    # 下载所有必要的资源
    required_resources = ["punkt"]

    # 首先下载基本资源
    for resource in required_resources:
        print(f"⚙ 正在下载NLTK {resource}资源...")
        nltk.download(resource, download_dir=NLTK_DATA_DIR, quiet=False)
        print(f"✓ {resource}下载完成")

    # 尝试直接下载punkt_tab资源（这是分词所必需的子资源）
    try:
        print("⚙ 正在下载punkt_tab资源...")
        # 尝试两种可能的下载方式
        try:
            nltk.download("punkt_tab", download_dir=NLTK_DATA_DIR, quiet=False)
        except:
            # 如果直接下载失败，尝试创建相应目录并下载English.pickle
            tokenizers_dir = os.path.join(
                NLTK_DATA_DIR, "tokenizers", "punkt_tab", "english"
            )
            os.makedirs(tokenizers_dir, exist_ok=True)

            # 复制已有的punkt数据
            src_dir = os.path.join(NLTK_DATA_DIR, "tokenizers", "punkt")
            if os.path.exists(src_dir):
                import shutil

                for file in os.listdir(src_dir):
                    if file.endswith(".pickle"):
                        shutil.copy2(
                            os.path.join(src_dir, file),
                            os.path.join(tokenizers_dir, file),
                        )
                print("✓ 已手动创建punkt_tab资源")

        # 验证下载结果
        test_text = "This is a test sentence. This is another sentence."
        sentences = sent_tokenize(test_text)
        if len(sentences) == 2:
            print("✓ 验证成功：分词资源可正常使用")
        else:
            print("! 警告：分词资源验证不完全，分词结果异常")
    except Exception as e:
        print(f"! 警告：资源验证失败: {e}")
        print("  将使用备用分词方法")


# 添加备用分词方法
def fallback_sentence_tokenize(text):
    """当NLTK分词失败时的备用方案"""
    # 使用正则表达式按句号、问号和感叹号分割文本
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def read_file_with_fallback_encodings(file_path):
    """尝试多种编码方式读取文件"""
    encodings = ["utf-8", "latin-1", "iso-8859-1", "windows-1252"]
    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"无法解码文件 {file_path} 使用尝试的编码: {encodings}")


def preprocess_text(text):
    """预处理文本提高可匹配性"""
    # 标准化换行符和特殊字符
    text = text.replace("\r\n", "\n").replace("′", "'").replace("'", "'")
    # 减少连续空格和特殊空白字符
    text = re.sub(r"[ \t]{2,}", " ", text)
    # 处理表格中的分隔线
    text = re.sub(r"[-–—]{3,}", " ", text)
    return text


# 清理规则
def clean_financial_text(text):
    """清理金融文本中的常见噪声"""
    # 1. 删除页眉页脚、页码
    text = re.sub(r"\n\s*\d+\s*\n", "\n", text)  # 删除单独成行的页码
    text = re.sub(r"Form 10-K.*?\n", "", text, flags=re.IGNORECASE)  # 删除表单标识

    # 2. 删除表格内的连续空格和破折号
    text = re.sub(r"[-–—]{3,}", " ", text)
    text = re.sub(r"\s{2,}", " ", text)

    # 3. 处理常见的金融报表头部
    text = re.sub(
        r"(Table of Contents|PART [IVX]+|Item \d+\.)", r"\n\1", text
    )  # 保留但增加换行

    # 4. 移除URL和邮箱
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"\S+@\S+", "", text)

    # 5. 移除括号内的引用标记，如 (1), [2]
    text = re.sub(r"\([0-9]+\)|\[[0-9]+\]", "", text)  # 修正括号表达式

    # 6. 处理换行和段落
    text = re.sub(r"\n{3,}", "\n\n", text)  # 多个连续换行替换为双换行

    # 7. 删除不必要的空白行
    text = re.sub(r"^\s*$\n", "", text, flags=re.MULTILINE)

    return text


# 检测公司并返回特定模式
def detect_company_and_get_patterns(text):
    """检测报告所属公司，返回定制的提取模式"""
    # 检测Apple公司
    if re.search(r"Apple\s+Inc\.|APPLE\s+INC\.", text, re.IGNORECASE):
        return {
            "risk_factors": r"Risk\s+Factors(.*?)(?=Item\s+[1-9]|PART\s+[IVX]|Management's\s+Discussion|$)",
            "md_and_a": r"Management['']s\s+Discussion\s+and\s+Analysis\s+of\s+Financial\s+Condition\s+and\s+Results\s+of\s+Operations(.*?)(?=Item\s+[1-9]|Quantitative\s+and\s+Qualitative|$)",
            "financial_statements": r"(?:CONSOLIDATED|Consolidated)\s+(?:FINANCIAL\s+STATEMENTS|Financial\s+Statements)(.*?)(?=Notes\s+to\s+Consolidated|$)",
        }

    # 检测Google/Alphabet公司
    if re.search(
        r"Google\s+Inc\.|GOOGLE\s+INC\.|Alphabet\s+Inc\.|ALPHABET\s+INC\.",
        text,
        re.IGNORECASE,
    ):
        return {
            "risk_factors": r"(?:RISK\s+FACTORS|Risk\s+Factors)(.*?)(?=UNRESOLVED\s+STAFF|Unresolved\s+Staff|MANAGEMENT['']S\s+DISCUSSION|Management['']s\s+Discussion|$)",
            "md_and_a": r"MANAGEMENT['']S\s+DISCUSSION\s+AND\s+ANALYSIS\s+OF\s+FINANCIAL\s+CONDITION\s+AND\s+RESULTS\s+OF\s+OPERATIONS(.*?)(?=QUANTITATIVE\s+AND\s+QUALITATIVE|Quantitative\s+and\s+Qualitative|$)",
            "financial_statements": r"(?:FINANCIAL\s+STATEMENTS\s+AND\s+SUPPLEMENTARY\s+DATA|Financial\s+Statements\s+and\s+Supplementary\s+Data)(.*?)(?=CHANGES\s+IN\s+AND\s+DISAGREEMENTS|Changes\s+in\s+and\s+Disagreements|$)",
        }

    # 检测Tesla公司
    if re.search(r"Tesla,?\s+Inc\.|TESLA,?\s+INC\.", text, re.IGNORECASE):
        return {
            "risk_factors": r"Risk\s+Factors(.*?)(?=Item\s+[1-9]|PART\s+[IVX]|Unresolved\s+Staff\s+Comments|$)",
            "md_and_a": r"Management['']s\s+Discussion\s+and\s+Analysis\s+of\s+Financial\s+Condition\s+and\s+Results\s+of\s+Operations(.*?)(?=Quantitative\s+and\s+Qualitative|$)",
            "financial_statements": r"(?:FINANCIAL\s+STATEMENTS\s+AND\s+SUPPLEMENTARY\s+DATA|Financial\s+Statements\s+and\s+Supplementary\s+Data)(.*?)(?=Item\s+[1-9]|PART\s+[IVX]|$)",
        }

    return None  # 没有识别出特定公司


def extract_sections(text):
    """提取10-K报告中的重要章节（增强版）"""
    sections = {}

    # 首先尝试特定公司的模式
    company_specific_patterns = detect_company_and_get_patterns(text)
    if company_specific_patterns:
        print("检测到特定公司格式，使用定制提取模式")
        for section_name, pattern in company_specific_patterns.items():
            try:
                matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if matches and matches.group(1) and len(matches.group(1).strip()) > 100:
                    sections[section_name] = matches.group(1).strip()
            except Exception as e:
                print(f"特定公司模式匹配错误 {section_name}: {e}")

    # 如果特定公司模式未成功，尝试通用模式
    if not sections:
        # 增强的一般性正则表达式模式
        general_patterns = {
            "risk_factors": [
                r"(?:ITEM|Item)\s*1A\.?\s*(?:[-—–]|\s)\s*(?:RISK\s*FACTORS|Risk\s*Factors)(.*?)(?=(?:ITEM|Item)\s*[1-9]|$)",
                r"RISK\s*FACTORS(.*?)(?=(?:ITEM|Item)\s*[1-9]|PART\s+[IVX]|$)",
                r"Risk\s*Factors(.*?)(?=(?:ITEM|Item)\s*[1-9]|PART\s+[IVX]|$)",
            ],
            "md_and_a": [
                r"(?:ITEM|Item)\s*7\.?\s*(?:[-—–]|\s)\s*(?:MANAGEMENT'S\s*DISCUSSION|Management's\s*Discussion)(.*?)(?=(?:ITEM|Item)\s*[1-9]|$)",
                r"MANAGEMENT'S\s*DISCUSSION\s*AND\s*ANALYSIS(.*?)(?=(?:ITEM|Item)\s*[1-9]|$)",
                r"Management's\s*Discussion\s*and\s*Analysis(.*?)(?=(?:ITEM|Item)\s*[1-9]|$)",
            ],
            "financial_statements": [
                r"(?:ITEM|Item)\s*8\.?\s*(?:[-—–]|\s)\s*(?:FINANCIAL\s*STATEMENTS|Financial\s*Statements)(.*?)(?=(?:ITEM|Item)\s*[1-9]|$)",
                r"FINANCIAL\s*STATEMENTS\s*AND\s*SUPPLEMENTARY\s*DATA(.*?)(?=(?:ITEM|Item)\s*[1-9]|$)",
                r"Financial\s*Statements\s*and\s*Supplementary\s*Data(.*?)(?=(?:ITEM|Item)\s*[1-9]|$)",
            ],
        }

        for section_name, patterns in general_patterns.items():
            for pattern in patterns:
                try:
                    matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                    if matches and len(matches.group(1).strip()) > 100:
                        sections[section_name] = matches.group(1).strip()
                        break  # 找到一个匹配就停止尝试其他模式
                except Exception as e:
                    print(f"通用模式匹配错误 {section_name}: {e}")

    # 如果仍然没有提取到章节，使用最终备用方法
    if not sections:
        sections = alternative_extraction_method(text)

    return sections


def alternative_extraction_method(text):
    """当主正则失败时使用的备用提取方法"""
    sections = {}

    # 尝试基于目录和关键字的定位方法
    toc_patterns = {
        "md_and_a": [
            r"(?:Management Discussion|MANAGEMENT DISCUSSION|MD&A)(.*?)(?=Financial Statements|FINANCIAL STATEMENTS|Item 8|ITEM 8|$)",
            r"(?:RESULTS OF OPERATIONS|Results of Operations)(.*?)(?=Financial Statements|FINANCIAL STATEMENTS|Liquidity|LIQUIDITY|$)",
        ],
        "risk_factors": [
            r"(?:RISK FACTORS|Risk Factors)(.*?)(?=Business|BUSINESS|Properties|PROPERTIES|$)",
            r"(?:factors that may affect future results|Factors That May Affect Future Results)(.*?)(?=Management|MANAGEMENT|$)",
        ],
    }

    for section_name, patterns in toc_patterns.items():
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
                if match and len(match.group(1).strip()) > 200:
                    sections[section_name] = match.group(1).strip()
                    break
            except Exception:
                pass

    # 如果还没找到，尝试查找整个部分
    if "md_and_a" not in sections:
        try:
            # 尝试定位MD&A部分的开始和结束
            start_patterns = [
                r"Management('s|'s)?\s+Discussion\s+and\s+Analysis",
                r"MANAGEMENT('S|'S)?\s+DISCUSSION\s+AND\s+ANALYSIS",
                r"Item\s+7\.\s+Management",
            ]

            end_patterns = [
                r"Item\s+7A",
                r"ITEM\s+7A",
                r"Item\s+8",
                r"ITEM\s+8",
                r"Quantitative and Qualitative",
                r"QUANTITATIVE AND QUALITATIVE",
            ]

            # 查找开始点
            start_pos = -1
            for pattern in start_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    start_pos = match.start()
                    break

            # 查找结束点
            end_pos = len(text)
            if start_pos >= 0:
                for pattern in end_patterns:
                    match = re.search(pattern, text[start_pos:], re.IGNORECASE)
                    if match:
                        end_pos = start_pos + match.start()
                        break

                # 提取内容
                if end_pos > start_pos and end_pos - start_pos > 500:
                    content = text[start_pos:end_pos].strip()
                    sections["md_and_a"] = content
        except Exception as e:
            print(f"备用提取方法出错: {e}")

    return sections


def process_sections_to_sentences(sections):
    """将章节内容分割为句子"""
    processed_sections = {}

    for section_name, content in sections.items():
        try:
            if not content or len(content) < 200:  # 跳过内容过少的章节
                continue

            # 清理文本
            cleaned_text = clean_financial_text(content)

            # 尝试使用NLTK分词，失败时使用备用方法
            try:
                sentences = sent_tokenize(cleaned_text)
            except Exception as e:
                print(f"NLTK分词失败，使用备用方法: {e}")
                sentences = fallback_sentence_tokenize(cleaned_text)

            # 过滤掉过短或不合理的句子
            filtered_sentences = [
                s.strip()
                for s in sentences
                if len(s.strip()) > 20 and len(s.strip()) < 500
            ]

            # 确保提取了足够的句子
            if len(filtered_sentences) > 5:
                processed_sections[section_name] = filtered_sentences
            else:
                print(
                    f"警告: '{section_name}' 章节提取的有效句子不足 ({len(filtered_sentences)})"
                )
        except Exception as e:
            print(f"处理章节 '{section_name}' 时出错: {str(e)}")
            processed_sections[section_name] = []

    return processed_sections


def save_debug_info(file_path, text, sections):
    """保存调试信息用于分析"""
    base_name = os.path.basename(file_path).replace(".txt", "")

    # 使用配置中的辅助函数获取路径
    preview_path = get_debug_file_path(file_path, "preview")
    sections_path = get_debug_file_path(file_path, "sections")

    # 保存原始文本前1000字符
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(text[:1000])

    # 保存提取结果
    with open(sections_path, "w", encoding="utf-8") as f:
        for name, content in sections.items():
            f.write(f"=== {name.upper()} ===\n")
            f.write(content[:500] + "\n\n")


def process_txt_files():
    """处理所有txt文件，提取并清洗关键章节"""
    # 获取所有文本文件 - 使用RAW_DATA_DIR或DATA_DIR
    txt_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.txt"))
    if not txt_files:  # 如果raw目录没有文件，尝试使用DATA_DIR
        txt_files = glob.glob(os.path.join(DATA_DIR, "*.txt"))

    print(f"找到 {len(txt_files)} 个文本文件待处理")

    # 记录成功和失败的文件
    success_count = 0
    failed_files = []

    for txt_file in tqdm(txt_files, desc="处理文件"):
        try:
            raw_text = read_file_with_fallback_encodings(txt_file)

            # 预处理文本
            preprocessed_text = preprocess_text(raw_text)

            # 提取关键章节
            sections = extract_sections(preprocessed_text)

            # 调试：保存提取信息
            save_debug_info(txt_file, preprocessed_text, sections)

            # 如果没有提取到任何章节，记录并继续
            if not sections:
                print(f"警告: '{os.path.basename(txt_file)}' 未提取到任何章节")
                failed_files.append(txt_file)
                continue

            # 处理章节为句子
            processed_sections = process_sections_to_sentences(sections)

            # 如果没有有效处理后的章节，记录并继续
            if not processed_sections:
                print(f"警告: '{os.path.basename(txt_file)}' 未能处理出有效章节句子")
                failed_files.append(txt_file)
                continue

            # 保存整体清洗后文本
            cleaned_path = get_processed_file_path(txt_file)
            with open(cleaned_path, "w", encoding="utf-8") as f:
                f.write(clean_financial_text(preprocessed_text))

            # 保存分章节的文本
            for section_name, sentences in processed_sections.items():
                if not sentences:  # 跳过空章节
                    continue

                section_path = get_processed_file_path(txt_file, section_name)
                with open(section_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(sentences))

            success_count += 1

        except Exception as e:
            print(f"处理文件 '{os.path.basename(txt_file)}' 时出错: {e}")
            failed_files.append(txt_file)

    # 输出处理结果统计
    print(f"\n处理完成: 成功 {success_count}/{len(txt_files)} 文件")
    if failed_files:
        print(f"处理失败的文件 ({len(failed_files)}):")
        for f in failed_files[:10]:  # 只显示前10个
            print(f"  - {os.path.basename(f)}")
        if len(failed_files) > 10:
            print(f"  ...以及其他 {len(failed_files)-10} 个文件")


if __name__ == "__main__":
    # 首先设置NLTK资源
    setup_nltk_resources()
    #  然后处理文件
    process_txt_files()
