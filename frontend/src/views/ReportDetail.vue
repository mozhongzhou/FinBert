<template>
  <div class="report-detail-container">
    <div class="header">
      <el-page-header
        @back="goBack"
        :title="ticker + ' 10-K报告'"
        :content="date"
      />
      <h2>{{ ticker }} 10-K报告 ({{ formatDate(date) }})</h2>
    </div>

    <div v-if="store.loading" class="loading">
      <el-skeleton :rows="15" animated />
    </div>
    <div v-else-if="store.error" class="error">
      <el-alert :title="store.error" type="error" show-icon />
    </div>
    <div v-else-if="store.currentReport" class="report-content">
      <div class="report-summary">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card class="summary-card">
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
          <el-col :span="16">
            <el-card class="summary-card">
              <template #header>
                <div class="card-header">
                  <span>总体情感趋势</span>
                </div>
              </template>
              <div class="summary-stats">
                <div
                  class="stat-item"
                  :class="getSentimentClass(mainSentiment)"
                >
                  <div class="stat-label">主要情感倾向</div>
                  <div class="stat-value">
                    {{ getSentimentName(mainSentiment) }}
                  </div>
                </div>
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
                  {{ formatPercent(sectionData.proportions.positive) }}</el-tag
                >
                <el-tag type="info"
                  >中性:
                  {{ formatPercent(sectionData.proportions.neutral) }}</el-tag
                >
                <el-tag type="danger"
                  >负面:
                  {{ formatPercent(sectionData.proportions.negative) }}</el-tag
                >
              </div>
            </div>

            <div class="sentences-container">
              <div
                v-for="(sentence, index) in sectionData.sentences"
                :key="index"
                class="sentence-item"
                :class="getSentenceClass(sentence.label)"
                @click="selectSentence(sentence)"
              >
                {{ sentence.text }}
              </div>
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
                  `正面: ${formatPercent(selectedSentence.confidence.positive)}`
              "
              :stroke-width="18"
              class="sentiment-progress"
            />
            <el-progress
              :percentage="selectedSentence.confidence.neutral * 100"
              :color="'#909399'"
              :format="
                () =>
                  `中性: ${formatPercent(selectedSentence.confidence.neutral)}`
              "
              :stroke-width="18"
              class="sentiment-progress"
            />
            <el-progress
              :percentage="selectedSentence.confidence.negative * 100"
              :color="'#F56C6C'"
              :format="
                () =>
                  `负面: ${formatPercent(selectedSentence.confidence.negative)}`
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
  },
  setup() {
    const route = useRoute();
    const router = useRouter();
    const store = useReportStore();

    const ticker = computed(() => route.params.ticker as string);
    const date = computed(() => route.params.date as string);
    const activeSection = ref<string>("");

    // 选中的句子和弹出抽屉
    const selectedSentence = ref<SectionSentence | null>(null);
    const sentenceDrawer = ref<boolean>(false);

    // 饼图选项
    const chartOption = computed(() => {
      if (!store.currentReport) return {};

      const summary = store.currentReport.summary;
      return {
        tooltip: {
          trigger: "item",
          formatter: "{b}: {c} ({d}%)",
        },
        legend: {
          orient: "vertical",
          left: "left",
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

    // 获取主要情感倾向
    const mainSentiment = computed(() => {
      if (!store.currentReport) return "neutral";

      const summary = store.currentReport.summary;
      if (
        summary.positive_count > summary.neutral_count &&
        summary.positive_count > summary.negative_count
      ) {
        return "positive";
      } else if (
        summary.negative_count > summary.neutral_count &&
        summary.negative_count > summary.positive_count
      ) {
        return "negative";
      }
      return "neutral";
    });

    // 处理句子选择
    const selectSentence = (sentence: SectionSentence) => {
      selectedSentence.value = sentence;
      sentenceDrawer.value = true;
    };

    // 工具函数
    const formatPercent = (value: number) => {
      return (value * 100).toFixed(1) + "%";
    };

    const getSentimentName = (sentiment: string) => {
      const map: { [key: string]: string } = {
        positive: "正面",
        neutral: "中性",
        negative: "负面",
      };
      return map[sentiment] || "未知";
    };

    const getSentimentClass = (sentiment: string) => {
      return sentiment;
    };

    const getSentenceClass = (sentiment: string) => {
      return `sentiment-${sentiment}`;
    };

    const getSentimentTagType = (sentiment: string) => {
      const map: { [key: string]: string } = {
        positive: "success",
        neutral: "info",
        negative: "danger",
      };
      return map[sentiment] || "";
    };

    const formatSectionName = (section: string) => {
      const map: { [key: string]: string } = {
        md_and_a: "管理层讨论与分析",
        risk_factors: "风险因素",
        business: "业务概述",
        financial_statements: "财务报表",
      };
      return map[section] || section;
    };

    const formatDate = (dateStr: string) => {
      // 格式化日期，例如20210331 => 2021-03-31
      if (dateStr.length === 8) {
        return `${dateStr.substring(0, 4)}-${dateStr.substring(
          4,
          6
        )}-${dateStr.substring(6, 8)}`;
      }
      return dateStr;
    };

    const goBack = () => {
      router.push("/");
    };

    // 为句子生成简单解释（如果没有GPT解释）
    const generateExplanation = (sentence: SectionSentence) => {
      if (sentence.explanation) {
        return sentence.explanation;
      }

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

    // 加载报告数据
    onMounted(async () => {
      if (ticker.value && date.value) {
        await store.fetchReportDetails(ticker.value, date.value);

        // 设置初始激活章节
        if (store.currentReport && store.currentReport.sections) {
          const sectionNames = Object.keys(store.currentReport.sections);
          if (sectionNames.length > 0) {
            activeSection.value = sectionNames[0];
          }
        }
      }
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
      getSentimentClass,
      getSentenceClass,
      getSentimentTagType,
      formatSectionName,
      formatDate,
      goBack,
      generateExplanation,
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
  margin-bottom: 30px;
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
  flex-wrap: wrap;
  gap: 20px;
}

.stat-item {
  min-width: 120px;
  padding: 10px;
  border-radius: 4px;
  background-color: #f5f7fa;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 18px;
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
  margin-bottom: 10px;
}

.section-stats {
  display: flex;
  gap: 10px;
}

.sentences-container {
  margin-top: 20px;
}

.sentence-item {
  padding: 8px;
  margin-bottom: 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.sentence-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
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
  padding: 10px;
}

.sentence-text {
  padding: 15px;
  margin-bottom: 15px;
  border-radius: 4px;
  background-color: #f5f7fa;
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
</style>
