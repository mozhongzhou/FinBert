# FinBert - 金融报告情感分析系统

本项目是一个基于 FinBERT 模型的金融报告情感分析系统，专注于对 10-K 年报进行情感分析，将文本内容分类为积极（利好）、中性或消极（利空）情感，并提供直观的可视化界面展示分析结果。

## 项目概述

FinBert 系统自动提取和分析 10-K 报告中的关键章节，如管理层讨论与分析(MD&A)、风险因素等，使用专为金融领域训练的 BERT 模型判断情感倾向，并通过 Web 界面呈现分析结果，帮助投资者和分析师快速理解财报情感基调。

## 项目结构

```
FinBert/
├── backend/               # FastAPI后端
│   └── app.py             # 主应用服务
├── data/                  # 数据存储
│   ├── processed/         # 处理后的报告文本
│   └── raw/               # 原始10-K报告
├── frontend/              # Vue3前端应用
│   ├── public/            # 静态资源
│   ├── src/               # 源代码
│   │   ├── components/    # Vue组件
│   │   ├── services/      # API服务
│   │   ├── store/         # Pinia状态管理
│   │   └── views/         # 页面视图
│   ├── index.html         # 主HTML模板
│   └── package.json       # 依赖配置
├── preprocess/            # 数据预处理模块
│   ├── clean_10-K.py      # 报告文本清洗
│   ├── config.py          # 配置参数
│   └── data_fetcher.py    # SEC数据获取
├── results/               # 分析结果存储
├── sentiment_analysis/    # 情感分析模块
│   └── predict.py         # 预测分析脚本
└── requirements.txt       # Python依赖
```

## 技术栈

- **后端**: Python, FastAPI, NLTK, Transformers, PyTorch
- **前端**: Vue 3, TypeScript, Pinia, Element Plus, ECharts
- **数据处理**: BeautifulSoup, 正则表达式, Pandas
- **模型**: FinBERT (金融领域预训练 BERT 模型)

## 使用流程

### 1. 环境配置

```bash
# 创建虚拟环境(可选)
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 安装Python依赖
pip install -r requirements.txt

# 创建必要目录
mkdir -p data/raw data/processed results
```

### 2. 数据获取与预处理

```bash
# 从SEC EDGAR下载10-K报告
python preprocess/data_fetcher.py --email your.email@example.com

# 清洗文本并提取关键章节
python preprocess/clean_10-K.py
```

预处理会生成以下关键章节文件:

- **Item_1.txt**: 业务描述（Business）
- **Item_1A.txt**: 风险因素（Risk Factors）
- **Item_7.txt**: 管理层讨论与分析（MD&A）
- **Item_7A.txt**: 市场风险定量与定性披露

### 3. 情感分析

```bash
# 分析所有处理好的报告
python -m sentiment_analysis.predict

# 分析特定股票
python -m sentiment_analysis.predict --ticker AAPL

# 分析特定年份的报告
python -m sentiment_analysis.predict --ticker AAPL --year 2020
```

### 4. 启动应用

```bash
# 启动后端API
cd backend
uvicorn app:app --reload

# 在新终端启动前端
cd frontend
npm install
npm run dev
```

## 核心功能

### 1. 数据处理

- 自动下载并解析 SEC EDGAR 上的 10-K 年报
- 智能提取关键章节，移除页眉页脚等干扰内容
- 句子级别拆分，保留有意义的文本内容

### 2. 情感分析

- 使用 FinBERT 模型分析每个句子的情感倾向
- 提供积极、中性、消极的分类结果和置信度
- 生成章节级和整体报告的情感摘要统计

### 3. 可视化界面

- **首页**: 查看可用的所有报告列表，按公司分组
- **报告详情**: 显示各章节情感分析结果，支持句子级探索
- **分析概览**: 提供跨公司、跨年份的情感趋势对比
- **交互式功能**: 点击句子查看详细情感分析和置信度

### 4. 情感标记系统

- 正面情感（绿色）: 可能对公司或投资者有利的内容
- 中性情感（灰色）: 客观描述，不带明显情感倾向
- 负面情感（红色）: 可能存在风险或不利因素的内容

## API 接口

- `/api/tickers`: 获取所有可用股票代码
- `/api/reports`: 获取所有报告列表
- `/api/report/{ticker}/{date}`: 获取特定报告详情和情感分析
- `/api/report/{ticker}/{date}/section/{section}`: 获取特定章节分析
- `/api/summary`: 获取所有报告的情感分析摘要

通过以上功能和流程，FinBert 系统帮助用户深入理解金融报告的情感倾向，为投资决策提供辅助参考。
