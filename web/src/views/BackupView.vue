<template>
  <div class="backup-view">
    <div class="header">
      <h2>配置备份</h2>
    </div>

    <div class="card">
      <h3>导出配置</h3>
      <p>将所有配置（API Key、人设、记忆、白名单、固定会话、Skills 等）导出为 JSON 文件。</p>
      <button class="btn btn-primary" :disabled="exporting" @click="handleExport">
        {{ exporting ? '导出中...' : '导出配置' }}
      </button>
    </div>

    <div class="card">
      <h3>导入配置</h3>
      <p>从之前导出的 JSON 文件还原配置。会覆盖当前所有配置。</p>
      <input
        ref="fileInputRef"
        type="file"
        accept=".json"
        style="display:none"
        @change="handleFileSelected"
      />
      <button class="btn btn-warning" :disabled="importing" @click="triggerFilePicker">
        {{ importing ? '导入中...' : '选择备份文件导入' }}
      </button>
      <div v-if="importResult" class="import-result" :class="importResult.success ? 'success' : 'error'">
        {{ importResult.message }}
      </div>
    </div>

    <div class="card hint">
      <h3>版本兼容</h3>
      <p>备份文件包含版本号。导入时会按原始内容写入文件，不依赖特定版本格式，因此旧版备份在新版中亦可还原。</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { api } from '@/api'

const exporting = ref(false)
const importing = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const importResult = ref<{ success: boolean; message: string } | null>(null)

async function handleExport() {
  exporting.value = true
  importResult.value = null
  try {
    await api.exportBackup()
  } catch (e: any) {
    importResult.value = { success: false, message: `导出失败: ${e.message}` }
  } finally {
    exporting.value = false
  }
}

function triggerFilePicker() {
  importResult.value = null
  fileInputRef.value?.click()
}

async function handleFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  importing.value = true
  importResult.value = null
  try {
    const text = await file.text()
    const result = await api.importBackup(text)
    importResult.value = {
      success: true,
      message: `成功还原 ${result.restored_count} 个文件`,
    }
  } catch (e: any) {
    importResult.value = { success: false, message: `导入失败: ${e.message}` }
  } finally {
    importing.value = false
    input.value = ''
  }
}
</script>

<style scoped>
.backup-view {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  max-width: 640px;
}
.header {
  margin-bottom: 24px;
}
.header h2 {
  font-size: 20px;
  font-weight: 700;
}
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 16px;
}
.card h3 {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
}
.card p {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 14px;
  line-height: 1.5;
}
.card.hint {
  background: var(--bg-secondary);
}
.btn {
  padding: 8px 20px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  border: none;
  transition: opacity 0.15s;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-primary {
  background: var(--accent);
  color: #fff;
}
.btn-primary:hover:not(:disabled) {
  opacity: 0.85;
}
.btn-warning {
  background: #f59e0b;
  color: #fff;
}
.btn-warning:hover:not(:disabled) {
  opacity: 0.85;
}
.import-result {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
}
.import-result.success {
  background: #dcfce7;
  color: #166534;
}
.import-result.error {
  background: #fee2e2;
  color: #991b1b;
}
</style>
