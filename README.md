# FinBert 金融报告情感分析项目

本项目利用金融领域的预训练模型（FinBERT）对 10-K 年报进行情感分析，判断报告中的句子是积极（利好）、中性还是消极（利空），并给出判断的置信度。通过 GPT 模型为 FinBERT 分析结果提供专业解释，并使用 Vue3+TypeScript+ECharts 开发可视化 BI 界面，使用户能够交互查看分析结果。

## 项目特点

- 自动获取 SEC EDGAR 数据库中的 10-K 年报
- 智能清洗和处理 10-K 文本，提取关键章节
- 使用 FinBERT 金融领域预训练模型进行情感分析
- 集成 GPT 模型提供专业金融解释
- 前端可视化界面显示带颜色标记的报告内容

## 项目结构

```
FinBert/
├── data/                  # 数据目录
│   ├── raw/               # 原始10-K报告
│   └── processed/         # 处理后的文本文件
├── models/                # 存放模型文件
├── preprocess/            # 预处理脚本
│   ├── config.py          # 配置文件
│   ├── data_fetcher.py    # SEC EDGAR数据获取
│   ├── pdf_to_txt.py      # PDF转TXT
│   └── clean_10-K.py      # 清洗10-K报告文本
├── sentiment_analysis/    # 情感分析模块
│   ├── model.py           # FinBERT模型定义
│   ├── predict.py         # 情感分析预测
│   └── gpt_explainer.py   # GPT解释器
├── backend/               # 后端API
│   └── app.py             # FastAPI应用
├── frontend/              # Vue3前端
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── views/         # 页面视图
│   │   ├── store/         # Pinia状态管理
│   │   └── router/        # 路由配置
├── results/               # 分析结果
└── README.md              # 项目说明
```

## 使用流程

### 1. 环境配置

```bash
# 克隆项目
git clone https://github.com/your-username/FinBert.git
cd FinBert

# 创建目录
mkdir -p data/raw data/processed results

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据获取与预处理

```bash
# 自动从SEC EDGAR获取10-K报告
python preprocess/data_fetcher.py --email "2014160588@qq.com" --ticker AAPL MSFT --year 2023

# 或者手动准备PDF文件，转换为文本
python preprocess/pdf_to_txt.py

# 清洗文本并提取关键章节
python preprocess/clean_10-K.py
```

### 3. 情感分析与解释

```bash
# 使用FinBERT进行基础情感分析
python -m sentiment_analysis.predict --ticker AAPL

# 使用GPT模型添加解释性分析 (需要OpenAI API密钥)
export OPENAI_API_KEY=your_api_key  # Linux/MacOS
# 或 set OPENAI_API_KEY=your_api_key  # Windows
python -m sentiment_analysis.gpt_explainer --ticker AAPL --gpt_model gpt-3.5-turbo
```

### 4. 启动应用

```bash
# 启动后端
cd backend
uvicorn app:app --reload

# 启动前端
cd frontend
npm install
npm run dev
```

## 技术栈

- **数据获取**: SEC EDGAR API, sec-edgar-downloader
- **预处理**: Python, NLTK, 正则表达式
- **情感分析**: FinBERT, Transformers, PyTorch
- **解释生成**: OpenAI GPT API
- **后端 API**: FastAPI
- **前端框架**: Vue 3, TypeScript, Pinia
- **数据可视化**: ECharts

## 核心功能

### 1. 数据获取与清洗

自动下载 10-K 报告并提取关键章节，支持多种格式处理。

### 2. 情感分析

使用 FinBERT 模型分析财报中每个句子的情感倾向，提供置信度评分。

### 3. GPT 解释器

为重要的情感分析结果提供专业的 AI 解释，帮助理解文本含义。

### 4. 可视化界面

- 情感标记显示：正面(绿色)、中性(灰色)、负面(红色)
- 点击句子查看详细分析和 GPT 解释
- 章节级别和报告级别的情感统计
