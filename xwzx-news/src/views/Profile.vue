<template>
  <div class="profile-page">
    <van-nav-bar
      title="个人信息"
      left-arrow
      @click-left="$router.back()"
      fixed
      :style="{ top: '30px' }"
    />
    
    <div class="profile-container">
      <van-cell-group inset class="avatar-group">
        <van-cell title="头像" center @click="showAvatarUpload">
          <template #right-icon>
            <van-image
              width="60"
              height="60"
              style="border-radius: 12px; overflow: hidden;"
              :src="userInfo.avatar || 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg'"
            />
          </template>
        </van-cell>
      </van-cell-group>
      
      <van-cell-group inset class="info-group">
        <van-cell title="用户名" :value="userInfo.username || 'admin'" is-link @click="showUsernameDialog" />
        <van-cell title="账号ID" :value="`ID: ${userInfo.id || 'N/A'}`" />
        <van-cell title="个人简介" :value="userInfo.bio || '暂无简介'" is-link @click="showBioDialog" />
      </van-cell-group>
      
      <van-cell-group inset class="security-group">
        <van-cell title="修改密码" is-link @click="showPasswordConfirm" />
      </van-cell-group>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h, onMounted } from 'vue';
import { useUserStore } from '../store/user';
import { showDialog, showToast, showLoadingToast, showSuccessToast, showFailToast } from 'vant';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { apiConfig } from '../config/api';

const router = useRouter();
const userStore = useUserStore();

// 初始化用户状态
onMounted(async () => {
  // 如果用户未登录，跳转到登录页面
  if (!userStore.getLoginStatus) {
    router.push('/login');
    return;
  }
  
  // 获取用户信息
  try {
    // 显示加载提示
    const loadingInstance = showLoadingToast({
      message: '加载中...',
      forbidClick: true,
      duration: 0
    });
    
    // console.log('获取用户信息，当前token:', userStore.token);
    
    // 使用新的 getUserInfoDetail 方法
    const result = await userStore.getUserInfoDetail();
    
    // 手动关闭加载提示
    loadingInstance.close();
    
    if (result.success) {
      console.log('获取用户信息成功:', userStore.userInfo);
      // 显示成功提示
      // showSuccessToast('获取用户信息成功');
    } else {
      console.error('获取用户信息失败:', result.message);
      showFailToast(result.message || '获取用户信息失败');
    }
  } catch (error) {
    console.error('获取用户信息请求失败:', error);
    // 确保关闭加载提示
    showToast.clear();
    showToast.fail('获取用户信息失败');
  }
});

const userInfo = computed(() => userStore.userInfo);
const userBio = computed(() => userStore.userInfo?.bio || '暂无简介');

// 修改用户名
const showUsernameDialog = () => {
  const newUsername = ref(userInfo.value.username || '');
  
  showDialog({
    title: '修改用户名',
    showCancelButton: true,
    message: h('div', { style: 'text-align: left; padding: 10px 0;' }, [
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, '新用户名：'),
        h('input', {
          type: 'text',
          value: newUsername.value,
          onInput: (e) => { newUsername.value = e.target.value },
          placeholder: '请输入新用户名',
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box;'
        })
      ])
    ])
  }).then(async () => {
    if (!newUsername.value || newUsername.value.trim() === '') {
      showToast('请输入用户名');
      return;
    }
    
    try {
      const loadingInstance = showLoadingToast({
        message: '修改中...',
        forbidClick: true,
        duration: 0
      });
      
      const response = await axios.put(`${apiConfig.baseURL}/api/user/update`,
        { username: newUsername.value.trim() },
        {
          headers: {
            Authorization: userStore.token
          }
        }
      );
      
      loadingInstance.close();
      
      if (response.data.code === 200) {
        // 更新本地用户信息
        userStore.userInfo.username = response.data.data.username;
        showSuccessToast('用户名修改成功');
      } else {
        showFailToast(response.data.message || '用户名修改失败');
      }
    } catch (error) {
      console.error('修改用户名失败:', error);
      showToast.clear();
      showToast.fail('用户名修改失败');
    }
  }).catch(() => {
    // 点击取消
  });
};

// 修改头像（支持上传）
const showAvatarUpload = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  
  input.onchange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // 限制文件大小 2MB
    if (file.size > 2 * 1024 * 1024) {
      showToast('图片大小不能超过2MB');
      return;
    }
    
    try {
      const loadingInstance = showLoadingToast({
        message: '上传中...',
        forbidClick: true,
        duration: 0
      });
      
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${apiConfig.baseURL}/api/user/upload-avatar`,
        formData,
        {
          headers: {
            Authorization: userStore.token,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      loadingInstance.close();
      
      if (response.data.code === 200) {
        // 获取完整头像URL
        const avatarUrl = response.data.data.avatar;
        const fullAvatarUrl = avatarUrl.startsWith('http') ? avatarUrl : `${apiConfig.baseURL}${avatarUrl}`;
        
        // 更新本地用户信息
        userStore.userInfo.avatar = fullAvatarUrl;
        
        // 重新获取用户信息以确保数据一致性
        await userStore.getUserInfoDetail();
        
        showSuccessToast('头像修改成功');
        // 强制刷新页面以显示新头像
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        showFailToast(response.data.message || '头像上传失败');
      }
    } catch (error) {
      console.error('修改头像失败:', error);
      showToast.clear();
      showToast.fail('头像上传失败');
    }
  };
  
  input.click();
};

const showPasswordConfirm = () => {
  // 使用ref创建响应式变量
  const oldPassword = ref('');
  const newPassword = ref('');
  const confirmPassword = ref('');
  
  showDialog({
    title: '修改密码',
    showCancelButton: true,
    className: 'password-dialog',
    message: h('div', { style: 'text-align: left; padding: 10px 0;' }, [
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, '当前密码：'),
        h('input', {
          type: 'password',
          value: oldPassword.value,
          onInput: (e) => { oldPassword.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box;'
        })
      ]),
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, '新密码：'),
        h('input', {
          type: 'password',
          value: newPassword.value,
          onInput: (e) => { newPassword.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box;'
        })
      ]),
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, '确认密码：'),
        h('input', {
          type: 'password',
          value: confirmPassword.value,
          onInput: (e) => { confirmPassword.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box;'
        })
      ])
    ]),
  }).then(async () => {
    // 点击确认按钮
    if (!oldPassword.value) {
      showToast('请输入当前密码');
      return;
    }
    
    if (!newPassword.value) {
      showToast('请输入新密码');
      return;
    }
    
    if (newPassword.value !== confirmPassword.value) {
      showToast('两次密码输入不一致');
      return;
    }
    
    try {
      // 显示加载提示
      const loadingInstance = showLoadingToast({
        message: '修改中...',
        forbidClick: true,
        duration: 0
      });
      
      // 调用API更新密码
      const result = await userStore.updatePassword(oldPassword.value, newPassword.value);
      
      // 关闭加载提示
      loadingInstance.close();
      
      if (result && result.success) {
        showSuccessToast('密码修改成功');
      } else {
        showFailToast((result && result.message) || '密码修改失败');
      }
    } catch (error) {
      console.error('修改密码失败:', error);
      showToast.clear();
      showToast.fail('密码修改失败');
    }
  }).catch(() => {
    // 点击取消按钮
  });
};

const showBioDialog = () => {
  // 使用ref创建响应式变量
  const newBioValue = ref(userBio.value);
  
  showDialog({
    title: '修改个人简介',
    showCancelButton: true,
    confirmButtonText: '确认',
    className: 'bio-dialog',
    message: h('div', { style: 'text-align: left; padding: 10px 0;' }, [
      h('div', { style: 'margin-bottom: 15px;' }, [
        h('div', { style: 'margin-bottom: 5px; text-align: left;' }, '个人简介：'),
        h('textarea', {
          value: newBioValue.value,
          onInput: (e) => { newBioValue.value = e.target.value },
          style: 'width: 100%; border: 1px solid #dcdee0; border-radius: 4px; padding: 8px; box-sizing: border-box; min-height: 100px; resize: vertical;'
        })
      ])
    ])
  }).then(async () => {
    // 点击确认按钮
    try {
      // 显示加载提示
      const loadingInstance = showLoadingToast({
        message: '保存中...',
        forbidClick: true,
        duration: 0
      });
      
      console.log('更新个人简介:', newBioValue.value);
      
      // 调用API更新个人简介
      const result = await userStore.updateUserBio(newBioValue.value);
      
      // 关闭加载提示
      loadingInstance.close();
      
      if (result && result.success) {
        showSuccessToast('个人简介修改成功');
      } else {
        showFailToast((result && result.message) || '个人简介修改失败');
      }
    } catch (error) {
      console.error('更新个人简介失败:', error);
      showToast.clear();
      showToast.fail('个人简介修改失败');
    }
  }).catch(() => {
    // 点击取消按钮
  });
};
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background-color: #f7f8fa;
}

.profile-container {
  padding-top: 76px;
  padding-bottom: 20px;
}

.avatar-group,
.info-group,
.security-group {
  margin-top: 12px;
}

:deep(.van-cell__right-icon), :deep(.van-cell__right-icon .van-image) {
  border-radius: 12px !important;
  overflow: hidden !important;
}
:deep(.van-cell__right-icon .van-image img) {
  object-fit: cover !important;
  border-radius: 12px !important;
}

.password-dialog .van-dialog__content {
  padding: 20px;
}

.password-form .form-item {
  margin-bottom: 15px;
  text-align: left;
}

.password-form .form-item span {
  display: block;
  margin-bottom: 5px;
  text-align: left;
}

.password-form .password-input {
  width: 100%;
  border: 1px solid #dcdee0;
  border-radius: 4px;
  padding: 8px;
  outline: none;
  box-sizing: border-box;
}
</style>