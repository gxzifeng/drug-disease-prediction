<template>
  <router-view />
</template>

<script setup lang="ts">
// App entry component
</script>

<style lang="scss">
/* 强制全局浅色背景 + 深色文字 + 大字体 */
#app {
  width: 100%;
  height: 100vh;
  background: #ffffff !important;
  color: #000000 !important;
  font-size: 16px !important;  /* 基础字体调大 */
}

/* 覆盖所有可能存在的深色背景容器 */
div,
section,
main,
header,
footer,
aside,
nav,
article,
.el-container,
.el-main,
.el-header,
.el-footer,
.el-card,
.el-dialog,
.el-menu,
.el-table,
.el-table__body,
.el-table__row,
.el-table__header,
.page-container,
.card,
.box-card,
.content,
.wrapper,
.layout {
  background-color: #ffffff !important;
  color: #000000 !important;
}

/* 表格文字、表单文字、按钮文字全部调大且黑色 */
.el-table th,
.el-table td,
.el-form-item__label,
.el-input__inner,
.el-button,
.el-select .el-input__inner,
.el-radio__label,
.el-checkbox__label,
.el-tabs__item,
.el-menu-item,
.el-submenu__title {
  font-size: 14px !important;
  color: #000000 !important;
}

/* 输入框背景变白，边框保留 */
.el-input__inner,
.el-textarea__inner,
.el-select .el-input__inner {
  background-color: #ffffff !important;
  border: 1px solid #dcdfe6 !important;
  color: #000000 !important;
}

/* 下拉菜单背景变白 */
.el-popper,
.el-select-dropdown,
.el-dropdown-menu {
  background-color: #ffffff !important;
  border: 1px solid #e4e7ed !important;
}

.el-select-dropdown__item {
  color: #000000 !important;
}

/* 按钮背景调整（保留原有风格，但确保文字可见） */
.el-button--primary {
  background-color: #409eff !important;
  border-color: #409eff !important;
  color: #ffffff !important;
}

.el-button--default {
  background-color: #ffffff !important;
  border-color: #dcdfe6 !important;
  color: #606266 !important;
}

/* 顶部导航栏（如果有） */
.el-menu--horizontal,
.el-menu-bar {
  background-color: #ffffff !important;
  border-bottom: 1px solid #e4e7ed !important;
}

/* 分页组件 */
.el-pagination {
  color: #000000 !important;
  background: transparent !important;
}
</style>