<template>
  <div>
    <h2>文件生成 · 完整参数</h2>
    <el-card>
      <el-form label-width="120px">
        <el-form-item label="负荷计算表">
          <el-input v-model="excelPath" placeholder="Excel 绝对路径" style="width: 460px" />
          <el-upload :auto-upload="false" :show-file-list="false" :on-change="onFile" style="margin-left: 10px">
            <el-button>浏览…</el-button>
          </el-upload>
        </el-form-item>
        <el-row>
          <el-col :span="12">
            <el-form-item label="工程类型">
              <el-select v-model="form.project_type" style="width: 220px">
                <el-option v-for="t in types" :key="t.code" :label="t.name" :value="t.code.split('_')[0]" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设计阶段">
              <el-select v-model="form.design_stage" style="width: 220px">
                <el-option label="初步设计" value="初步设计" />
                <el-option label="可研" value="可研" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="文档模板">
              <el-select v-model="form.template" style="width: 220px">
                <el-option label="标准版" value="standard" />
                <el-option label="紧凑版" value="compact" />
                <el-option label="报批版" value="report" />
                <el-option label="现代版" value="modern" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目名称">
              <el-input v-model="form.project_name" style="width: 220px" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row>
          <el-col :span="12">
            <el-form-item label="电压等级">
              <el-select v-model="form.voltage_level" style="width: 220px">
                <el-option label="10kV" value="10kV" />
                <el-option label="20kV" value="20kV" />
                <el-option label="35kV" value="35kV" />
                <el-option label="0.4kV" value="0.4kV" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="负荷等级">
              <el-select v-model="form.load_level" style="width: 220px">
                <el-option label="一级" value="一级" />
                <el-option label="二级" value="二级" />
                <el-option label="三级" value="三级" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
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
  project_name: '新建项目', voltage_level: '10kV', load_level: '二级',
  power_source: '两路', standby_desc: '两路电源互为备用'
})

onMounted(async () => {
  try { const r = await getProjectTypes(); types.value = r.data } catch (e) {}
})

function onFile(file) {
  const fd = new FormData()
  fd.append('file', file.raw)
  fd.append('doc_type', 'load_excel')
  uploadDoc(fd).then(res => { excelPath.value = res.data.abs_path || res.data.filename })
    .catch(e => { err.value = '上传失败：' + e })
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
