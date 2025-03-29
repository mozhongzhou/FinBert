import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000, // 超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 定义接口类型
export interface Ticker {
  ticker: string
  name?: string
}

export interface Report {
  ticker: string
  date: string
  sections: string[]
}

export interface SectionSentence {
  text: string
  label: 'positive' | 'neutral' | 'negative'
  confidence: {
    positive: number
    neutral: number
    negative: number
  }
}

export interface SectionData {
  stats: {
    positive: number
    neutral: number
    negative: number
  }
  proportions: {
    positive: number
    neutral: number
    negative: number
  }
  sentences: SectionSentence[]
}

export interface ReportData {
  summary: {
    positive: number
    neutral: number
    negative: number
    positive_ratio: number
    neutral_ratio: number
    negative_ratio: number
  }
  sections: {
    [key: string]: SectionData
  }
}

export interface SummaryItem {
  ticker: string
  date: string
  main_sentiment: 'positive' | 'neutral' | 'negative'
  positive_ratio: number
  neutral_ratio: number
  negative_ratio: number
  positive_count: number
  neutral_count: number
  negative_count: number
}

// API方法
export default {
  // 检查健康状态
  checkHealth() {
    return api.get<{ status: string; model_loaded: boolean }>('/health')
  },

  // 获取所有股票代码
  getTickers() {
    return api.get<{ tickers: string[] }>('/tickers')
  },

  // 获取所有报告
  getReports(ticker?: string) {
    return api.get<{ reports: Report[] }>('/reports', {
      params: { ticker }
    })
  },

  // 获取特定报告的详细数据
  getReportData(ticker: string, date: string) {
    return api.get<ReportData>(`/report/${ticker}/${date}`)
  },

  // 获取特定报告章节的句子及其情感分析
  getSectionData(ticker: string, date: string, section: string) {
    return api.get<SectionData>(`/report/${ticker}/${date}/section/${section}`)
  },

  // 获取所有报告的情感分析摘要
  getSummary(ticker?: string) {
    return api.get<{ summary: SummaryItem[] }>('/summary', {
      params: { ticker }
    })
  }
} 