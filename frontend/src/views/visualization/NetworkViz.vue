<template>
  <div class="network-viz fade-in">
    <div class="page-header">
      <div class="header-content">
        <h1>网络探索</h1>
        <p>药物-疾病关联网络可视化与分析</p>
      </div>
      <div class="header-actions">
        <el-radio-group v-model="viewMode" @change="handleModeChange">
          <el-radio-button value="graph">原始图</el-radio-button>
          <el-radio-button value="prediction">预测结果</el-radio-button>
        </el-radio-group>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- Sidebar Controls -->
      <el-col :span="6">
        <el-card class="control-panel">
          <template #header>
            <div class="panel-header">
              <span>可视化控制</span>
              <el-button type="primary" link @click="resetFilters">重置</el-button>
            </div>
          </template>

          <el-form label-position="top">
            <!-- Data Selection -->
            <el-form-item v-if="viewMode === 'graph'" label="选择图数据">
              <el-select v-model="selectedGraphId" placeholder="选择图" @change="loadGraphData">
                <el-option
                  v-for="item in availableGraphs"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
             

            <el-form-item v-else label="选择实验模型">
              <el-select v-model="selectedExperimentId" placeholder="选择模型" @change="loadPredictionData">
                <el-option
                  v-for="item in availableExperiments"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>

            <el-divider />

            <!-- Layout Controls -->
            <el-form-item label="布局算法">
              <el-select v-model="layout" @change="updateChart">
                <el-option label="力导向布局 (Force)" value="force" />
                <el-option label="圆形布局 (Circular)" value="circular" />
                <el-option label="正交布局 (None)" value="none" />
              </el-select>
            </el-form-item>

            <el-form-item label="显示节点数" v-if="!selectedNodeId">
              <el-slider v-model="limit" :min="10" :max="500" :step="10" @change="refreshData" />
            </el-form-item>
            </el-form> 

            <!-- Node Information -->
            <div v-if="selectedNode" class="node-info">
              <el-divider />
              <h4>节点详情</h4>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="ID">{{ selectedNode.id }}</el-descriptions-item>
                <el-descriptions-item label="类型">
                  <el-tag :type="selectedNode.type === 'drug' ? 'primary' : 'success'" size="small">
                    {{ selectedNode.type === 'drug' ? '药物' : '疾病' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
              <div class="node-actions">
                <el-button type="primary" size="small" @click="expandNode">查看邻居</el-button>
                <el-button size="small" @click="clearSelection">取消选择</el-button>
              </div>
            </div>

            <div v-else class="empty-selection">
              <el-text type="info">在图中点击节点查看详情</el-text>
            </div>
          
        </el-card>

        <!-- Stats Card -->
        <el-card class="stats-card" v-if="subgraph">
          <template #header>统计信息</template>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="label">节点数</div>
              <div class="value">{{ subgraph.nodes.length }}</div>
            </div>
            <div class="stat-item">
              <div class="label">边数</div>
              <div class="value">{{ subgraph.edges.length }}</div>
            </div>
            <div class="stat-item">
              <div class="label">药物</div>
              <div class="value">{{ nodeCounts.drug }}</div>
            </div>
            <div class="stat-item">
              <div class="label">疾病</div>
              <div class="value">{{ nodeCounts.disease }}</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Graph Container -->
      <el-col :span="18">
        <el-card class="graph-card" v-loading="loading">
          <div v-if="subgraph" class="chart-container">
            <v-chart
              ref="chartRef"
              :option="chartOption"
              autoresize
              @click="handleChartClick"
            />
          </div>
          <el-empty v-else description="请选择数据源以开始探索" />
          
          <!-- Legend and Overlay -->
          <div v-if="subgraph" class="graph-overlay">
            <div class="legend">
              <div class="legend-item">
                <span class="dot drug"></span> 药物
              </div>
              <div class="legend-item">
                <span class="dot disease"></span> 疾病
              </div>
              <div class="legend-item">
                <span class="line original"></span> 原始关联
              </div>
              <div v-if="viewMode === 'prediction'" class="legend-item">
                <span class="line predicted"></span> 预测关联
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { GraphChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage } from 'element-plus'

import { listGraphs, getSubgraph, Graph, SubgraphResponse, GraphNode } from '@/api/graphs'
import { listExperiments, getTopPredictions, Experiment } from '@/api/experiments'

// Register ECharts components
use([
  CanvasRenderer,
  GraphChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
])

// State
const loading = ref(false)
const viewMode = ref<'graph' | 'prediction'>('graph')
const selectedGraphId = ref<number>()
const selectedExperimentId = ref<number>()
const availableGraphs = ref<Graph[]>([])
const availableExperiments = ref<Experiment[]>([])
const subgraph = ref<SubgraphResponse | null>(null)
const limit = ref(100)
const layout = ref<'force' | 'circular' | 'none'>('force')
const selectedNodeId = ref<string | null>(null)
const chartRef = ref<any>(null)

// Computed
const selectedNode = computed(() => {
  if (!selectedNodeId.value || !subgraph.value) return null
  return subgraph.value.nodes.find(n => n.id === selectedNodeId.value) || null
})

const nodeCounts = computed(() => {
  if (!subgraph.value) return { drug: 0, disease: 0 }
  return {
    drug: subgraph.value.nodes.filter(n => n.type === 'drug').length,
    disease: subgraph.value.nodes.filter(n => n.type === 'disease').length
  }
})

const chartOption = computed(() => {
  if (!subgraph.value) return {}

  const nodes = subgraph.value.nodes.map(n => ({
    id: n.id,
    name: n.name,
    symbolSize: n.id === selectedNodeId.value ? 40 : 25,
    value: n.type === 'drug' ? '药物' : '疾病',
    category: n.type === 'drug' ? 0 : 1,
    itemStyle: {
      color: n.type === 'drug' ? '#409EFF' : '#67C23A',
      borderColor: n.id === selectedNodeId.value ? '#303133' : 'transparent',
      borderWidth: 2
    },
    label: {
      show: subgraph.value!.nodes.length < 50 || n.id === selectedNodeId.value
    }
  }))

  const edges = subgraph.value.edges.map(e => ({
    source: e.source,
    target: e.target,
    lineStyle: {
      color: e.type === 'predicted' ? '#F56C6C' : '#DCDFE6',
      type: e.type === 'predicted' ? 'dashed' : 'solid',
      width: e.weight ? e.weight * 3 : 1,
      opacity: 0.6
    }
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          return `节点: ${params.data.name}<br/>类型: ${params.data.value}`
        } else {
          const edge = subgraph.value!.edges[params.dataIndex]
          return `关联: ${params.data.source} - ${params.data.target}<br/>
                  类型: ${edge.type === 'predicted' ? '预测' : '原始'}<br/>
                  ${edge.weight ? '概率: ' + edge.weight.toFixed(4) : ''}`
        }
      }
    },
    legend: [
      {
        data: ['药物', '疾病'],
        orient: 'vertical',
        left: 'left'
      }
    ],
    series: [
      {
        type: 'graph',
        layout: layout.value,
        data: nodes,
        links: edges,
        categories: [
          { name: '药物' },
          { name: '疾病' }
        ],
        roam: true,
        label: {
          position: 'right',
          formatter: '{b}'
        },
        force: {
          repulsion: 200,
          edgeLength: 100
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 5
          }
        }
      }
    ]
  }
})

// Methods
const fetchAvailableData = async () => {
  try {
    const [graphsRes, expsRes] = await Promise.all([
      listGraphs(1, 100, { is_built: true }),
      listExperiments(1, 100, { status: 'completed' })
    ])
    availableGraphs.value = graphsRes.data.items
    availableExperiments.value = expsRes.data.items
  } catch (error) {
    console.error('Failed to fetch data sources:', error)
  }
}

const handleModeChange = () => {
  subgraph.value = null
  selectedNodeId.value = null
  if (viewMode.value === 'graph' && availableGraphs.value.length > 0) {
    selectedGraphId.value = availableGraphs.value[0].id
    loadGraphData()
  } else if (viewMode.value === 'prediction' && availableExperiments.value.length > 0) {
    selectedExperimentId.value = availableExperiments.value[0].id
    loadPredictionData()
  }
}

const loadGraphData = async () => {
  if (!selectedGraphId.value) return
  loading.value = true
  try {
    const res = await getSubgraph(selectedGraphId.value, limit.value, selectedNodeId.value || undefined)
    subgraph.value = res.data
  } catch (error) {
    ElMessage.error('无法加载图数据')
  } finally {
    loading.value = false
  }
}

const loadPredictionData = async () => {
  if (!selectedExperimentId.value) return
  loading.value = true
  try {
    const res = await getTopPredictions(selectedExperimentId.value, limit.value)
    subgraph.value = res.data
  } catch (error) {
    ElMessage.error('无法加载预测数据')
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  if (viewMode.value === 'graph') {
    loadGraphData()
  } else {
    loadPredictionData()
  }
}

const handleChartClick = (params: any) => {
  if (params.dataType === 'node') {
    selectedNodeId.value = params.data.id
  }
}

const clearSelection = () => {
  selectedNodeId.value = null
  refreshData()
}

const expandNode = () => {
  if (!selectedNodeId.value) return
  loadGraphData()
}

const resetFilters = () => {
  limit.value = 100
  layout.value = 'force'
  selectedNodeId.value = null
  refreshData()
}

const updateChart = () => {
  // ECharts component will automatically update via computed chartOption
}

// Lifecycle
onMounted(() => {
  fetchAvailableData()
})
</script>

<style lang="scss" scoped>
.network-viz {
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  
  h1 {
    font-size: 28px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }
  
  p {
    color: var(--text-secondary);
  }
}

.control-panel {
  margin-bottom: 20px;
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
  }
}

.node-info {
  margin-top: 10px;
  
  h4 {
    margin-bottom: 12px;
    font-size: 14px;
    color: var(--text-primary);
  }
  
  .node-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
  }
}

.empty-selection {
  margin-top: 20px;
  text-align: center;
  padding: 20px;
  background: var(--el-fill-color-light);
  border-radius: 4px;
}

.stats-card {
  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    
    .stat-item {
      text-align: center;
      padding: 10px;
      background: var(--el-fill-color-light);
      border-radius: 4px;
      
      .label {
        font-size: 12px;
        color: var(--text-secondary);
        margin-bottom: 4px;
      }
      
      .value {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-color-primary);
      }
    }
  }
}

.graph-card {
  height: calc(100vh - 200px);
  min-height: 600px;
  position: relative;
  
  .chart-container {
    height: 100%;
    width: 100%;
  }
  
  .graph-overlay {
    position: absolute;
    bottom: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.9);
    padding: 12px;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
    z-index: 10;
    
    .legend {
      display: flex;
      flex-direction: column;
      gap: 8px;
      
      .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        color: var(--text-secondary);
        
        .dot {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          
          &.drug { background: #409EFF; }
          &.disease { background: #67C23A; }
        }
        
        .line {
          width: 20px;
          height: 2px;
          
          &.original { background: #DCDFE6; }
          &.predicted { border-bottom: 2px dashed #F56C6C; height: 0; }
        }
      }
    }
  }
}

:deep(.el-card__body) {
  height: 100%;
}
</style>
