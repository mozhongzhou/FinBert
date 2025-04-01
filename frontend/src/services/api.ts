import axios from 'axios';

// API基础URL - 根据实际部署环境进行调整
const API_BASE_URL = 'http://localhost:8000';

// 创建axios实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 较长的超时时间，因为情感分析可能需要时间
  headers: {
    'Content-Type': 'application/json'
  }
});

// 定义接口类型
export interface SectionSentence {
  text: string;
  label: 'positive' | 'neutral' | 'negative';
  confidence: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export interface SectionSummary {
  positive: number;
  neutral: number;
  negative: number;
}

export interface ReportSection {
  sentences: SectionSentence[];
  summary: SectionSummary;
  counts?: {
    positive: number;
    neutral: number;
    negative: number;
  };
}

export interface ReportSummary {
  positive_count: number;
  neutral_count: number;
  negative_count: number;
  positive_ratio: number;
  neutral_ratio: number;
  negative_ratio: number;
  total_sentences?: number;
}

export interface ReportDetail {
  ticker: string;
  date: string;
  summary: ReportSummary;
  sections: Record<string, ReportSection>;
}

export interface ReportItem {
  ticker: string;
  date: string;
  sections: string[];
}

export interface SummaryItem {
  ticker: string;
  date: string;
  main_sentiment: 'positive' | 'neutral' | 'negative';
  positive_ratio: number;
  neutral_ratio: number;
  negative_ratio: number;
  positive_count: number;
  neutral_count: number;
  negative_count: number;
}

// API函数
export const fetchTickers = async (): Promise<string[]> => {
  const response = await api.get('/api/tickers');
  return response.data.tickers;
};

export const fetchReports = async (ticker?: string): Promise<ReportItem[]> => {
  const url = ticker ? `/api/reports?ticker=${ticker}` : '/api/reports';
  const response = await api.get(url);
  return response.data.reports;
};

export const fetchReportDetails = async (ticker: string, date: string, analyze: boolean = false): Promise<ReportDetail> => {
  const url = `/api/report/${ticker}/${date}${analyze ? '?analyze=true' : ''}`;
  const response = await api.get(url);
  return response.data;
};

export const fetchSummary = async (ticker?: string): Promise<SummaryItem[]> => {
  const url = ticker ? `/api/summary?ticker=${ticker}` : '/api/summary';
  const response = await api.get(url);
  return response.data.summary;
};

export const analyzeText = async (text: string): Promise<SectionSentence> => {
  const response = await api.get(`/api/analyze-text?text=${encodeURIComponent(text)}`);
  return response.data;
};

export default api;