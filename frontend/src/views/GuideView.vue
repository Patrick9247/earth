<template>
  <div class="guide-container">
    <h1 class="page-title">使用指南</h1>

    <!-- 计算方法 -->
    <section class="guide-section">
      <h2 class="section-title">地热流体资源量计算方法</h2>
      <p class="section-desc">本系统采用一种不规则热储层多相态地热流体资源量计算方法。</p>

      <div class="method-steps">
        <el-steps :active="5" direction="vertical">
          <el-step title="数据收集" description="收集研究区域的钻孔空间信息、热储层分层数据、钻孔测温曲线、孔口压力数据以及岩石孔隙度数据" />
          <el-step title="模型构建" description="基于钻孔空间信息与热储层分层数据构建热储层的三维地质构造模型，并进行网格划分生成热储层三维地质构造网格模型" />
          <el-step title="参数模型" description="建立孔隙度模型、压力模型、温度场模型，获得每个网格的孔隙度、压力和温度" />
          <el-step title="相态判定与密度校正" description="引入相态判定曲线方程划分气液网格集，并确定每个网格中地热流体的密度" />
          <el-step title="资源量计算" description="基于每个网格的孔隙度、温度以及地热流体的密度，带入资源量公式计算地热资源量" />
        </el-steps>
      </div>
    </section>

    <!-- 相态判定 -->
    <section class="guide-section">
      <h2 class="section-title">相态判定</h2>
      <p class="section-desc">引入相态判定曲线方程，将每个网格的温度与对应的沸点温度进行比较，划分为气液共存网格集和液态水网格集。</p>

      <div class="formula-block">
        <h3>相态判定曲线方程（饱和温度）</h3>
        <div class="formula">
          T<sub>isat</sub> = 0.95 × P<sub>i</sub> + 26.44 <span class="formula-condition">（P<sub>i</sub> ≤ 101.325 kPa）</span>
        </div>
        <div class="formula">
          T<sub>isat</sub> = 0.04 × P<sub>i</sub> + 132.01 <span class="formula-condition">（P<sub>i</sub> &gt; 101.325 kPa）</span>
        </div>
        <p class="formula-desc">其中：T<sub>isat</sub> 为第 i 个网格的饱和温度（°C），P<sub>i</sub> 为第 i 个网格的压力（kPa）</p>
      </div>

      <div class="formula-block">
        <h3>密度校正公式</h3>
        <div class="formula">
          ρ<sub>i</sub> = 137.1358 × e<sup>(A)</sup> + 139.3560 × e<sup>(B)</sup> + 769.9024
        </div>
        <div class="formula-sub">
          A = -(P<sub>i</sub> - 163278.7315)² / (6.613 × 10<sup>10</sup>)
        </div>
        <div class="formula-sub">
          B = -(T<sub>i</sub> - 4.1171)² / 29947.659
        </div>
        <p class="formula-desc">其中：ρ<sub>i</sub> 为第 i 个网格中地热流体的密度（kg/m³），T<sub>i</sub> 为第 i 个网格的温度（°C），P<sub>i</sub> 为第 i 个网格的压力（Pa），e 为自然常数</p>
        <p class="formula-note">注意：密度公式中压力单位为 Pa（帕斯卡），系统输入压力单位为 kPa，计算时需转换：1 kPa = 1000 Pa</p>
      </div>

      <div class="formula-block">
        <h3>相态判定规则</h3>
        <ul class="rule-list">
          <li><strong>液态水网格集：</strong>当网格中的温度小于沸点温度时（T<sub>i</sub> &lt; T<sub>iboil</sub>），网格中的地热流体视为液态水</li>
          <li><strong>气液共存网格集：</strong>当网格中的温度等于沸点温度时（T<sub>i</sub> = T<sub>iboil</sub>），网格中的地热流体视为气液共存</li>
          <li><strong>气态网格集：</strong>当网格中的温度大于沸点温度时（T<sub>i</sub> &gt; T<sub>iboil</sub>），网格中的地热流体视为气态（过热蒸汽）</li>
        </ul>
      </div>
    </section>

    <!-- 液态水网格集资源量计算 -->
    <section class="guide-section">
      <h2 class="section-title">液态水网格集资源量</h2>

      <div class="formula-block">
        <h3>液态地热流体资源量公式</h3>
        <div class="formula">
          Q<sub>1</sub> = Σ<sub>i=1</sub><sup>N</sup> [ φ<sub>i</sub> × V<sub>i</sub> × ρ<sub>i</sub> × C<sub>w</sub> × (T<sub>i</sub> - T<sub>0</sub>) ]
        </div>
        <p class="formula-desc">
          其中：Q<sub>1</sub> 为液态地热流体的资源量（kJ），φ<sub>i</sub> 为第 i 网格的孔隙度，V<sub>i</sub> 为第 i 网格的体积（m³），ρ<sub>i</sub> 为第 i 网格的地热流体密度（kg/m³），C<sub>w</sub> 为地热水的比热容 [kJ/(kg·°C)]，T<sub>i</sub> 为第 i 网格的温度（°C），T<sub>0</sub> 为参考温度（°C），i ∈ [1, N]
        </p>
      </div>
    </section>

    <!-- 气液共存网格集资源量计算 -->
    <section class="guide-section">
      <h2 class="section-title">气液共存网格集资源量</h2>
      <p class="section-desc">气液共存网格集中的地热资源总量 Q<sub>4</sub> 由液态资源量 Q<sub>2</sub> 和蒸汽资源量 Q<sub>3</sub> 组成。</p>

      <div class="formula-block">
        <h3>地热资源总量</h3>
        <div class="formula">
          Q<sub>4</sub> = Q<sub>2</sub> + Q<sub>3</sub>
        </div>
        <p class="formula-desc">其中：Q<sub>4</sub> 为热储层的地热资源总量，Q<sub>2</sub> 为气液共存时液态地热流体的资源量，Q<sub>3</sub> 为气液共存时水蒸汽的资源量</p>
      </div>

      <div class="formula-block">
        <h3>液态地热流体资源量 Q<sub>2</sub></h3>
        <div class="formula">
          Q<sub>2</sub> = Σ<sub>i=1</sub><sup>N</sup> [ φ<sub>i</sub> × V<sub>i</sub> × (1 - ρ<sub>i</sub> × v<sub>g</sub>) / (v<sub>p</sub> - v<sub>g</sub>) × C<sub>w</sub> × (T<sub>iboil</sub> - T<sub>0</sub>) ]
        </div>
        <p class="formula-desc">其中：v<sub>g</sub> 为水蒸气比容（m³/kg），v<sub>p</sub> 为水的比容（m³/kg），i ∈ [1, N]</p>
      </div>

      <div class="formula-block">
        <h3>水蒸汽资源量 Q<sub>3</sub></h3>
        <div class="formula">
          Q<sub>3</sub> = Σ<sub>i=1</sub><sup>N</sup> [ φ<sub>i</sub> × V<sub>i</sub> × (ρ<sub>i</sub> - (1 - ρ<sub>i</sub> × v<sub>g</sub>) / (v<sub>p</sub> - v<sub>g</sub>)) × [C<sub>w</sub> × (T<sub>iboil</sub> - T<sub>0</sub>) + L<sub>v</sub> + C<sub>v</sub> × (T<sub>i</sub> - T<sub>iboil</sub>)] ]
        </div>
        <p class="formula-desc">
          其中：L<sub>v</sub> 为气化潜热（kJ/kg），C<sub>v</sub> 为气体的比热容 [kJ/(kg·°C)]，i ∈ [1, N]
        </p>
      </div>
    </section>

    <!-- 气态网格集资源量计算 -->
    <section class="guide-section">
      <h2 class="section-title">气态网格集资源量</h2>
      <p class="section-desc">当网格温度大于饱和温度时，地热流体为过热蒸汽，按气态计算资源量。</p>

      <div class="formula-block">
        <h3>气态资源量公式</h3>
        <div class="formula">
          Q<sub>5</sub> = Σ<sub>i=1</sub><sup>N</sup> [ φ<sub>i</sub> × V<sub>i</sub> × ρ<sub>i</sub> × (C<sub>w</sub> × (T<sub>isat</sub> - T<sub>0</sub>) + L<sub>v</sub> + C<sub>v</sub> × (T<sub>i</sub> - T<sub>isat</sub>)) ]
        </div>
        <p class="formula-desc">
          其中：Q<sub>5</sub> 为气态地热流体的资源量（kJ），ρ<sub>i</sub> 为第i个网格中地热流体的密度（kg/m³），T<sub>isat</sub> 为饱和温度（°C），T<sub>i</sub> - T<sub>isat</sub> 为过热度（°C）
        </p>
      </div>
    </section>

    <!-- 总资源量计算 -->
    <section class="guide-section">
      <h2 class="section-title">总地热资源量</h2>
      <p class="section-desc">总地热资源量为所有相态网格集资源量之和。</p>

      <div class="formula-block highlight">
        <h3>总资源量公式</h3>
        <div class="formula">
          Q<sub>总</sub> = Q<sub>1</sub> + Q<sub>4</sub> + Q<sub>5</sub>
        </div>
        <p class="formula-desc">其中：Q<sub>1</sub> 为液态水网格集的资源量，Q<sub>4</sub> 为气液共存网格集的资源总量，Q<sub>5</sub> 为气态网格集的资源量</p>
      </div>
    </section>

    <!-- 参数说明 -->
    <section class="guide-section">
      <h2 class="section-title">参数说明</h2>
      <el-table :data="paramTableData" border style="width: 100%">
        <el-table-column prop="symbol" label="符号" width="100" />
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="unit" label="单位" width="100" />
        <el-table-column prop="description" label="说明" />
      </el-table>
    </section>

    <!-- 技术支持 -->
    <section class="guide-section">
      <h2 class="section-title">技术支持</h2>
      <ul class="tech-list">
        <li><strong>数据库：</strong>SQLite</li>
        <li><strong>建模库：</strong>GemPy</li>
        <li><strong>开发团队：</strong>地热资源研究团队</li>
        <li><strong>联系方式：</strong>请通过系统反馈功能联系管理员</li>
      </ul>
    </section>
  </div>
</template>

<script lang="ts">
export default {
  data() {
    return {
      paramTableData: [
        { symbol: 'T<sub>iboil</sub>', name: '沸点温度', unit: '°C', description: '第i个网格对应的沸点温度' },
        { symbol: 'P<sub>i</sub>', name: '压力', unit: 'kPa', description: '第i个网格的压力' },
        { symbol: 'ρ<sub>i</sub>', name: '流体密度', unit: 'kg/m³', description: '第i个网格中地热流体的密度' },
        { symbol: 'T<sub>i</sub>', name: '温度', unit: '°C', description: '第i个网格的温度' },
        { symbol: 'φ<sub>i</sub>', name: '孔隙度', unit: '-', description: '第i个网格的孔隙度' },
        { symbol: 'V<sub>i</sub>', name: '网格体积', unit: 'm³', description: '第i个网格的体积' },
        { symbol: 'C<sub>w</sub>', name: '比热容', unit: 'kJ/(kg·°C)', description: '地热水的比热容' },
        { symbol: 'C<sub>v</sub>', name: '气体比热容', unit: 'kJ/(kg·°C)', description: '气体的比热容' },
        { symbol: 'T<sub>0</sub>', name: '参考温度', unit: '°C', description: '地热流体排放参考温度' },
        { symbol: 'v<sub>g</sub>', name: '水蒸气比容', unit: 'm³/kg', description: '水蒸气比容' },
        { symbol: 'v<sub>p</sub>', name: '水的比容', unit: 'm³/kg', description: '水的比容' },
        { symbol: 'L<sub>v</sub>', name: '气化潜热', unit: 'kJ/kg', description: '气化潜热' },
        { symbol: 'e', name: '自然常数', unit: '-', description: '自然对数的底数，约等于2.71828' },
      ]
    }
  }
}
</script>

<style scoped>
.guide-container {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 32px;
}

.guide-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--primary-color);
}

.section-desc {
  color: #666;
  line-height: 1.8;
  margin-bottom: 20px;
}

.method-steps {
  padding: 10px 0;
}

.formula-block {
  background: #f8f9fa;
  border-left: 4px solid var(--primary-color);
  padding: 16px 20px;
  margin-bottom: 20px;
  border-radius: 0 8px 8px 0;
}

.formula-block h3 {
  font-size: 16px;
  color: var(--text-color);
  margin-bottom: 12px;
}

.formula-block.highlight {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.formula-block.highlight h3,
.formula-block.highlight .formula,
.formula-block.highlight .formula-desc,
.formula-block.highlight .formula sub,
.formula-block.highlight .formula sup {
  color: rgb(29, 6, 112) !important;
}

.formula {
  font-size: 18px;
  font-family: 'Times New Roman', serif;
  color: var(--primary-color);
  font-weight: 600;
  margin: 12px 0;
  padding: 12px;
  background: white;
  border-radius: 6px;
  text-align: center;
}

.formula-sub {
  font-size: 15px;
  font-family: 'Times New Roman', serif;
  color: #666;
  margin: 8px 0 8px 20px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
  display: inline-block;
}

.formula-desc {
  color: #666;
  font-size: 14px;
  line-height: 1.6;
  margin-top: 12px;
}

.rule-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.rule-list li {
  padding: 12px 16px;
  margin-bottom: 8px;
  background: white;
  border-radius: 6px;
  line-height: 1.6;
}

.rule-list li:last-child {
  margin-bottom: 0;
}

.tech-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tech-list li {
  padding: 12px 0;
  border-bottom: 1px solid #eee;
  line-height: 1.6;
}

.tech-list li:last-child {
  border-bottom: none;
}

:deep(.el-step__title) {
  font-weight: 600;
}

:deep(.el-table) {
  font-size: 14px;
}
</style>
