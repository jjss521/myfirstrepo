<template>
  <div>
    <h2>模板管理 · 规范栏目（按深度要求）</h2>
    <p style="color: #888">下列栏目由《市政公用工程设计文件编制深度规定》（2025年版）提取，生成文件时逐栏编写。</p>
    <el-collapse v-model="active">
      <el-collapse-item v-for="(group, idx) in grouped" :key="idx" :title="group.category + '（' + group.items.length + '）'">
        <el-table :data="group.items" border size="small">
          <el-table-column prop="title" label="栏目" width="220" />
          <el-table-column prop="depth_requirement" label="深度要求" />
          <el-table-column prop="flags" label="标记" width="180" />
        </el-table>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { getSections } from '../api'

const sections = ref([])
const active = ref([])

function decorate(s) {
  const f = []
  if (s.has_calculation) f.push('含计算')
  if (s.table_required) f.push('需表格')
  if (s.calc_from_excel) f.push('来自Excel')
  if (s.optional) f.push('可选')
  return f.join(' / ')
}

const grouped = computed(() => {
  const map = {}
  for (const s of sections.value) {
    map[s.category] = map[s.category] || []
    map[s.category].push({ ...s, flags: decorate(s) })
  }
  return Object.entries(map).map(([category, items]) => ({ category, items }))
})

onMounted(async () => {
  try {
    const r = await getSections()
    sections.value = r.data
    active.value = grouped.value.slice(0, 2).map((g, i) => i)
  } catch (e) {}
})
</script>
