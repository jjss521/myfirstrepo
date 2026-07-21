<template>
  <el-container style="height: 100vh">
    <el-aside width="210px" style="background: #304156">
      <div class="logo">⚡ 电气自控生成器</div>
      <el-menu background-color="#304156" text-color="#bfcbd9"
               active-text-color="#409EFF" router>
        <el-menu-item index="/workbench">🏠 工作台</el-menu-item>
        <el-menu-item index="/generate">🚀 文件生成</el-menu-item>
        <el-menu-item index="/docs">📁 文档管理</el-menu-item>
        <el-menu-item index="/templates">📋 模板管理</el-menu-item>
        <el-menu-item index="/regulation">📖 规范浏览</el-menu-item>
      </el-menu>
    </el-aside>
    <el-main style="background: #f0f2f5">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
</script>

<style>
.logo {
  padding: 18px 16px;
  color: #fff;
  font-weight: bold;
  font-size: 15px;
  border-bottom: 1px solid #41495a;
}
</style>
