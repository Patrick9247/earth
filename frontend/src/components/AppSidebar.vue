<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()

// 跳转到钻孔管理页面
const goToAddDrillHole = () => {
  router.push('/drill-holes')
}

// 跳转到资源计算页面
const goToQuickCalc = () => {
  router.push('/calculation')
}

// 打开使用指南
const openGuide = () => {
  router.push('/settings')
}
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar-section">
      <h4 class="section-title">快捷操作</h4>
      <div class="quick-actions">
        <el-button type="primary" size="small" class="action-btn" @click="goToAddDrillHole">
          <el-icon><Plus /></el-icon>
          新建钻孔
        </el-button>
        <el-button type="success" size="small" class="action-btn" @click="goToQuickCalc">
          <el-icon><Cpu /></el-icon>
          快速计算
        </el-button>
      </div>
    </div>
    
    <div class="sidebar-section">
      <h4 class="section-title">系统状态</h4>
      <div class="status-item">
        <span class="status-label">数据库</span>
        <el-tag type="success" size="small">正常</el-tag>
      </div>
      <div class="status-item">
        <span class="status-label">GemPy</span>
        <el-tag type="success" size="small">就绪</el-tag>
      </div>
    </div>

    <div class="sidebar-section">
      <h4 class="section-title">帮助文档</h4>
      <el-link type="primary" :underline="false" class="guide-link" @click="openGuide">
        <el-icon><Document /></el-icon>
        使用指南
      </el-link>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 240px;
  background: #fff;
  padding: 20px;
  border-right: 1px solid #ebeef5;
  overflow-y: auto;
}

.sidebar-section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #909399;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #ebeef5;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-btn {
  width: 100%;
  justify-content: flex-start;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.status-label {
  color: #606266;
  font-size: 14px;
}

.guide-link {
  cursor: pointer;
  font-size: 14px;
}

.guide-link:hover {
  color: #409eff;
}
</style>
