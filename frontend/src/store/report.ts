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
  if (error instanceof Error) return error.message;
  if (typeof error === 'object' && error !== null) {
    // 处理Axios错误响应
    const axiosError = error as any;
    if (axiosError.response?.data?.detail) {
      return axiosError.response.data.detail;
    }
  }
  return String(error);
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
        const tickers = await fetchTickers();
        this.tickers = tickers;
      } catch (error: unknown) {
        this.error = '获取股票代码失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchReports(ticker?: string) {
      try {
        this.loading = true;
        this.error = null;
        const reports = await fetchReports(ticker);
        this.reports = reports;
        
        // 按ticker组织报告
        this.reportsByTicker = reports.reduce((acc, report) => {
          if (!acc[report.ticker]) {
            acc[report.ticker] = [];
          }
          acc[report.ticker].push(report);
          return acc;
        }, {} as Record<string, ReportItem[]>);
      } catch (error: unknown) {
        this.error = '获取报告列表失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchReportDetails(ticker: string, date: string, forceAnalyze: boolean = false) {
      try {
        this.loading = true;
        this.error = null;
        const reportData = await fetchReportDetails(ticker, date, forceAnalyze);
        this.currentReport = reportData;
      } catch (error: unknown) {
        this.error = '获取报告详情失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    async fetchSummary(ticker?: string) {
      try {
        this.loading = true;
        this.error = null;
        const summaryData = await fetchSummary(ticker);
        this.summaryData = summaryData;
      } catch (error: unknown) {
        this.error = '获取摘要数据失败：' + getErrorMessage(error);
      } finally {
        this.loading = false;
      }
    },
    
    clearCurrentReport() {
      this.currentReport = null;
    }
  }
});