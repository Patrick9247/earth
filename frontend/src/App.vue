<script setup lang="ts">
import { RouterView } from 'vue-router'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'
</script>

<template>
  <div class="app-container">
    <AppHeader />
    <div class="main-wrapper">
      <AppSidebar />
      <main class="content-area">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.main-wrapper {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>
