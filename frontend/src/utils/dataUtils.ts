/**
 * 数据工具类 - 用于前端数据处理和验证
 */

import { ReportDetail, SectionSentence } from '@/services/api';

/**
 * 验证报告数据是否有效且完整
 * @param report 报告详情数据
 * @returns 如果数据有效返回true，否则返回false
 */
export const isValidReportData = (report: ReportDetail | null): boolean => {
  if (!report) return false;
  
  // 检查基本属性
  if (!report.ticker || !report.date || !report.summary) {
    console.error('报告缺少基本属性', report);
    return false;
  }
  
  // 检查章节数据
  if (!report.sections || Object.keys(report.sections).length === 0) {
    console.error('报告没有章节数据', report);
    return false;
  }
  
  // 检查至少一个章节有句子数据
  const hasSentences = Object.values(report.sections).some(
    section => section.sentences && section.sentences.length > 0
  );
  
  if (!hasSentences) {
    console.error('报告所有章节都没有句子数据', report);
    return false;
  }
  
  return true;
};

/**
 * 获取情感分析标签的颜色类
 * @param sentiment 情感标签
 * @returns 对应的CSS类名
 */
export const getSentimentClass = (sentiment: string): string => {
  switch (sentiment) {
    case 'positive':
      return 'sentiment-positive';
    case 'negative':
      return 'sentiment-negative';
    case 'neutral':
    default:
      return 'sentiment-neutral';
  }
};

/**
 * 获取主要情感标签
 * @param report 报告数据
 * @returns 主要情感标签
 */
export const getMainSentiment = (report: ReportDetail): string => {
  if (!report || !report.summary) return 'neutral';
  
  const summary = report.summary;
  const counts = {
    positive: summary.positive_count || 0,
    neutral: summary.neutral_count || 0,
    negative: summary.negative_count || 0
  };
  
  let maxSentiment = 'neutral';
  let maxCount = 0;
  
  for (const [sentiment, count] of Object.entries(counts)) {
    if (count > maxCount) {
      maxCount = count;
      maxSentiment = sentiment;
    }
  }
  
  return maxSentiment;
};

/**
 * 格式化章节名称
 * @param section 章节代码
 * @returns 格式化后的章节名称
 */
export const formatSectionName = (section: string): string => {
  const sectionMap: Record<string, string> = {
    "Item_1": "业务描述",
    "Item_1A": "风险因素",
    "Item_7": "管理层讨论与分析",
    "Item_7A": "市场风险披露"
  };
  return sectionMap[section] || section;
};

/**
 * 格式化百分比
 * @param value 0-1之间的小数
 * @returns 格式化后的百分比字符串
 */
export const formatPercent = (value: number): string => {
  return (value * 100).toFixed(1) + "%";
}; 