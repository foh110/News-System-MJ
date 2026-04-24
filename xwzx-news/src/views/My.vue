<template>
  <div class="my-container">
    <van-nav-bar :title="$t('my.title')" fixed :style="{ top: '30px' }" />
    <div class="user-info" @click="goToProfile" v-if="isLogin">
      <div class="avatar">
        <van-image
          width="80"
          height="80"
          :src="userInfo.avatar || 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
        />
      </div>
      <div class="info">
        <div class="username">{{ userInfo.username || 'admin' }}</div>
        <div class="desc">{{ userInfo.bio || '这个人很懒，什么都没留下' }}</div>
      </div>
      <van-icon name="arrow" class="arrow-icon" />
    </div>
    <div class="user-info" v-else>
      <div class="avatar">
        <van-image
          width="80"
          height="80"
          fit="contain"
          :src="'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
        />
      </div>
      <div class="info">
        <div class="username">{{ $t('my.notLoggedIn') }}</div>
        <div class="desc">
          <van-button type="primary" size="small" @click="goToLogin" style="margin-right: 10px">{{ $t('my.goToLogin') }}</van-button>
          <van-button type="default" size="small" @click="goToRegister">{{ $t('my.goToRegister') }}</van-button>
        </div>
      </div>
    </div>

    <div class="menu-list">
      <van-cell-group inset>
        <van-cell title="更新新闻" icon="replay" is-link @click="triggerCrawl" />
        <van-cell :title="$t('my.myFavorite')" is-link @click="goToFavorite" />
        <van-cell :title="$t('my.browsingHistory')" is-link @click="goToHistory" />
        <van-cell :title="$t('my.notifications')" is-link />
        <van-cell :title="$t('my.settings')" is-link @click="goToSettings" />
        <van-cell v-if="isLogin" :title="$t('my.logout')" @click="handleLogout" />
      </van-cell-group>
    </div>
    <tab-bar />
  </div>
</template>

<script setup>
import { onMounted, onActivated } from 'vue';
import { useUserStore } from '../store/user';
import { useRouter } from 'vue-router';
import { computed } from 'vue';
import { showDialog, showToast, showLoadingToast } from 'vant';
import TabBar from '../components/TabBar.vue';
import { useI18n } from 'vue-i18n';
import axios from 'axios';
import { apiConfig } from '../config/api';

const userStore = useUserStore();
const router = useRouter();
const { t } = useI18n();

// 从store获取用户信息和登录状态
const userInfo = computed(() => userStore.userInfo);
const isLogin = computed(() => userStore.getLoginStatus);

// 刷新用户信息
const refreshUserInfo = async () => {
  if (isLogin.value) {
    try {
      await userStore.getUserInfoDetail();
    } catch (error) {
      console.error('获取用户信息失败:', error);
    }
  }
};

// 页面挂载时获取信息
onMounted(() => {
  refreshUserInfo();
});

// 页面激活时（从其他页面返回）刷新信息
onActivated(() => {
  refreshUserInfo();
});

// 跳转到登录页
const goToLogin = () => {
  router.push('/login');
};

// 跳转到注册页
const goToRegister = () => {
  router.push('/register');
};

// 跳转到个人信息页
const goToProfile = () => {
  if (isLogin.value) {
    router.push('/profile');
  }
};

// 跳转到浏览历史页面
const goToHistory = () => {
  if (isLogin.value) {
    router.push('/history');
  } else {
    showToast(t('common.login'));
    router.push('/login');
  }
};

// 跳转到我的收藏页面
const goToFavorite = () => {
  if (isLogin.value) {
    router.push('/favorite');
  } else {
    showToast(t('common.login'));
    router.push('/login');
  }
};

// 跳转到设置页面
const goToSettings = () => {
  router.push('/settings');
};

// 退出登录
const handleLogout = () => {
  showDialog({
    title: t('common.confirm'),
    message: t('my.logout') + '?',
    showCancelButton: true,
  }).then((action) => {
    if (action === 'confirm') {
      userStore.logout();
      router.push('/login');
    }
  });
};

// 触发新闻爬虫
const triggerCrawl = async () => {
  showDialog({
    title: '更新新闻',
    message: '确定要从网络爬取最新新闻吗？',
    showCancelButton: true,
  }).then(async (action) => {
    if (action === 'confirm') {
      const loadingInstance = showLoadingToast({
        message: '正在爬取新闻...',
        forbidClick: true,
        duration: 0
      });
      
      try {
        await axios.post(`${apiConfig.baseURL}/api/spider/crawl?category_ids=1,2,3`);
        loadingInstance.close();
        showToast({
          type: 'success',
          message: '新闻更新任务已启动，请稍后刷新首页查看'
        });
      } catch (error) {
        loadingInstance.close();
        showToast({
          type: 'fail',
          message: '更新失败，请稍后再试'
        });
      }
    }
  }).catch(() => {});
};
</script>

<style scoped>
.my-container {
  padding-top: 46px;
  padding-bottom: 50px;
  background-color: var(--background-color);
  color: var(--text-color);
  min-height: 100vh;
  box-sizing: border-box;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 20px 16px;
  background-color: #fff;
  color: #333;
  border-radius: 8px;
  margin: 16px;
  position: relative;
  border: 1px solid #ddd;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.arrow-icon {
  position: absolute;
  right: 16px;
  color: #969799;
}

.avatar {
  margin-right: 16px;
}

:deep(.van-image) {
  border-radius: 16px !important;
  overflow: hidden !important;
}
:deep(.van-image img) {
  object-fit: cover !important;
}

.info {
  flex: 1;
}

.username {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 4px;
}

.desc {
  font-size: 14px;
  color: #999;
}

.menu-list {
  margin: 0 16px;
}
</style>