<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="layout">
    <nav class="nav">
      <RouterLink to="/" class="logo">金价助手</RouterLink>
      <div class="nav-links">
        <RouterLink to="/">首页</RouterLink>
        <RouterLink to="/calculate">计算</RouterLink>
        <RouterLink to="/rules">规则</RouterLink>
      </div>
    </nav>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 1.5rem;
  height: 52px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}

.logo {
  font-weight: 600;
  font-size: 0.95rem;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
}

.nav-links a {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.nav-links a.router-link-active {
  color: var(--text);
}

.main {
  flex: 1;
  max-width: 960px;
  width: 100%;
  margin: 0 auto;
  padding: 2rem 1.25rem;
}
</style>
