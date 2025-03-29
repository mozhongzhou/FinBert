import { defineStore } from 'pinia'
import api, { Report, ReportData, SectionData, SummaryItem } from '@/services/api'
import { ref, computed } from 'vue'

export const useReportStore = defineStore('report', () => {
  // 状态
  const reports = ref<Report[]>([])
  const tickers = ref<string[]>([])
  const currentReport = ref<ReportData | null>(null)
  const currentSectionData = ref<SectionData | null>(null)
  const summaryData = ref<SummaryItem[]>([])
  const loading = ref(false)
  const error = ref('')

  // 获取所有股票代码
  async function fetchTickers() {
    try {
      loading.value = true
      error.value = ''
      const response = await api.getTickers()
      tickers.value = response.data.tickers
    } catch (err: any) {
      error.value = err.message || '获取股票代码失败'
      console.error('获取股票代码失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 获取所有报告
  async function fetchReports(ticker?: string) {
    try {
      loading.value = true
      error.value = ''
      const response = await api.getReports(ticker)
      reports.value = response.data.reports
    } catch (err: any) {
      error.value = err.message || '获取报告列表失败'
      console.error('获取报告列表失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 获取特定报告数据
  async function fetchReportData(ticker: string, date: string) {
    try {
      loading.value = true
      error.value = ''
      const response = await api.getReportData(ticker, date)
      currentReport.value = response.data
    } catch (err: any) {
      error.value = err.message || '获取报告详情失败'
      console.error('获取报告详情失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 获取特定章节数据
  async function fetchSectionData(ticker: string, date: string, section: string) {
    try {
      loading.value = true
      error.value = ''
      const response = await api.getSectionData(ticker, date, section)
      currentSectionData.value = response.data
    } catch (err: any) {
      error.value = err.message || '获取章节数据失败'
      console.error('获取章节数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 获取摘要数据
  async function fetchSummary(ticker?: string) {
    try {
      loading.value = true
      error.value = ''
      const response = await api.getSummary(ticker)
      summaryData.value = response.data.summary
    } catch (err: any) {
      error.value = err.message || '获取摘要数据失败'
      console.error('获取摘要数据失败:', err)
    } finally {
      loading.value = false
    }
  }

  // 计算属性：按股票分组的报告
  const reportsByTicker = computed(() => {
    const result: Record<string, Report[]> = {}
    for (const report of reports.value) {
      if (!result[report.ticker]) {
        result[report.ticker] = []
      }
      result[report.ticker].push(report)
    }
    return result
  })

  // 计算属性：当前报告的情感分布
  const currentSentimentDistribution = computed(() => {
    if (!currentReport.value) return null
    
    return {
      positive: currentReport.value.summary.positive_ratio,
      neutral: currentReport.value.summary.neutral_ratio,
      negative: currentReport.value.summary.negative_ratio
    }
  })

  return {
    reports,
    tickers,
    currentReport,
    currentSectionData,
    summaryData,
    loading,
    error,
    reportsByTicker,
    currentSentimentDistribution,
    fetchTickers,
    fetchReports,
    fetchReportData,
    fetchSectionData,
    fetchSummary
  }
}) 