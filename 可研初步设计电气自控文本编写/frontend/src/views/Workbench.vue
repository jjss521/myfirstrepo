<template>
  <div>
    <h2>工作台 · 快速生成</h2>
    <el-card>
      <el-form label-width="110px">
        <el-form-item label="负荷计算表">
          <el-input v-model="excelPath" placeholder="Excel 绝对路径，如 D:\00-水厂负荷计算表.xlsx" style="width: 420px" />
          <el-upload :auto-upload="false" :show-file-list="false" :on-change="onFile" style="margin-left: 10px">
            <el-button>浏览…</el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="工程类型">
          <el-select v-model="form.project_type" style="width: 240px">
            <el-option v-for="t in types" :key="t.code" :label="t.name" :value="t.code.split('_')[0]" />
          </el-select>
        </el-form-item>
        <el-form-item label="设计阶段">
          <el-select v-model="form.design_stage" style="width: 240px">
            <el-option label="初步设计" value="初步设计" />
            <el-option label="可研" value="可研" />
          </el-select>
        </el-form-item>
        <el-form-item label="文档模板">
          <el-select v-model="form.template" style="width: 240px">
            <el-option label="标准版" value="standard" />
            <el-option label="紧凑版" value="compact" />
            <el-option label="报批版" value="report" />
            <el-option label="现代版" value="modern" />
          </el-select>
        </el-form-item>
        <el-form-item label="项目名称">
          <el-input v-model="form.project_name" style="width: 240px" />
        </el-form-item>
        <el-button type="primary" @click="doGen" :disabled="!excelPath">生成设计文件（Word）</el-button>
      </el-form>
    </el-card>
    <el-alert v-if="result" :title="'已生成：' + result" type="success" show-icon style="margin-top: 12px" />
    <el-alert v-if="err" :title="err" type="error" show-icon style="margin-top: 12px" />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { getProjectTypes, generateDoc, uploadDoc } from '../api'

const types = ref([])
const excelPath = ref('')
const result = ref('')
const err = ref('')
const form = reactive({
  project_type: 'water_supply', design_stage: '初步设计', template: 'standard',
  project_name: '新建项目', voltage_level: '10kV', load_level: '二级'
})

onMounted(async () => {
  try { const r = await getProjectTypes(); types.value = r.data } catch (e) {}
})

function onFile(file) {
  const raw = file.raw
  const fd = new FormData()
  fd.append('file', raw)
  fd.append('doc_type', 'load_excel')
  uploadDoc(fd).then(res => {
    excelPath.value = res.data.abs_path || res.data.filename
  }).catch(e => { err.value = '上传失败：' + e })
}

async function doGen() {
  err.value = ''; result.value = ''
  if (!excelPath.value) { err.value = '请先选择负荷计算表'; return }
  try {
    const r = await generateDoc({ excel_path: excelPath.value, ...form })
    result.value = r.data.output_path
  } catch (e) {
    err.value = '生成失败：' + (e.response?.data?.detail || e.message)
  }
}
</script>
