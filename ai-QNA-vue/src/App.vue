<script setup>
import { ref, onMounted } from 'vue'
import AuthPage from './components/AuthPage.vue'
import TechAssistant from './components/TechAssistant.vue'
import { authService } from './services/api.js'

const isAuthenticated = ref(false)

const checkAuth = () => {
  isAuthenticated.value = authService.isAuthenticated()
}

const handleLoginSuccess = () => {
  isAuthenticated.value = true
}

const handleLogout = () => {
  authService.logout()
  isAuthenticated.value = false
}

onMounted(() => {
  checkAuth()
})
</script>

<template>
  <AuthPage v-if="!isAuthenticated" @login-success="handleLoginSuccess" />
  <TechAssistant v-else @logout="handleLogout" />
</template>
