<template>
  <div class="home-container">
    <div class="header">
      <h1>金融报告情感分析</h1>
      <p>使用FinBERT模型分析10-K年报</p>
    </div>

    <div class="ticker-selector">
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
      <el-button type="primary" @click="handleAnalysisView"
        >查看分析总览</el-button
      >
    </div>

    <div v-if="store.loading" class="loading">
      <el-skeleton :rows="10" animated />
    </div>
    <div v-else-if="store.error" class="error">
      <el-alert :title="store.error" type="error" show-icon />
    </div>
    <div v-else class="reports-container">
      <template v-if="Object.keys(store.reportsByTicker).length > 0">
        <div
          v-for="(reports, ticker) in store.reportsByTicker"
          :key="ticker"
          class="ticker-reports"
        >
          <h2>{{ ticker }}</h2>
          <el-table :data="reports" stripe style="width: 100%">
            <el-table-column prop="date" label="报告日期" sortable />
            <el-table-column label="可用章节">
              <template #default="scope">
                <el-tag
                  v-for="section in scope.row.sections"
                  :key="section"
                  class="section-tag"
                >
                  {{ formatSectionName(section) }}
                </el-tag>
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
        </div>
      </template>
      <el-empty v-else description="暂无报告数据" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useReportStore } from "@/store/report";

export default defineComponent({
  name: "HomeView",
  setup() {
    const router = useRouter();
    const store = useReportStore();
    const selectedTicker = ref("");

    // 初始化加载数据
    onMounted(async () => {
      await store.fetchTickers();
      await store.fetchReports();
    });

    // 处理股票代码变更
    const handleTickerChange = async (ticker: string) => {
      await store.fetchReports(ticker);
    };

    // 格式化章节名称
    const formatSectionName = (section: string) => {
      const sectionMap: Record<string, string> = {
        Item_1: "业务描述",
        Item_1A: "风险因素",
        Item_7: "管理层讨论与分析",
        Item_7A: "市场风险披露",
      };
      return sectionMap[section] || section;
    };

    // 查看报告详情
    const viewReport = (ticker: string, date: string) => {
      router.push(`/report/${ticker}/${date}`);
    };

    // 跳转到分析总览页面
    const handleAnalysisView = () => {
      router.push("/analysis");
    };

    return {
      selectedTicker,
      store,
      handleTickerChange,
      formatSectionName,
      viewReport,
      handleAnalysisView,
    };
  },
});
</script>

<style scoped>
.home-container {
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

.ticker-selector {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.ticker-selector .el-select {
  width: 200px;
}

.reports-container {
  margin-top: 20px;
}

.ticker-reports {
  margin-bottom: 30px;
}

.ticker-reports h2 {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
  color: #303133;
}

.section-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.loading,
.error {
  margin: 50px 0;
}
</style>
