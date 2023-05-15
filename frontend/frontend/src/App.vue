<template>
  <div class="container">
    <div class="input-container">
      <input type="text" class="input" v-model="inputValue" placeholder="ใส่ปัญหาที่นี่">
      <button class="enter-button" @click="sendData">ส่ง</button>
    </div>
    <div class="result-container">
      <div v-if="result" class="result">{{ result }}</div>
    </div>
    <div class="slider-container">
      <div class="topics">
        <span class="topic">{{ topic }}</span>
      </div>
      <div class="slider">
        <div v-for="(report, index) in reports" :key="index" class="report">{{ report }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import './assets/index.css';
</style>

<script>
export default {
  data() {
    return {
      inputValue: "",
      result: "sdsd",
      activeIndex: 1,
      topic: "ปัญหาอื่นๆ",
      reports: [
        "ปัญหา 1",
        "ปัญหา 2",
      ],
    };
  },
  methods: {
    sendData() {
      // This is where you would handle sending data from the input box and getting a result
      // You could update the `result` data property to display the result in the page
    },
  },
};
</script>
