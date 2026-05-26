<template>
  <div style="min-height: 100vh; background-color: #000; color: #fff; font-family: sans-serif; padding: 40px; text-align: center;">
    
    <div v-if="isLoading" style="padding-top: 20vh;">
      <p style="color: #666; letter-spacing: 0.2em;">Loading the legacy...</p>
    </div>

    <div v-else-if="error" style="padding-top: 20vh;">
      <p style="color: #ff4444;">{{ error }}</p>
    </div>

    <div v-else style="max-width: 800px; margin: 0 auto;">
      
      <h2 style="color: #888; font-size: 14px; letter-spacing: 0.3em; text-transform: uppercase; margin-bottom: 20px;">
        {{ carData.car_name }}
      </h2>

      <h1 style="font-size: 48px; font-weight: bold; margin-bottom: 40px; line-height: 1.2;">
        {{ carData.catchphrase }}
      </h1>

      <div style="width: 100%; height: 400px; background-color: #111; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 60px;">
        <p style="color: #444;">[ここに美しい車両画像が入ります]</p>
      </div>

      <div style="text-align: left; max-width: 600px; margin: 0 auto;">
        <p style="color: #ccc; font-size: 18px; line-height: 1.8; white-space: pre-wrap;">
          {{ carData.story }}
        </p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const carData = ref(null)
const isLoading = ref(true)
const error = ref(null)

// あなたのデータベースに保存されたポルシェのID
const LP_ID = "d7953c7b-c4ff-492b-a070-9c2170d75d10" 

onMounted(async () => {
  try {
    // 🌟 あなたのCodespacesのDjango(8000番)へデータをリクエスト！
    const response = await fetch(`https://studious-adventure-5g76vvrg99jvcvww9-8000.app.github.dev/api/lp/detail/${LP_ID}/`)
    
    if (!response.ok) {
      throw new Error('データの取得に失敗しました')
    }

    const json = await response.json()
    
    if (json.status === 'success') {
      carData.value = json.data
    } else {
      error.value = json.message
    }
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
})
</script>

<style>
/* デフォルトの余白を消す */
body { margin: 0; }
</style>