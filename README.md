
# FinBert 金融报告情感分析项目

本项目利用金融领域的预训练模型（FinBERT）对10-K年报进行情感分析，判断报告中的句子是积极（利好）、中性还是消极（利空），并给出判断的置信度。通过GPT模型为FinBERT分析结果提供专业解释，并使用Vue3+TypeScript+ECharts开发可视化BI界面，使用户能够交互查看分析结果。

## 项目特点

- 自动获取SEC EDGAR数据库中的10-K年报
- 智能清洗和处理10-K文本，提取关键章节
- 使用FinBERT金融领域预训练模型进行情感分析
- 集成GPT模型提供专业金融解释
- 前端可视化界面显示带颜色标记的报告内容
- 用户可点击句子获取AI分析解释
- 支持不同公司、不同年份的报告对比

## 项目结构

```
FinBert/
├── data/                  # 数据目录
│   ├── raw/               # 原始10-K报告
│   ├── processed/         # 处理后的文本文件
│   └── debug/             # 调试信息
├── models/                # 存放模型文件
├── preprocess/            # 预处理脚本
│   ├── config.py          # 配置文件
│   ├── data_fetcher.py    # SEC EDGAR数据获取
│   ├── pdf_to_txt.py      # PDF转TXT
│   ├── clean_10-K.py      # 清洗10-K报告文本
│   └── renamePDFTXTto_yyyy_mm_dd.py  # 重命名文件
├── sentiment_analysis/    # 情感分析模块
│   ├── model.py           # FinBERT模型定义
│   ├── predict.py         # 情感分析预测
│   └── gpt_explainer.py   # GPT解释器
├── backend/               # 后端API
│   ├── app.py             # FastAPI应用
│   └── services/          # 业务逻辑服务
├── frontend/              # Vue3前端
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── views/         # 页面视图
│   │   ├── store/         # Pinia状态管理
│   │   ├── services/      # API调用服务
│   │   └── router/        # 路由配置
├── results/               # 分析结果
├── logs/                  # 日志文件
└── README.md              # 项目说明
```

## 使用流程

### 1. 环境配置

```bash
# 克隆项目
git clone https://github.com/your-username/FinBert.git
cd FinBert

# 创建目录
mkdir -p data/raw data/processed results logs

# 安装依赖
pip install -r requirements.txt
```

### 2. 数据获取

```bash
# 自动从SEC EDGAR获取10-K报告
python -m preprocess.data_fetcher --ticker NVDA --start_year 2020 --end_year 2023

# 或者手动准备PDF文件，命名格式为：ticker_10-K_yyyymmdd.pdf，然后转换为文本
python preprocess/pdf_to_txt.py
```

### 3. 数据预处理

```bash
# 规范化文件名（如果需要）
python preprocess/renamePDFTXTto_yyyy_mm_dd.py

# 清洗文本并提取关键章节
python preprocess/clean_10-K.py
```

### 4. 情感分析与解释

```bash
# 使用FinBERT进行基础情感分析
python -m sentiment_analysis.predict --ticker AAPL

# 使用GPT模型添加解释性分析 (需要OpenAI API密钥)
export OPENAI_API_KEY=your_api_key  # Linux/MacOS
# 或 set OPENAI_API_KEY=your_api_key  # Windows
python -m sentiment_analysis.gpt_explainer --ticker AAPL --gpt_model gpt-3.5-turbo
```

### 5. 启动后端服务

```bash
# 启动FastAPI服务
cd backend
uvicorn app:app --reload
```

### 6. 启动前端服务

```bash
# 安装依赖
cd frontend
npm install

# 开发模式启动
npm run dev

# 或构建生产版本
npm run build
```

## 技术栈

- **数据获取**: SEC EDGAR API, sec-edgar-downloader
- **预处理**: Python, NLTK, 正则表达式
- **情感分析**: FinBERT, Transformers, PyTorch
- **解释生成**: OpenAI GPT API
- **后端 API**: FastAPI
- **前端框架**: Vue 3, TypeScript, Pinia
- **UI 组件库**: Element Plus
- **数据可视化**: ECharts

## 功能模块

### 1. 数据获取模块 (data_fetcher.py)
自动从SEC EDGAR数据库获取指定公司和年份的10-K报告，无需手动下载PDF文件。

### 2. 增强版文本清洗 (clean_10-K.py)
使用多种模式匹配和启发式算法，提高10-K报告的解析准确率，支持不同格式的报告。

### 3. GPT解释器 (gpt_explainer.py)
调用OpenAI API为FinBERT的情感分析结果提供专业的解释，帮助投资者理解文本的潜在含义。

### 4. 交互式前端
- 情感标记显示：正面(绿色)、中性(灰色)、负面(红色)
- 点击句子查看详细分析和GPT解释
- 章节级别和报告级别的情感统计
- 多维度数据可视化和比较

## 主要配置项

在`preprocess/config.py`中可以配置以下参数:
- 数据目录路径
- 输出结果路径
- 模型参数
- 章节提取规则

## 界面预览

- 首页：显示可用的报告列表和情感分布概览
- 报告详情页：带情感标记的报告内容，点击句子可查看FinBERT分析结果和GPT解释
- 分析总览页：各公司报告的情感分析对比和趋势图表

## 未来改进

- 支持更多类型的金融报告(8-K, 10-Q等)
- 添加更多金融领域预训练模型的支持
- 开发更多数据可视化图表
- 集成自动投资决策建议功能
- 实现批量处理和定时更新的自动化流程
