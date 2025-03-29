<template>
  <div class="app-container">
    <el-config-provider :locale="zhCn">
      <router-view />
    </el-config-provider>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import zhCn from "element-plus/es/locale/lang/zh-cn";

export default defineComponent({
  name: "App",
  setup() {
    return {
      zhCn,
    };
  },
});
</script>

<style>
html,
body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
}

.app-container {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
