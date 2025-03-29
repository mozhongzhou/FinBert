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

// 注册ECharts组件
use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
]);

export default defineComponent({
  name: "ReportDetailView",
  components: {
    VChart,
  },
  props: {
    ticker: {
      type: String,
      required: true,
    },
    date: {
      type: String,
      required: true,
    },
  },
  setup(props) {
    const route = useRoute();
    const router = useRouter();
    const store = useReportStore();

    const activeSection = ref("");
    const sentenceDrawer = ref(false);
    const selectedSentence = ref<SectionSentence | null>(null);

    // 加载报告数据
    onMounted(async () => {
      await store.fetchReportData(props.ticker, props.date);

      // 设置默认选中的章节
      if (store.currentReport && store.currentReport.sections) {
        const sections = Object.keys(store.currentReport.sections);
        if (sections.length > 0) {
          activeSection.value = sections[0];
        }
      }
    });

    // 主要情感倾向
    const mainSentiment = computed(() => {
      if (!store.currentReport) return "neutral";

      const { positive_ratio, neutral_ratio, negative_ratio } =
        store.currentReport.summary;
      if (positive_ratio > neutral_ratio && positive_ratio > negative_ratio) {
        return "positive";
      } else if (
        negative_ratio > neutral_ratio &&
        negative_ratio > positive_ratio
      ) {
        return "negative";
      } else {
        return "neutral";
      }
    });

    // 饼图配置
    const chartOption = computed(() => {
      if (!store.currentReport) return {};

      const { positive_ratio, neutral_ratio, negative_ratio } =
        store.currentReport.summary;

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
            type: "pie",
            radius: ["50%", "70%"],
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
                value: (positive_ratio * 100).toFixed(1),
                name: "正面",
                itemStyle: { color: "#67C23A" },
              },
              {
                value: (neutral_ratio * 100).toFixed(1),
                name: "中性",
                itemStyle: { color: "#909399" },
              },
              {
                value: (negative_ratio * 100).toFixed(1),
                name: "负面",
                itemStyle: { color: "#F56C6C" },
              },
            ],
          },
        ],
      };
    });

    // 格式化百分比
    const formatPercent = (value: number) => {
      return (value * 100).toFixed(1) + "%";
    };

    // 格式化日期
    const formatDate = (dateString: string) => {
      if (!dateString) return "";

      // 将YYYYMMDD格式转换为YYYY-MM-DD
      const year = dateString.substr(0, 4);
      const month = dateString.substr(4, 2);
      const day = dateString.substr(6, 2);

      return `${year}-${month}-${day}`;
    };

    // 格式化章节名称
    const formatSectionName = (section: string) => {
      const sectionMap: Record<string, string> = {
        md_and_a: "管理层讨论与分析",
        risk_factors: "风险因素",
        financial_statements: "财务报表",
      };
      return sectionMap[section] || section;
    };

    // 获取情感样式类
    const getSentimentClass = (sentiment: string) => {
      return {
        positive: sentiment === "positive",
        neutral: sentiment === "neutral",
        negative: sentiment === "negative",
      };
    };

    // 获取情感标签样式类型
    const getSentimentTagType = (sentiment: string) => {
      switch (sentiment) {
        case "positive":
          return "success";
        case "neutral":
          return "info";
        case "negative":
          return "danger";
        default:
          return "info";
      }
    };

    // 获取情感中文名称
    const getSentimentName = (sentiment: string) => {
      switch (sentiment) {
        case "positive":
          return "正面/利好";
        case "neutral":
          return "中性";
        case "negative":
          return "负面/利空";
        default:
          return "未知";
      }
    };

    // 获取句子样式类
    const getSentenceClass = (sentiment: string) => {
      return {
        "positive-sentence": sentiment === "positive",
        "neutral-sentence": sentiment === "neutral",
        "negative-sentence": sentiment === "negative",
      };
    };

    // 选择查看句子详情
    const selectSentence = (sentence: SectionSentence) => {
      selectedSentence.value = sentence;
      sentenceDrawer.value = true;
    };

    // 生成AI解释
    const generateExplanation = (sentence: SectionSentence) => {
      // 这里可以集成更高级的解释算法，目前使用简单规则
      const { label, confidence } = sentence;
      const text = sentence.text;

      let explanation = "";

      if (label === "positive") {
        explanation = `该文本被判定为利好消息，置信度为${formatPercent(
          confidence.positive
        )}。`;
        explanation += `其中包含积极的关键词和表述，如`;

        // 简单关键词检测
        if (
          text.includes("增长") ||
          text.includes("提高") ||
          text.includes("增加")
        ) {
          explanation += `"增长"、"提高"或"增加"等表示业务向好的词汇，`;
        }
        if (text.includes("成功") || text.includes("领先")) {
          explanation += `"成功"或"领先"等表示优势的描述，`;
        }
        if (text.includes("机会") || text.includes("创新")) {
          explanation += `"机会"或"创新"等表示未来发展潜力的词汇，`;
        }

        explanation += `这些表述表明公司经营状况良好或有积极的发展前景。`;
      } else if (label === "negative") {
        explanation = `该文本被判定为利空消息，置信度为${formatPercent(
          confidence.negative
        )}。`;
        explanation += `其中包含消极的关键词和表述，如`;

        // 简单关键词检测
        if (
          text.includes("下降") ||
          text.includes("减少") ||
          text.includes("降低")
        ) {
          explanation += `"下降"、"减少"或"降低"等表示业务下滑的词汇，`;
        }
        if (
          text.includes("风险") ||
          text.includes("挑战") ||
          text.includes("困难")
        ) {
          explanation += `"风险"、"挑战"或"困难"等表示存在问题的描述，`;
        }
        if (text.includes("竞争") || text.includes("压力")) {
          explanation += `"竞争"或"压力"等表示面临外部挑战的词汇，`;
        }

        explanation += `这些表述表明公司可能面临经营困难或市场挑战。`;
      } else {
        explanation = `该文本被判定为中性消息，置信度为${formatPercent(
          confidence.neutral
        )}。`;
        explanation += `文本中没有明显的积极或消极倾向，可能是在客观陈述事实或提供中立的信息，不包含明显的情感色彩。`;
      }

      return explanation;
    };

    // 返回上一页
    const goBack = () => {
      router.push("/");
    };

    return {
      store,
      activeSection,
      sentenceDrawer,
      selectedSentence,
      mainSentiment,
      chartOption,
      formatPercent,
      formatDate,
      formatSectionName,
      getSentenceClass,
      getSentimentClass,
      getSentimentTagType,
      getSentimentName,
      selectSentence,
      generateExplanation,
      goBack,
    };
  },
});
</script>

<style scoped>
.report-detail-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  margin-bottom: 30px;
}

.header h2 {
  margin-top: 15px;
  color: #303133;
}

.loading,
.error,
.no-data {
  margin: 50px 0;
}

.report-summary {
  margin-bottom: 30px;
}

.summary-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 250px;
}

.chart {
  height: 100%;
  width: 100%;
}

.summary-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.stat-item {
  flex: 1;
  min-width: 120px;
  padding: 15px;
  border-radius: 4px;
  background-color: #f5f7fa;
  text-align: center;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
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

.report-sections {
  margin-top: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.section-header h3 {
  margin: 0;
  color: #303133;
}

.section-stats {
  display: flex;
  gap: 10px;
}

.sentences-container {
  max-height: 500px;
  overflow-y: auto;
  padding: 10px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.sentence-item {
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.sentence-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.positive-sentence {
  background-color: rgba(103, 194, 58, 0.1);
  border-left: 4px solid #67c23a;
}

.neutral-sentence {
  background-color: rgba(144, 147, 153, 0.1);
  border-left: 4px solid #909399;
}

.negative-sentence {
  background-color: rgba(245, 108, 108, 0.1);
  border-left: 4px solid #f56c6c;
}

.sentence-detail {
  padding: 15px;
}

.sentence-text {
  padding: 15px;
  margin-bottom: 20px;
  border-radius: 4px;
  font-size: 16px;
  line-height: 1.6;
}

.sentiment-analysis {
  margin-top: 20px;
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
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.ai-explanation p {
  line-height: 1.6;
  color: #606266;
}
</style>
