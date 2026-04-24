<template>
  <div class="app">
    <router-view v-slot="{ Component }">
      <template v-if="$route.meta.keepAlive">
        <keep-alive>
          <component :is="Component" />
        </keep-alive>
      </template>
      <template v-else>
        <component :is="Component" />
      </template>
    </router-view>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue';
import { showToast } from 'vant';
import { App as CapacitorApp } from '@capacitor/app';

let lastBackPressTime = 0;

const handleBackButton = async (event) => {
  const currentTime = Date.now();
  if (currentTime - lastBackPressTime < 2000) {
    // 2 秒内再次点击，退出应用
    await CapacitorApp.exitApp();
  } else {
    // 第一次点击，提示用户
    lastBackPressTime = currentTime;
    showToast({ message: '再按一次退出应用', duration: 2000 });
    event.preventDefault();
  }
};

onMounted(() => {
  // 监听 Capacitor 返回键事件
  CapacitorApp.addListener('backButton', handleBackButton);
});

onUnmounted(() => {
  CapacitorApp.removeAllListeners();
});
</script>

<style>
/* 全局重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-size: 16px;
  background-color: #f7f8fa;
  color: #333;
  height: 100%;
  width: 100%;
  overflow: hidden;
}

#app, .app {
  max-width: 750px;
  margin: 0 auto;
  height: 100%;
  width: 100%;
}

/* 移动端适配 */
@media screen and (max-width: 750px) {
  html {
    font-size: calc(100vw / 750 * 16);
  }
}
</style>
