<template>
  <div class="sentence-explanation">
    <div 
      :class="['sentence', sentenceClass]" 
      @click="toggleExplanation"
    >
      {{ sentence.text }}
    </div>
    
    <el-collapse-transition>
      <div v-if="showExplanation" class="explanation">
        <div class="explanation-header">
          <div class="sentiment-label">
            <el-tag :type="sentimentTagType" effect="dark">
              {{ sentimentText }}
              <span class="confidence">{{ (maxConfidence * 100).toFixed(1) }}%</span>
            </el-tag>
          </div>
          <div class="ai-badge" v-if="hasGptExplanation">
            <el-tag type="info" size="small">GPT分析</el-tag>
          </div>
        </div>
        
        <div class="explanation-body">
          <p>{{ explanationText }}</p>
          
          <div class="confidence-bars">
            <div class="bar-label">置信度:</div>
            <div class="bar-group">
              <div class="bar-item">
                <div class="bar-name positive">积极</div>
                <el-progress 
                  :percentage="(sentence.confidence.positive * 100)" 
                  :color="'#67c23a'" 
                  :show-text="false"
                />
                <div class="bar-value">{{ (sentence.confidence.positive * 100).toFixed(1) }}%</div>
              </div>
              <div class="bar-item">
                <div class="bar-name neutral">中性</div>
                <el-progress 
                  :percentage="(sentence.confidence.neutral * 100)" 
                  :color="'#909399'" 
                  :show-text="false"
                />
                <div class="bar-value">{{ (sentence.confidence.neutral * 100).toFixed(1) }}%</div>
              </div>
              <div class="bar-item">
                <div class="bar-name negative">消极</div>
                <el-progress 
                  :percentage="(sentence.confidence.negative * 100)" 
                  :color="'#f56c6c'" 
                  :show-text="false"
                />
                <div class="bar-value">{{ (sentence.confidence.negative * 100).toFixed(1) }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-collapse-transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

// 定义组件接收的属性
const props = defineProps({
  sentence: {
    type: Object,
    required: true
  }
});

// 状态
const showExplanation = ref(false);

// 计算属性
const sentenceClass = computed(() => {
  return {
    'positive': props.sentence.label === 'positive',
    'neutral': props.sentence.label === 'neutral',
    'negative': props.sentence.label === 'negative',
    'active': showExplanation.value
  };
});

const sentimentTagType = computed(() => {
  switch(props.sentence.label) {
    case 'positive': return 'success';
    case 'neutral': return 'info';
    case 'negative': return 'danger';
    default: return 'info';
  }
});

const sentimentText = computed(() => {
  switch(props.sentence.label) {
    case 'positive': return '积极';
    case 'neutral': return '中性';
    case 'negative': return '消极';
    default: return '未知';
  }
});

const maxConfidence = computed(() => {
  const confidence = props.sentence.confidence || {};
  return Math.max(
    confidence.positive || 0,
    confidence.neutral || 0,
    confidence.negative || 0
  );
});

const explanationText = computed(() => {
  if (props.sentence.explanation) {
    if (typeof props.sentence.explanation === 'object') {
      return props.sentence.explanation.explanation || '暂无解释';
    }
    return props.sentence.explanation;
  }
  
  // 简单的默认解释
  switch(props.sentence.label) {
    case 'positive': 
      return '这段内容传达了积极信息，可能对公司未来发展有利。';
    case 'negative': 
      return '这段内容传达了消极信息，可能存在风险或挑战。';
    case 'neutral': 
    default:
      return '这是一段中性描述，主要陈述事实，没有明显的积极或消极含义。';
  }
});

const hasGptExplanation = computed(() => {
  return props.sentence.explanation && 
         typeof props.sentence.explanation === 'object' && 
         props.sentence.explanation.model && 
         props.sentence.explanation.model.includes('gpt');
});

// 方法
const toggleExplanation = () => {
  showExplanation.value = !showExplanation.value;
};
</script>

<style scoped>
.sentence-explanation {
  margin-bottom: 8px;
}

.sentence {
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 4px solid transparent;
}

.sentence:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.sentence.active {
  background-color: rgba(0, 0, 0, 0.07);
}

.sentence.positive {
  border-left-color: var(--el-color-success);
}

.sentence.neutral {
  border-left-color: var(--el-color-info);
}

.sentence.negative {
  border-left-color: var(--el-color-danger);
}

.explanation {
  margin-top: 8px;
  background-color: var(--el-color-info-light-9);
  border-radius: 4px;
  padding: 12px;
}

.explanation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.sentiment-label .confidence {
  margin-left: 5px;
  font-size: 0.85em;
  opacity: 0.9;
}

.explanation-body {
  font-size: 14px;
}

.confidence-bars {
  margin-top: 12px;
  background-color: rgba(255, 255, 255, 0.5);
  padding: 10px;
  border-radius: 4px;
}

.bar-label {
  font-weight: 500;
  margin-bottom: 8px;
}

.bar-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-name {
  width: 40px;
  text-align: right;
  font-size: 12px;
}

.bar-name.positive {
  color: var(--el-color-success);
}

.bar-name.neutral {
  color: var(--el-color-info);
}

.bar-name.negative {
  color: var(--el-color-danger);
}

.bar-value {
  width: 50px;
  font-size: 12px;
  color: #606266;
}

.el-progress {
  flex: 1;
}
</style> 