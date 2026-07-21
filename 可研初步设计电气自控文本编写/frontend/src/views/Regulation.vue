<template>
  <div>
    <h2>规范浏览 · 四大工程类型电气/自控深度要求</h2>
    <el-alert type="info" :closable="false" style="margin-bottom: 12px">
      依据《市政公用工程设计文件编制深度规定》（2025年版）：给水、排水、道路、环卫工程的初步设计阶段电气与自控说明编写要求。
    </el-alert>
    <el-tabs v-model="tab">
      <el-tab-pane v-for="t in types" :key="t.code" :label="t.name + '·' + t.design_stage" :name="t.code">
        <el-collapse>
          <el-collapse-item v-for="(group, idx) in groupOf(t.code)" :key="idx"
                            :title="group.category + '（' + group.items.length + ' 项）'">
            <ol>
              <li v-for="(it, i) in group.items" :key="i" style="margin-bottom: 4px">
                <b>{{ it.title }}</b> —— {{ it.depth_requirement }}
                <span v-if="it.calc_from_excel" style="color:#409EFF"> ［需由负荷计算Excel生成］</span>
              </li>
            </ol>
          </el-collapse-item>
        </el-collapse>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getProjectTypes, getSections } from '../api'

const types = ref([])
const sections = ref([])
const tab = ref('')

const byType = computed(() => {
  const m = {}
  for (const s of sections.value) m[s.project_type_id] = m[s.project_type_id] || []
  return m
})

function groupOf(code) {
  const pt = types.value.find(t => t.code === code)
  if (!pt) return []
  const list = byType.value[pt.id] || []
  const map = {}
  for (const s of list) {
    map[s.category] = map[s.category] || []
    map[s.category].push(s)
  }
  return Object.entries(map).map(([category, items]) => ({ category, items }))
}

onMounted(async () => {
  const [t, s] = await Promise.all([getProjectTypes(), getSections()])
  types.value = t.data
  sections.value = s.data
  if (types.value.length) tab.value = types.value[0].code
})
</script>
