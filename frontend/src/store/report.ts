import { defineStore } from 'pinia';
import { 
  fetchTickers, 
  fetchReports, 
  fetchReportDetails, 
  fetchSummary,
  ReportItem,
  ReportDetail,
  SummaryItem
} from '@/services/api';

// 定义错误处理辅助函数
function getErrorMessage(error: unknown): string {
  console.error('API错误详情:', error);
  if (error instanceof Error) return error.message;
  if (typeof error === 'object' && error !== null) {
    // 处理Axios错误响应
    const axiosError = error as any;
    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail;
    }
    if (axiosError.response?.status) {
      return `服务器返回错误码: ${axiosError.response.status} - ${axiosError.response?.statusText || '未知错误'}`;
    }
    if (axiosError.message) {
      return axiosError.message;
    }
  }
  return String(error);
}

// 添加调试日志函数
function logDebug(message: string, data?: any) {
  if (import.meta.env.DEV) {
    console.log(`[ReportStore] ${message}`, data);
  }
}

interface ReportState {
  tickers: string[];
  reports: ReportItem[];
  reportsByTicker: Record<string, ReportItem[]>;
  currentReport: ReportDetail | null;
  summaryData: SummaryItem[];
  loading: boolean;
  error: string | null;
}

export const useReportStore = defineStore('report', {
  state: (): ReportState => ({
    tickers: [],
    reports: [],
    reportsByTicker: {},
    currentReport: null,
    summaryData: [],
    loading: false,
    error: null
  }),
  
  actions: {
    async fetchTickers() {
      try {
        this.loading = true;
        this.error = null;
        logDebug('开始获取股票代码列表');
        const tickers = await fetchTickers();
        logDebug('获取股票代码成功', tickers);
        this.tickers = tickers;
      } catch (error: unknown) {
        logDebug('获取股票代码失败', error);
        this.error = '获取股票代码失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchReports(ticker?: string) {
      try {
        this.loading = true;
        this.error = null;
        logDebug(`开始获取报告列表${ticker ? `(${ticker})` : ''}`);
        const reports = await fetchReports(ticker);
        logDebug('获取报告列表成功', reports);
        this.reports = reports;
        
        // 按ticker组织报告
        this.reportsByTicker = reports.reduce((acc, report) => {
          if (!acc[report.ticker]) {
            acc[report.ticker] = [];
          }
          acc[report.ticker].push(report);
          return acc;
        }, {} as Record<string, ReportItem[]>);
        
        logDebug('报告按股票代码分组完成', this.reportsByTicker);
      } catch (error: unknown) {
        logDebug('获取报告列表失败', error);
        this.error = '获取报告列表失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchReportDetails(ticker: string, date: string, forceAnalyze: boolean = false) {
      try {
        this.loading = true;
        this.error = null;
        logDebug(`开始获取报告详情: ${ticker}/${date}, 强制分析: ${forceAnalyze}`);
        
        const reportData = await fetchReportDetails(ticker, date, forceAnalyze);
        logDebug('获取报告详情成功', {
          ticker: reportData.ticker,
          date: reportData.date,
          sections: Object.keys(reportData.sections || {}),
          summary: reportData.summary
        });
        
        // 检查数据结构是否完整
        if (!reportData.sections || Object.keys(reportData.sections).length === 0) {
          throw new Error('报告章节数据为空');
        }
        
        this.currentReport = reportData;
      } catch (error: unknown) {
        logDebug('获取报告详情失败', error);
        this.error = '获取报告详情失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchSummary(ticker?: string) {
      try {
        this.loading = true;
        this.error = null;
        logDebug(`开始获取摘要数据${ticker ? `(${ticker})` : ''}`);
        const summaryData = await fetchSummary(ticker);
        logDebug('获取摘要数据成功', summaryData);
        this.summaryData = summaryData;
      } catch (error: unknown) {
        logDebug('获取摘要数据失败', error);
        this.error = '获取摘要数据失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    clearCurrentReport() {
      logDebug('清除当前报告数据');
      this.currentReport = null;
    }
  }
});