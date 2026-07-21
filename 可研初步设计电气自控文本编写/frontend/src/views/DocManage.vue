<template>
  <div>
    <h2>文档管理 · 参考文档上传</h2>
    <el-upload
      drag
      :auto-upload="true"
      action="/api/upload?doc_type=reference"
      :on-success="onOk"
      multiple
      style="max-width: 640px"
    >
      <el-icon style="font-size: 48px; color: #409eff"><UploadFilled /></el-icon>
      <div>将可研 / 初设参考文档拖到此处，或点击上传（.docx / .doc / .pdf）</div>
    </el-upload>

    <el-table :data="rows" style="margin-top: 16px; max-width: 760px">
      <el-table-column prop="original_name" label="文件名" />
      <el-table-column prop="doc_type" label="类型" width="120" />
      <el-table-column prop="uploaded_at" label="上传时间" width="200" />
    </el-table>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'

const rows = ref([])
function onOk() { load() }
function load() {
  api.get('/documents').then(r => { rows.value = r.data }).catch(() => {})
}
load()
</script>
