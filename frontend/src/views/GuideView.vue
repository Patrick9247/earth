<script setup lang="ts">
// 使用指南页面
</script>

<template>
  <div class="guide-view">
    <h1 class="page-title">📖 使用指南</h1>
    
    <div class="guide-content">
      <!-- 系统概述 -->
      <section class="guide-section">
        <h2>一、系统概述</h2>
        <p class="intro">
          地热流体资源建模系统是一个集三维地质建模、资源计算和数据管理于一体的综合性平台。
          系统基于 <strong>GemPy</strong> 地质建模引擎和 <strong>Three.js</strong> 可视化技术，
          为地热资源勘探开发提供专业的技术支撑。
        </p>
        
        <div class="feature-grid">
          <div class="feature-item">
            <el-icon :size="32" color="#409eff"><DataAnalysis /></el-icon>
            <h4>三维地质建模</h4>
            <p>构建三维地质结构模型，可视化展示地层分布</p>
          </div>
          <div class="feature-item">
            <el-icon :size="32" color="#67c23a"><Cpu /></el-icon>
            <h4>资源计算</h4>
            <p>精确计算地热储层的热含量和发电潜力</p>
          </div>
          <div class="feature-item">
            <el-icon :size="32" color="#e6a23c"><TrendCharts /></el-icon>
            <h4>数据管理</h4>
            <p>管理钻孔、地质层数据，支持数据导出</p>
          </div>
          <div class="feature-item">
            <el-icon :size="32" color="#f56c6c"><Document /></el-icon>
            <h4>结果分析</h4>
            <p>查看历史计算结果，生成分析报告</p>
          </div>
        </div>
      </section>

      <!-- 快速开始 -->
      <section class="guide-section">
        <h2>二、快速开始</h2>
        <el-steps direction="vertical" :active="5">
          <el-step title="准备地质数据">
            <template #description>
              <div class="step-content">
                <p>在 <router-link to="/layers">地质层管理</router-link> 页面添加地质层信息，包括：</p>
                <ul>
                  <li>地层名称和类型（沉积层、储层、盖层、基岩等）</li>
                  <li>顶底板深度（单位：米）</li>
                  <li>孔隙度参数（0-0.5）</li>
                  <li>地层颜色标识</li>
                </ul>
              </div>
            </template>
          </el-step>
          
          <el-step title="录入钻孔数据">
            <template #description>
              <div class="step-content">
                <p>在 <router-link to="/drill-holes">钻孔数据</router-link> 页面录入钻孔信息：</p>
                <ul>
                  <li>钻孔编号/名称</li>
                  <li>地理位置坐标（X, Y）</li>
                  <li>钻孔深度和温度测量值</li>
                </ul>
              </div>
            </template>
          </el-step>
          
          <el-step title="构建地质模型">
            <template #description>
              <div class="step-content">
                <p>在 <router-link to="/model">地质建模</router-link> 页面：</p>
                <ul>
                  <li>设置建模范围（X、Y、Z 方向的边界）</li>
                  <li>选择网格分辨率（20-100）</li>
                  <li>点击"生成地质模型"按钮</li>
                  <li>在 3D 视图中查看建模结果</li>
                </ul>
                <el-alert type="info" :closable="false" style="margin-top: 12px;">
                  <template #title>3D 视图操作</template>
                  左键拖拽旋转 | 右键拖拽平移 | 滚轮缩放
                </el-alert>
              </div>
            </template>
          </el-step>
          
          <el-step title="计算资源潜力">
            <template #description>
              <div class="step-content">
                <p>在 <router-link to="/calculation">资源计算</router-link> 页面：</p>
                <ul>
                  <li><strong>快速计算</strong>：输入储层体积、温度、孔隙度快速估算</li>
                  <li><strong>网格计算</strong>：将区域划分为网格，逐格计算后汇总</li>
                </ul>
                <p>计算结果包含：</p>
                <ul>
                  <li>总热含量（EJ，艾焦耳）</li>
                  <li>可采热量（EJ）</li>
                  <li>发电潜力（MW，兆瓦）</li>
                  <li>开采年限</li>
                </ul>
              </div>
            </template>
          </el-step>
          
          <el-step title="分析计算结果">
            <template #description>
              <div class="step-content">
                <p>在 <router-link to="/results">计算结果</router-link> 页面：</p>
                <ul>
                  <li>查看历史计算记录</li>
                  <li>对比不同方案的计算结果</li>
                  <li>导出数据报表</li>
                </ul>
              </div>
            </template>
          </el-step>
        </el-steps>
      </section>

      <!-- 功能详解 -->
      <section class="guide-section">
        <h2>三、功能模块详解</h2>
        
        <h3>3.1 地质层管理</h3>
        <div class="module-desc">
          <p>地质层是构建三维地质模型的基础数据。系统支持以下操作：</p>
          <el-table :data="layerFields" size="small" border>
            <el-table-column prop="field" label="字段名称" width="120" />
            <el-table-column prop="desc" label="说明" />
            <el-table-column prop="unit" label="单位" width="80" />
          </el-table>
        </div>

        <h3>3.2 钻孔数据管理</h3>
        <div class="module-desc">
          <p>钻孔数据用于确定地质界面的空间位置，是建模的关键输入。</p>
          <el-table :data="drillFields" size="small" border>
            <el-table-column prop="field" label="字段名称" width="120" />
            <el-table-column prop="desc" label="说明" />
            <el-table-column prop="unit" label="单位" width="80" />
          </el-table>
        </div>

        <h3>3.3 三维地质建模</h3>
        <div class="module-desc">
          <p>系统基于 GemPy 引擎进行三维地质建模，主要流程：</p>
          <ol>
            <li>根据钻孔数据插值生成地质界面</li>
            <li>基于地层序列构建三维模型</li>
            <li>使用 Three.js 进行实时渲染</li>
          </ol>
          <div class="tip-box">
            <strong>💡 提示：</strong>网格分辨率越高，模型精度越好，但计算时间也会增加。建议先用低分辨率预览，确认无误后再提高分辨率。
          </div>
        </div>

        <h3>3.4 资源计算</h3>
        <div class="module-desc">
          <p>系统采用体积法计算地热资源量，计算公式：</p>
          <div class="formula">
            Q = V × φ × ρ × c × (T - T₀)
          </div>
          <p>其中：</p>
          <ul>
            <li><strong>Q</strong>：热含量（J）</li>
            <li><strong>V</strong>：储层体积（m³）</li>
            <li><strong>φ</strong>：孔隙度</li>
            <li><strong>ρ</strong>：流体密度（kg/m³）</li>
            <li><strong>c</strong>：比热容（J/kg·K）</li>
            <li><strong>T</strong>：储层温度（°C）</li>
            <li><strong>T₀</strong>：基准温度（通常取 25°C）</li>
          </ul>
        </div>
      </section>

      <!-- 3D 可视化 -->
      <section class="guide-section">
        <h2>四、3D 可视化操作</h2>
        <div class="viz-guide">
          <el-row :gutter="20">
            <el-col :span="12">
              <div class="viz-card">
                <h4>🎮 视图控制</h4>
                <ul>
                  <li><strong>旋转</strong>：按住左键拖拽</li>
                  <li><strong>平移</strong>：按住右键拖拽</li>
                  <li><strong>缩放</strong>：滚动鼠标滚轮</li>
                  <li><strong>重置</strong>：点击"重置视图"按钮</li>
                </ul>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="viz-card">
                <h4>📊 坐标系统</h4>
                <ul>
                  <li><span style="color:#ff4444">●</span> <strong>X轴（红色）</strong>：西向</li>
                  <li><span style="color:#4488ff">●</span> <strong>Y轴（蓝色）</strong>：深度（向下为正）</li>
                  <li><span style="color:#44ff44">●</span> <strong>Z轴（绿色）</strong>：北向</li>
                </ul>
              </div>
            </el-col>
          </el-row>
          <el-row :gutter="20" style="margin-top: 16px;">
            <el-col :span="12">
              <div class="viz-card">
                <h4>🎨 图例说明</h4>
                <div class="legend-demo">
                  <span class="legend-item"><span class="color-box" style="background:#4CAF50"></span> 地表层</span>
                  <span class="legend-item"><span class="color-box" style="background:#FFC107"></span> 沉积层</span>
                  <span class="legend-item"><span class="color-box" style="background:#FF9800"></span> 储层</span>
                  <span class="legend-item"><span class="color-box" style="background:#E91E63"></span> 基底</span>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="viz-card">
                <h4>🌡️ 温度图例</h4>
                <div class="legend-demo">
                  <span class="legend-item"><span class="color-box" style="background:#4CAF50"></span> &lt;100°C</span>
                  <span class="legend-item"><span class="color-box" style="background:#FFC107"></span> 100-150°C</span>
                  <span class="legend-item"><span class="color-box" style="background:#FF9800"></span> 150-200°C</span>
                  <span class="legend-item"><span class="color-box" style="background:#F44336"></span> &gt;200°C</span>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </section>

      <!-- 系统设置 -->
      <section class="guide-section">
        <h2>五、系统设置</h2>
        <p>在 <router-link to="/settings">系统设置</router-link> 页面可以配置：</p>
        <ul>
          <li><strong>默认计算参数</strong>：孔隙度、采收率、利用效率、开采年限</li>
          <li><strong>模型配置</strong>：默认网格分辨率</li>
          <li><strong>物理常数</strong>：水密度、岩石密度、比热容等</li>
          <li><strong>数据导出</strong>：导出系统数据为 JSON/CSV 格式</li>
        </ul>
      </section>

      <!-- 常见问题 -->
      <section class="guide-section">
        <h2>六、常见问题</h2>
        <el-collapse>
          <el-collapse-item title="Q: 为什么地质模型显示不正确？" name="1">
            <p>A: 请检查以下内容：</p>
            <ul>
              <li>确保已添加地质层和钻孔数据</li>
              <li>检查钻孔深度是否在建模范围内</li>
              <li>尝试调整网格分辨率</li>
              <li>刷新页面重新加载</li>
            </ul>
          </el-collapse-item>
          <el-collapse-item title="Q: 计算结果为 0 是什么原因？" name="2">
            <p>A: 可能的原因：</p>
            <ul>
              <li>输入的温度值过低（接近基准温度 25°C）</li>
              <li>储层体积过小</li>
              <li>孔隙度设置为 0</li>
            </ul>
          </el-collapse-item>
          <el-collapse-item title="Q: 如何导出计算结果？" name="3">
            <p>A: 在计算结果页面，点击操作列的"详情"按钮可查看详细数据，或在系统设置页面使用"数据导出"功能导出所有数据。</p>
          </el-collapse-item>
          <el-collapse-item title="Q: 数据存储在哪里？" name="4">
            <p>A: 系统使用 MySQL 数据库存储数据，同时也支持本地存储（LocalStorage）保存用户设置。首次使用时需确保数据库连接正常。</p>
          </el-collapse-item>
        </el-collapse>
      </section>

      <!-- 技术支持 -->
      <section class="guide-section">
        <h2>七、技术支持</h2>
        <div class="support-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="技术栈">Vue 3 + FastAPI + GemPy + Three.js</el-descriptions-item>
            <el-descriptions-item label="数据库">MySQL 8.0</el-descriptions-item>
            <el-descriptions-item label="更新日期">2026年3月</el-descriptions-item>
          </el-descriptions>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts">
export default {
  data() {
    return {
      layerFields: [
        { field: '名称', desc: '地层名称，如"第四系覆盖层"', unit: '-' },
        { field: '类型', desc: '地层类型（沉积层/储层/盖层/基岩）', unit: '-' },
        { field: '顶板深度', desc: '地层顶部埋深', unit: 'm' },
        { field: '底板深度', desc: '地层底部埋深', unit: 'm' },
        { field: '孔隙度', desc: '岩石孔隙体积与总体积之比', unit: '-' },
        { field: '颜色', desc: '可视化显示颜色', unit: '-' },
      ],
      drillFields: [
        { field: '钻孔编号', desc: '唯一标识符，如 ZK-001', unit: '-' },
        { field: 'X坐标', desc: '东西方向位置', unit: 'm' },
        { field: 'Y坐标', desc: '南北方向位置', unit: 'm' },
        { field: '深度', desc: '钻孔总深度', unit: 'm' },
        { field: '温度', desc: '孔底测量温度', unit: '°C' },
      ]
    }
  }
}
</script>

<style scoped>
.guide-view {
  max-width: 1200px;
}

.guide-content {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
}

.guide-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #ebeef5;
}

.guide-section:last-child {
  border-bottom: none;
}

.guide-section h2 {
  color: #303133;
  font-size: 20px;
  margin-bottom: 16px;
  padding-left: 12px;
  border-left: 4px solid #409eff;
}

.guide-section h3 {
  color: #303133;
  font-size: 16px;
  margin: 20px 0 12px;
}

.intro {
  line-height: 1.8;
  color: #606266;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
}

.feature-item {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.3s;
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.feature-item h4 {
  margin: 12px 0 8px;
  font-size: 14px;
}

.feature-item p {
  color: #909399;
  font-size: 12px;
  margin: 0;
}

.step-content {
  padding: 8px 0;
}

.step-content ul, .step-content ol {
  padding-left: 20px;
  margin: 8px 0;
}

.step-content li {
  margin: 6px 0;
  color: #606266;
}

.step-content a {
  color: #409eff;
  text-decoration: none;
}

.step-content a:hover {
  text-decoration: underline;
}

.module-desc {
  margin: 12px 0;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
}

.formula {
  font-family: 'Times New Roman', serif;
  font-size: 20px;
  text-align: center;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
  margin: 16px 0;
  color: #409eff;
}

.tip-box {
  padding: 12px 16px;
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
  border-radius: 4px;
  margin-top: 12px;
}

.viz-guide {
  margin-top: 16px;
}

.viz-card {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  height: 100%;
}

.viz-card h4 {
  margin: 0 0 12px;
  font-size: 14px;
}

.viz-card ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.viz-card li {
  padding: 6px 0;
  font-size: 13px;
  color: #606266;
}

.legend-demo {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.color-box {
  width: 16px;
  height: 16px;
  border-radius: 4px;
}

.support-info {
  max-width: 500px;
}
</style>
