<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

// 跳转到钻孔数据页面
const goToAddDrillHole = () => {
  router.push('/drill-data')
}

// 跳转到资源计算页面
const goToQuickCalc = () => {
  router.push('/calculation')
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
    </div>

  </aside>
</template>

<style scoped>
@import "@/styles/app-sidebar.css";
</style>
