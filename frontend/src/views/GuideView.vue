<script setup lang="ts">
// 使用指南页面 - 资源计算公式
</script>

<template>
  <div class="guide-view">
    <h1 class="page-title">使用指南</h1>
    
    <div class="guide-content">
      <!-- 相态判别 -->
      <section class="guide-section">
        <h2>相态判别</h2>
        <p class="intro">
          地热流体相态根据温度和压力条件确定，主要依据饱和水蒸气曲线进行判别：
        </p>
        
        <div class="formula-section">
          <h4>相态判别原则</h4>
          <ul>
            <li><strong>液态（热水型）</strong>：T &lt; T<sub>饱</sub>（温度低于当前压力下的饱和温度）</li>
            <li><strong>气态（蒸汽型）</strong>：T ≥ T<sub>饱</sub>（温度高于或等于当前压力下的饱和温度）</li>
            <li><strong>两相态</strong>：介于临界点附近，流体以汽液混合物形式存在</li>
          </ul>
          
          <h4>饱和温度计算（近似公式）</h4>
          <div class="formula">
            T<sub>饱</sub> = 100 × P<sup>0.25</sup> + 3.5 × P + 0.02 × P²
          </div>
          <p>其中：</p>
          <ul>
            <li><strong>T<sub>饱</sub></strong>：饱和温度（°C）</li>
            <li><strong>P</strong>：绝对压力（bar），P = ρgh/10⁵ + P<sub>地表</sub></li>
            <li><strong>ρ</strong>：上覆岩层平均密度（kg/m³），约 2500-2700 kg/m³</li>
            <li><strong>g</strong>：重力加速度，9.81 m/s²</li>
            <li><strong>h</strong>：储层埋深（m）</li>
          </ul>
          
          <h4>临界点参考</h4>
          <el-table :data="criticalParams" size="small" border>
            <el-table-column prop="param" label="参数" width="120" />
            <el-table-column prop="value" label="数值" width="120" />
            <el-table-column prop="unit" label="单位" width="100" />
          </el-table>
          
          <h4>简易判别方法</h4>
          <ul>
            <li><strong>埋深 &lt; 1000m</strong>：通常为液态，温度 &lt; 180°C</li>
            <li><strong>埋深 1000-3000m</strong>：可为液态或两相态，温度 150-250°C</li>
            <li><strong>埋深 &gt; 3000m</strong>：可为气态或两相态，温度 &gt; 200°C</li>
          </ul>
          <el-alert type="tip" :closable="false" show-icon style="margin-top: 12px;">
            <template #title>实际判别建议</template>
            建议结合地质构造、温压测试数据，综合确定相态类型。
          </el-alert>
        </div>
      </section>

      <!-- 资源计算公式 -->
      <section class="guide-section">
        <h2>资源计算公式</h2>
        <p class="intro">
          系统采用体积法计算地热资源量，根据相态不同采用不同的计算公式：
        </p>
        
        <el-tabs type="border-card" class="formula-tabs">
          <el-tab-pane label="液态（热水型）">
            <div class="formula-section">
              <h4>热含量计算</h4>
              <div class="formula">
                Q = V × φ × ρw × cw × (T - T₀)
              </div>
              <p>其中：</p>
              <ul>
                <li><strong>Q</strong>：热含量（J）</li>
                <li><strong>V</strong>：储层体积（m³）</li>
                <li><strong>φ</strong>：孔隙度</li>
                <li><strong>ρw</strong>：水的密度（kg/m³），常温下约 1000 kg/m³</li>
                <li><strong>cw</strong>：水的比热容（J/kg·K），约 4186 J/kg·K</li>
                <li><strong>T</strong>：储层平均温度（°C）</li>
                <li><strong>T₀</strong>：基准温度（通常取 25°C，即排放温度）</li>
              </ul>
              <h4>发电潜力计算</h4>
              <div class="formula">
                E = Q × R × η / (L × 10⁶)
              </div>
              <p>其中：</p>
              <ul>
                <li><strong>E</strong>：发电潜力（MW）</li>
                <li><strong>Q</strong>：可采热量（J）= Q总 × 采收率</li>
                <li><strong>R</strong>：采收率（通常 0.05-0.25）</li>
                <li><strong>η</strong>：地热发电效率（通常 0.10-0.18）</li>
                <li><strong>L</strong>：开采年限（秒），通常取 30 年</li>
              </ul>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="气态（蒸汽型）">
            <div class="formula-section">
              <h4>热含量计算</h4>
              <div class="formula">
                Q = V × φ × ρs × (hs - h₂)
              </div>
              <p>其中：</p>
              <ul>
                <li><strong>Q</strong>：热含量（J）</li>
                <li><strong>V</strong>：储层体积（m³）</li>
                <li><strong>φ</strong>：孔隙度</li>
                <li><strong>ρs</strong>：蒸汽密度（kg/m³），随温度压力变化</li>
                <li><strong>hs</strong>：饱和蒸汽比焓（kJ/kg），查 IAPWS-IF97 表</li>
                <li><strong>h₂</strong>：排放状态下蒸汽比焓（kJ/kg）</li>
              </ul>
              <h4>常用蒸汽参数（参考）</h4>
              <el-table :data="steamParams" size="small" border>
                <el-table-column prop="temp" label="温度(°C)" width="100" />
                <el-table-column prop="pressure" label="压力(MPa)" width="100" />
                <el-table-column prop="enthalpy" label="比焓(kJ/kg)" width="120" />
                <el-table-column prop="density" label="密度(kg/m³)" width="120" />
              </el-table>
            </div>
          </el-tab-pane>
          
          <el-tab-pane label="干热岩型">
            <div class="formula-section">
              <h4>热含量计算</h4>
              <div class="formula">
                Q = V × ρr × cr × (T - T₀)
              </div>
              <p>其中：</p>
              <ul>
                <li><strong>Q</strong>：热含量（J）</li>
                <li><strong>V</strong>：热储体积（m³）</li>
                <li><strong>ρr</strong>：岩石密度（kg/m³），花岗岩约 2700 kg/m³</li>
                <li><strong>cr</strong>：岩石比热容（J/kg·K），约 800-1000 J/kg·K</li>
                <li><strong>T</strong>：岩体平均温度（°C）</li>
                <li><strong>T₀</strong>：冷却后温度（°C），通常取 50-80°C</li>
              </ul>
              <h4>增强型地热系统(EGS)</h4>
              <div class="formula">
                Q = V × [(1-φ)ρr·cr + φ·ρw·cw] × (T - T₀)
              </div>
              <p>此公式综合考虑了岩石骨架和孔隙流体的热容。</p>
            </div>
          </el-tab-pane>
        </el-tabs>
        
        <el-alert type="info" :closable="false" style="margin-top: 16px;">
          <template #title>单位换算提示</template>
          1 EJ = 10¹⁸ J | 1 TJ = 10¹² J | 1 PJ = 10¹⁵ J<br/>
          发电潜力(MW) = 可采热量(J) / (开采年限×365×24×3600)
        </el-alert>
      </section>

      <!-- 技术支持 -->
      <section class="guide-section">
        <h2>技术支持</h2>
        <div class="support-info">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统版本">v1.0.0</el-descriptions-item>
            <el-descriptions-item label="技术栈">Vue 3 + FastAPI + Three.js</el-descriptions-item>
            <el-descriptions-item label="数据库">SQLite</el-descriptions-item>
            <el-descriptions-item label="更新日期">2026年4月</el-descriptions-item>
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
      steamParams: [
        { temp: '150', pressure: '0.476', enthalpy: '2776.4', density: '2.547' },
        { temp: '180', pressure: '1.002', enthalpy: '2776.6', density: '5.147' },
        { temp: '200', pressure: '1.554', enthalpy: '2792.2', density: '7.865' },
        { temp: '220', pressure: '2.318', enthalpy: '2804.3', density: '11.61' },
        { temp: '250', pressure: '3.976', enthalpy: '2820.7', density: '19.78' },
        { temp: '300', pressure: '8.581', enthalpy: '2748.7', density: '46.46' },
      ],
      criticalParams: [
        { param: '临界温度', value: '374.15', unit: '°C' },
        { param: '临界压力', value: '22.06', unit: 'MPa' },
        { param: '临界密度', value: '322', unit: 'kg/m³' },
        { param: '三相点温度', value: '0.01', unit: '°C' },
        { param: '三相点压力', value: '0.0006', unit: 'MPa' },
      ]
    }
  }
}
</script>

<style scoped>
@import "@/styles/guide-view.css";
</style>
