<template>
  <div class="analysis-container">
    <div class="header">
      <h1>金融报告情感分析总览</h1>
      <p>各公司10-K报告情感分析统计</p>
    </div>

    <div class="filter-section">
      <el-select
        v-model="selectedTicker"
        placeholder="选择股票代码"
        clearable
        @change="handleTickerChange"
      >
        <el-option
          v-for="ticker in store.tickers"
          :key="ticker"
          :label="ticker"
          :value="ticker"
        />
      </el-select>
    </div>

    <div v-if="store.loading" class="loading">
      <el-skeleton :rows="10" animated />
    </div>
    <div v-else-if="store.error" class="error">
      <el-alert :title="store.error" type="error" show-icon />
    </div>
    <div v-else class="analysis-content">
      <div class="charts-section">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>历年情感趋势对比</span>
                </div>
              </template>
              <div class="chart-container">
                <v-chart class="chart" :option="trendChartOption" autoresize />
              </div>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="chart-card">
              <template #header>
                <div class="card-header">
                  <span>公司间情感对比</span>
                </div>
              </template>
              <div class="chart-container">
                <v-chart
                  class="chart"
                  :option="comparisonChartOption"
                  autoresize
                />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <div class="summary-table">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>报告情感分析详情</span>
              <el-button @click="exportCSV" size="small" type="primary"
                >导出CSV</el-button
              >
            </div>
          </template>
          <el-table :data="tableData" stripe style="width: 100%">
            <el-table-column prop="ticker" label="股票代码" sortable />
            <el-table-column prop="date" label="报告日期" sortable />
            <el-table-column label="主要情感">
              <template #default="scope">
                <el-tag :type="getSentimentTagType(scope.row.main_sentiment)">
                  {{ getSentimentName(scope.row.main_sentiment) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="正面占比">
              <template #default="scope">
                <el-progress
                  :percentage="scope.row.positive_ratio * 100"
                  :color="'#67C23A'"
                  :format="() => formatPercent(scope.row.positive_ratio)"
                  :stroke-width="15"
                />
              </template>
            </el-table-column>
            <el-table-column label="中性占比">
              <template #default="scope">
                <el-progress
                  :percentage="scope.row.neutral_ratio * 100"
                  :color="'#909399'"
                  :format="() => formatPercent(scope.row.neutral_ratio)"
                  :stroke-width="15"
                />
              </template>
            </el-table-column>
            <el-table-column label="负面占比">
              <template #default="scope">
                <el-progress
                  :percentage="scope.row.negative_ratio * 100"
                  :color="'#F56C6C'"
                  :format="() => formatPercent(scope.row.negative_ratio)"
                  :stroke-width="15"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作">
              <template #default="scope">
                <el-button
                  type="primary"
                  size="small"
                  @click="viewReport(scope.row.ticker, scope.row.date)"
                >
                  查看详情
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import { useReportStore } from "@/store/report";
import { SummaryItem } from "@/services/api";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { BarChart, LineChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import { groupBy } from "lodash";

// 注册ECharts组件
use([
  CanvasRenderer,
  BarChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
]);

export default defineComponent({
  name: "AnalysisView",
  components: {
    VChart,
  },
  setup() {
    const router = useRouter();
    const store = useReportStore();
    const selectedTicker = ref("");

    // 初始化加载数据
    onMounted(async () => {
      await Promise.all([store.fetchTickers(), store.fetchSummary()]);
    });

    // 处理股票代码变更
    const handleTickerChange = async (ticker: string) => {
      await store.fetchSummary(ticker);
    };

    // 格式化百分比
    const formatPercent = (value: number) => {
      return (value * 100).toFixed(1) + "%";
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

    // 查看报告详情
    const viewReport = (ticker: string, date: string) => {
      router.push(`/report/${ticker}/${date}`);
    };

    // 导出CSV
    const exportCSV = () => {
      // 创建CSV内容
      const headers = [
        "股票代码",
        "报告日期",
        "主要情感",
        "正面占比",
        "中性占比",
        "负面占比",
        "正面句子数",
        "中性句子数",
        "负面句子数",
      ];

      const rows = store.summaryData.map((item) => [
        item.ticker,
        item.date,
        getSentimentName(item.main_sentiment),
        formatPercent(item.positive_ratio),
        formatPercent(item.neutral_ratio),
        formatPercent(item.negative_ratio),
        item.positive_count,
        item.neutral_count,
        item.negative_count,
      ]);

      // 组合CSV内容
      const csvContent = [
        headers.join(","),
        ...rows.map((row) => row.join(",")),
      ].join("\n");

      // 创建下载链接
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", "金融报告情感分析.csv");
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    // 表格数据
    const tableData = computed(() => {
      // 按日期倒序排序
      return [...store.summaryData].sort((a, b) =>
        b.date.localeCompare(a.date)
      );
    });

    // 情感趋势图表选项
    const trendChartOption = computed(() => {
      if (store.summaryData.length === 0) return {};

      // 按公司分组并按日期排序
      const groupedByTicker = groupBy(store.summaryData, "ticker");

      // 准备数据系列
      const series: any[] = [];
      const tickers: string[] = [];

      Object.entries(groupedByTicker).forEach(([ticker, items]) => {
        // 按日期排序
        const sortedItems = [...items].sort((a, b) =>
          a.date.localeCompare(b.date)
        );

        tickers.push(ticker);

        // 添加正面情感系列
        series.push({
          name: `${ticker} 正面`,
          type: "line",
          stack: ticker,
          emphasis: { focus: "series" },
          data: sortedItems.map((item) => [
            // 格式化日期
            formatDate(item.date),
            // 使用百分比值
            (item.positive_ratio * 100).toFixed(1),
          ]),
        });
      });

      return {
        title: {
          text: "公司报告历年情感趋势",
        },
        tooltip: {
          trigger: "axis",
          formatter: function (params: any) {
            const date = params[0].value[0];
            let result = `日期: ${date}<br/>`;

            params.forEach((param: any) => {
              const value = param.value[1];
              result += `${param.seriesName}: ${value}%<br/>`;
            });

            return result;
          },
        },
        legend: {
          data: series.map((s) => s.name),
        },
        grid: {
          left: "3%",
          right: "4%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "time",
          boundaryGap: false,
        },
        yAxis: {
          type: "value",
          min: 0,
          max: 100,
          name: "百分比 (%)",
        },
        series: series,
      };
    });

    // 公司间情感对比图表选项
    const comparisonChartOption = computed(() => {
      if (store.summaryData.length === 0) return {};

      // 按公司分组
      const groupedByTicker = groupBy(store.summaryData, "ticker");

      // 计算每个公司的平均情感比例
      const comparisonData = Object.entries(groupedByTicker).map(
        ([ticker, items]) => {
          const total = items.length;
          const avgPositive =
            items.reduce((sum, item) => sum + item.positive_ratio, 0) / total;
          const avgNeutral =
            items.reduce((sum, item) => sum + item.neutral_ratio, 0) / total;
          const avgNegative =
            items.reduce((sum, item) => sum + item.negative_ratio, 0) / total;

          return { ticker, avgPositive, avgNeutral, avgNegative };
        }
      );

      return {
        title: {
          text: "公司间情感分布对比",
        },
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "shadow",
          },
          formatter: function (params: any) {
            let result = `${params[0].name}<br/>`;
            params.forEach((param: any) => {
              const value = (param.value * 100).toFixed(1);
              result += `${param.seriesName}: ${value}%<br/>`;
            });
            return result;
          },
        },
        legend: {
          data: ["正面", "中性", "负面"],
        },
        grid: {
          left: "3%",
          right: "4%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "category",
          data: comparisonData.map((item) => item.ticker),
        },
        yAxis: {
          type: "value",
          name: "百分比",
          axisLabel: {
            formatter: "{value}%",
          },
        },
        series: [
          {
            name: "正面",
            type: "bar",
            stack: "total",
            emphasis: { focus: "series" },
            data: comparisonData.map((item) =>
              (item.avgPositive * 100).toFixed(1)
            ),
            itemStyle: { color: "#67C23A" },
          },
          {
            name: "中性",
            type: "bar",
            stack: "total",
            emphasis: { focus: "series" },
            data: comparisonData.map((item) =>
              (item.avgNeutral * 100).toFixed(1)
            ),
            itemStyle: { color: "#909399" },
          },
          {
            name: "负面",
            type: "bar",
            stack: "total",
            emphasis: { focus: "series" },
            data: comparisonData.map((item) =>
              (item.avgNegative * 100).toFixed(1)
            ),
            itemStyle: { color: "#F56C6C" },
          },
        ],
      };
    });

    // 格式化日期
    const formatDate = (dateString: string) => {
      if (!dateString) return "";

      // 将YYYYMMDD格式转换为YYYY-MM-DD
      const year = dateString.substr(0, 4);
      const month = dateString.substr(4, 2);
      const day = dateString.substr(6, 2);

      return `${year}-${month}-${day}`;
    };

    return {
      store,
      selectedTicker,
      handleTickerChange,
      tableData,
      trendChartOption,
      comparisonChartOption,
      getSentimentTagType,
      getSentimentName,
      formatPercent,
      viewReport,
      exportCSV,
    };
  },
});
</script>

<style scoped>
.analysis-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 28px;
  color: #303133;
}

.header p {
  color: #606266;
  margin-top: 10px;
}

.filter-section {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}

.filter-section .el-select {
  width: 200px;
}

.loading,
.error {
  margin: 50px 0;
}

.charts-section {
  margin-bottom: 30px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 400px;
}

.chart {
  height: 100%;
  width: 100%;
}

.summary-table {
  margin-top: 20px;
}
</style>
