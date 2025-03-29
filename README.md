# FinBert 金融报告情感分析项目

本项目利用金融领域的预训练模型（FinBERT）对 10-K 年报进行情感分析，判断报告中的句子是积极（利好）、中性还是消极（利空），并给出判断的置信度。通过 Vue3+TypeScript+ECharts 开发可视化 BI 界面，使用户能够交互查看分析结果。

## 项目特点

- 使用 FinBERT 金融领域预训练模型进行 10-K 报告的情感分析
- 分析结果包括积极/中性/消极的情感分类和置信度
- 可视化 BI 界面显示带颜色标记的报告内容
- 用户可点击句子获取 AI 分析解释
- 多维度数据可视化，支持不同公司、不同年份的报告对比

## 项目结构

```
FinBert/
├── data/                  # 数据目录
│   ├── raw/               # 原始PDF和TXT文件
│   ├── processed/         # 处理后的文本文件
│   └── debug/             # 调试信息
├── models/                # 存放模型文件
├── preprocess/            # 预处理脚本
│   ├── config.py          # 配置文件
│   ├── pdf_to_txt.py      # PDF转TXT
│   ├── clean_10-K.py      # 清洗10-K报告文本
│   └── renamePDFTXTto_yyyy_mm_dd.py  # 重命名文件
├── sentiment_analysis/    # 情感分析模块
│   ├── model.py           # 模型定义
│   └── predict.py         # 模型预测
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
└── README.md              # 项目说明
```

## 使用流程

### 1. 数据准备

准备公司 10-K 年报 PDF 文件，命名格式为：`ticker_10-K_yyyymmdd.pdf`（例如：`AAPL_10-K_20221028.pdf`）。

### 2. 数据预处理

```bash
# 将PDF转换为TXT
python preprocess/pdf_to_txt.py

# 规范化文件名（如果需要）
python preprocess/renamePDFTXTto_yyyy_mm_dd.py

# 清洗文本并提取关键章节
python preprocess/clean_10-K.py
```

### 3. 情感分析

```bash
# 对所有处理好的文本进行情感分析
python -m sentiment_analysis.predict

# 仅分析特定股票
python -m sentiment_analysis.predict --ticker AAPL
```

### 4. 启动后端服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动FastAPI服务
cd backend
uvicorn app:app --reload
```

### 5. 启动前端服务

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

- **预处理**: Python, PyPDF2, NLTK
- **情感分析**: FinBERT, Transformers, PyTorch
- **后端 API**: FastAPI
- **前端框架**: Vue 3, TypeScript, Pinia
- **UI 组件库**: Element Plus
- **数据可视化**: ECharts

## 界面预览

- 首页：显示可用的报告列表
- 报告详情页：带情感标记的报告内容，点击句子可查看详细分析
- 分析总览页：各公司报告的情感分析对比

## 未来改进

- 添加更多金融领域预训练模型的支持
- 优化 PDF 处理算法，提高文本提取质量
- 增加更多数据可视化图表类型
- 支持用户上传自定义报告进行分析
