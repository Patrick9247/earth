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
@import "@/styles/app.css";
</style>
