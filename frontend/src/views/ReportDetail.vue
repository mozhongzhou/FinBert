<!-- filepath: c:\Coding\FinBert\frontend\src\views\ReportDetail.vue -->
<template>
  <div class="report-detail-container">
    <div v-if="store.loading" class="loading">
      <el-skeleton :rows="10" animated />
    </div>
    <div v-else-if="store.error" class="error">
      <el-alert :title="store.error" type="error" show-icon />
      <div class="error-actions">
        <el-button type="primary" @click="handleRetry">重试</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </div>
    <div v-else-if="store.currentReport" class="report-content">
      <!-- 调试信息区域 -->
      <div
        v-if="isDevelopment"
        class="debug-info"
        style="
          margin-bottom: 20px;
          padding: 10px;
          background: #f0f9eb;
          border-radius: 4px;
        "
      >
        <p><strong>调试信息</strong></p>
        <p>章节数量: {{ Object.keys(store.currentReport.sections).length }}</p>
        <p>
          章节列表: {{ Object.keys(store.currentReport.sections).join(", ") }}
        </p>
        <p v-if="activeSection">
          当前章节句子数:
          {{
            store.currentReport.sections[activeSection]?.sentences?.length || 0
          }}
        </p>
      </div>
      <div class="header">
        <el-page-header @back="goBack">
          <template #content>
            <span class="report-title"> {{ ticker }} {{ date }} 年报分析 </span>
          </template>
        </el-page-header>
      </div>

      <div class="report-summary">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>情感分布</span>
                </div>
              </template>
              <div class="chart-container">
                <v-chart class="chart" :option="chartOption" autoresize />
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="summary-card">
              <template #header>
                <div class="card-header">
                  <span>报告概述</span>
                  <el-tag :type="getSentimentTagType(mainSentiment)">
                    {{ getSentimentName(mainSentiment) }}
                  </el-tag>
                </div>
              </template>
              <div class="summary-stats">
                <div class="stat-item">
                  <div class="stat-label">正面句子占比</div>
                  <div class="stat-value positive">
                    {{
                      formatPercent(store.currentReport.summary.positive_ratio)
                    }}
                  </div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">中性句子占比</div>
                  <div class="stat-value neutral">
                    {{
                      formatPercent(store.currentReport.summary.neutral_ratio)
                    }}
                  </div>
                </div>
                <div class="stat-item">
                  <div class="stat-label">负面句子占比</div>
                  <div class="stat-value negative">
                    {{
                      formatPercent(store.currentReport.summary.negative_ratio)
                    }}
                  </div>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <div class="report-sections">
        <el-tabs v-model="activeSection" type="border-card">
          <el-tab-pane
            v-for="(sectionData, sectionName) in store.currentReport.sections"
            :key="sectionName"
            :label="formatSectionName(sectionName)"
            :name="sectionName"
          >
            <div class="section-header">
              <h3>{{ formatSectionName(sectionName) }}</h3>
              <div class="section-stats">
                <el-tag type="success"
                  >正面:
                  {{ formatPercent(sectionData.summary.positive) }}</el-tag
                >
                <el-tag type="info"
                  >中性:
                  {{ formatPercent(sectionData.summary.neutral) }}</el-tag
                >
                <el-tag type="danger"
                  >负面:
                  {{ formatPercent(sectionData.summary.negative) }}</el-tag
                >
              </div>
            </div>

            <div class="sentences-container">
              <template
                v-if="sectionData.sentences && sectionData.sentences.length > 0"
              >
                <sentence-explanation
                  v-for="(sentence, index) in sectionData.sentences"
                  :key="index"
                  :sentence="sentence"
                  @click="selectSentence(sentence)"
                />
              </template>
              <el-empty v-else description="没有句子数据" />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <el-drawer
        v-model="sentenceDrawer"
        title="句子情感分析详情"
        direction="rtl"
        size="30%"
      >
        <div v-if="selectedSentence" class="sentence-detail">
          <div
            class="sentence-text"
            :class="getSentenceClass(selectedSentence.label)"
          >
            {{ selectedSentence.text }}
          </div>

          <div class="sentiment-analysis">
            <h4>情感分析结果</h4>
            <div class="sentiment-label">
              <span>判断结果:</span>
              <el-tag :type="getSentimentTagType(selectedSentence.label)">
                {{ getSentimentName(selectedSentence.label) }}
              </el-tag>
            </div>

            <h4>置信度分布</h4>
            <el-progress
              :percentage="selectedSentence.confidence.positive * 100"
              :color="'#67C23A'"
              :format="
                () =>
                  `正面: ${
                    selectedSentence
                      ? formatPercent(selectedSentence.confidence.positive)
                      : 'N/A'
                  }`
              "
              :stroke-width="18"
              class="sentiment-progress"
            />
            <el-progress
              :percentage="selectedSentence.confidence.neutral * 100"
              :color="'#909399'"
              :format="
                () =>
                  `中性: ${
                    selectedSentence
                      ? formatPercent(selectedSentence.confidence.neutral)
                      : 'N/A'
                  }`
              "
              :stroke-width="18"
              class="sentiment-progress"
            />
            <el-progress
              :percentage="selectedSentence.confidence.negative * 100"
              :color="'#F56C6C'"
              :format="
                () =>
                  `负面: ${
                    selectedSentence
                      ? formatPercent(selectedSentence.confidence.negative)
                      : 'N/A'
                  }`
              "
              :stroke-width="18"
              class="sentiment-progress"
            />
          </div>

          <div class="ai-explanation">
            <h4>AI解释分析</h4>
            <p>{{ generateExplanation(selectedSentence) }}</p>
          </div>
        </div>
      </el-drawer>
    </div>
    <div v-else class="no-data">
      <el-empty description="未找到报告数据" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useReportStore } from "@/store/report";
import { SectionSentence } from "@/services/api";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import SentenceExplanation from "@/components/SentenceExplanation.vue";
import {
  formatSectionName,
  formatPercent,
  getSentimentClass,
  isValidReportData,
  getMainSentiment,
} from "@/utils/dataUtils";

// 注册必要的ECharts组件
use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
]);

export default defineComponent({
  name: "ReportDetail",
  components: {
    VChart,
    SentenceExplanation,
  },
  setup() {
    const router = useRouter();
    const route = useRoute();
    const store = useReportStore();

    // 获取路由参数
    const ticker = ref(route.params.ticker as string);
    const date = ref(route.params.date as string);

    // 界面状态
    const activeSection = ref("");
    const selectedSentence = ref<SectionSentence | null>(null);
    const sentenceDrawer = ref(false);

    // 构建饼图选项
    const chartOption = computed(() => {
      if (!store.currentReport || !store.currentReport.summary) {
        return {};
      }

      const summary = store.currentReport.summary;

      return {
        tooltip: {
          trigger: "item",
          formatter: "{b}: {c} ({d}%)",
        },
        legend: {
          orient: "vertical",
          left: 10,
          data: ["正面", "中性", "负面"],
        },
        series: [
          {
            name: "情感分布",
            type: "pie",
            radius: ["40%", "70%"],
            avoidLabelOverlap: false,
            label: {
              show: false,
              position: "center",
            },
            emphasis: {
              label: {
                show: true,
                fontSize: "18",
                fontWeight: "bold",
              },
            },
            labelLine: {
              show: false,
            },
            data: [
              {
                value: summary.positive_count,
                name: "正面",
                itemStyle: { color: "#67C23A" },
              },
              {
                value: summary.neutral_count,
                name: "中性",
                itemStyle: { color: "#909399" },
              },
              {
                value: summary.negative_count,
                name: "负面",
                itemStyle: { color: "#F56C6C" },
              },
            ],
          },
        ],
      };
    });

    // 添加主要情感计算
    const mainSentiment = computed(() => {
      if (!store.currentReport || !store.currentReport.summary)
        return "neutral";

      return getMainSentiment(store.currentReport);
    });

    // 处理句子选择
    const selectSentence = (sentence: SectionSentence) => {
      selectedSentence.value = sentence;
      sentenceDrawer.value = true;
    };

    // 工具函数 - 使用工具类方法
    const getSentimentName = (sentiment: string) => {
      const map: { [key: string]: string } = {
        positive: "正面",
        neutral: "中性",
        negative: "负面",
      };
      return map[sentiment] || "未知";
    };

    const getSentimentTagType = (sentiment: string) => {
      const map: { [key: string]: string } = {
        positive: "success",
        neutral: "info",
        negative: "danger",
      };
      return map[sentiment] || "";
    };

    const getSentenceClass = getSentimentClass;

    // 添加格式化日期函数
    const formatDate = (dateStr: string) => {
      // 简单格式化日期，如果需要可以增强
      return dateStr;
    };

    // 返回上一页
    const goBack = () => {
      router.back();
    };

    // 为句子生成简单解释
    const generateExplanation = (sentence: SectionSentence) => {
      // 基于情感和置信度生成简单解释
      const sentiment = sentence.label;
      const confidence = sentence.confidence[sentiment];

      if (sentiment === "positive" && confidence > 0.9) {
        return "这是一个非常积极的陈述，表明公司在这方面表现优异，可能对投资者是个好消息。";
      } else if (sentiment === "positive") {
        return "这是一个积极的陈述，表明公司在这方面表现良好。";
      } else if (sentiment === "negative" && confidence > 0.9) {
        return "这是一个非常消极的陈述，可能表明公司在这方面面临严重挑战，投资者应该关注。";
      } else if (sentiment === "negative") {
        return "这是一个消极的陈述，表明公司在这方面可能存在问题或风险。";
      } else {
        return "这是一个中性陈述，主要是陈述事实，不包含明显的积极或消极信息。";
      }
    };

    // 添加重试功能
    const handleRetry = async () => {
      if (ticker.value && date.value) {
        // 使用forceAnalyze参数强制重新分析
        await store.fetchReportDetails(ticker.value, date.value, true);
      }
    };

    // 加载报告数据
    onMounted(async () => {
      if (ticker.value && date.value) {
        try {
          await store.fetchReportDetails(ticker.value, date.value);

          // 检查数据是否有效
          if (
            store.currentReport &&
            (!store.currentReport.sections ||
              Object.keys(store.currentReport.sections).length === 0)
          ) {
            store.error = "报告数据无效，请重试或联系管理员";
            return;
          }

          // 设置初始激活章节
          if (store.currentReport && store.currentReport.sections) {
            const sectionNames = Object.keys(store.currentReport.sections);
            if (sectionNames.length > 0) {
              activeSection.value = sectionNames[0];
            }
          }
        } catch (error) {
          console.error("加载报告详情失败", error);
        }
      }
    });

    // 添加在script setup或script内部的适当位置
    const isDevelopment = computed(() => {
      return import.meta.env.MODE === "development";
    });

    return {
      ticker,
      date,
      store,
      activeSection,
      selectedSentence,
      sentenceDrawer,
      chartOption,
      mainSentiment,
      selectSentence,
      formatPercent,
      getSentimentName,
      getSentimentTagType,
      getSentenceClass,
      formatSectionName,
      formatDate,
      goBack,
      generateExplanation,
      isDevelopment,
      handleRetry,
    };
  },
});
</script>

<style scoped>
.report-detail-container {
  padding: 20px;
}

.header {
  margin-bottom: 20px;
}

.report-summary {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
}

.chart {
  height: 100%;
}

.summary-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.summary-stats {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  background-color: #f8f9fa;
}

.stat-label {
  font-weight: bold;
}

.stat-value {
  font-weight: bold;
}

.positive {
  color: #67c23a;
}

.neutral {
  color: #909399;
}

.negative {
  color: #f56c6c;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-stats {
  display: flex;
  gap: 10px;
}

.sentences-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sentence-item {
  padding: 10px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid #ebeef5;
  transition: all 0.3s;
}

.sentence-item:hover {
  background-color: #f5f7fa;
}

.sentiment-positive {
  border-left: 4px solid #67c23a;
}

.sentiment-neutral {
  border-left: 4px solid #909399;
}

.sentiment-negative {
  border-left: 4px solid #f56c6c;
}

.sentence-detail {
  padding: 20px;
}

.sentence-text {
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 20px;
  font-size: 16px;
  line-height: 1.5;
}

.sentiment-analysis {
  margin-bottom: 20px;
}

.sentiment-label {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.sentiment-progress {
  margin-bottom: 10px;
}

.ai-explanation {
  background-color: #ecf5ff;
  padding: 15px;
  border-radius: 4px;
  margin-top: 20px;
}

.error,
.loading,
.no-data {
  padding: 20px;
  min-height: 60vh;
  display: flex;
  justify-content: center;
  align-items: center;
}

.error-actions {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
}
</style>
