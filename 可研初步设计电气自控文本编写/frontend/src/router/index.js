import { createRouter, createWebHistory } from 'vue-router'
import Workbench from '../views/Workbench.vue'
import DocManage from '../views/DocManage.vue'
import TemplateManage from '../views/TemplateManage.vue'
import Generate from '../views/Generate.vue'
import Regulation from '../views/Regulation.vue'

const routes = [
  { path: '/', redirect: '/workbench' },
  { path: '/workbench', name: 'workbench', component: Workbench, meta: { title: '工作台' } },
  { path: '/generate', name: 'generate', component: Generate, meta: { title: '文件生成' } },
  { path: '/docs', name: 'docs', component: DocManage, meta: { title: '文档管理' } },
  { path: '/templates', name: 'templates', component: TemplateManage, meta: { title: '模板管理' } },
  { path: '/regulation', name: 'regulation', component: Regulation, meta: { title: '规范浏览' } }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
