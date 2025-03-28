from PyPDF2 import PdfReader
import os
import glob
from concurrent.futures import ProcessPoolExecutor


from config import *

directory = RAW_DATA_DIR


def process_pdf(pdf_path):
    filename = os.path.basename(pdf_path)
    txt_path = os.path.join(directory, filename.replace(".pdf", ".txt"))

    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved {txt_path}")
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")


if __name__ == "__main__":
    # 获取目录中所有PDF文件
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    # 获取 CPU 核心数
    cpu_count = os.cpu_count()
    # 设置进程池大小（例如 CPU 密集型任务）
    max_workers = cpu_count
    # 使用多进程执行
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        list(executor.map(process_pdf, pdf_files))
