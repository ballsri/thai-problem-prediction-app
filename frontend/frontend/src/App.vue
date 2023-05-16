<template>
  <div class="container">
    <div class="input-container">
      <input type="text" class="input" v-model="inputValue" placeholder="ใส่ปัญหาที่นี่">
      <button class="enter-button" @click="sendData">ส่ง</button>
    </div>
    <div class="result-container">
      <div v-if="result" class="result">{{ result }}</div>
      <div v-if="isLoading">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>
    </div>
    <div class="slider-container1">
        <div class="topics">
          <span class="topic">{{ topic1 }}</span>
        </div>
        <div class="slider">
          <div v-for="(report, index) in reports" :key="index" class="report">{{ report }}
          </div>
        </div>
      </div>
    <div class="slider-container2">
      <div class="topics">
        <span class="topic">{{ topic2 }}</span>
      </div>
      <div class="slider">
        <div v-for="(report, index) in cur_reports" :key="index" class="report">{{ report }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import './assets/index.css';
</style>

<script>
import { v4 as uuidv4 } from "uuid";
const url = "localhost:8000";

export default {
  data() {
    return {
      inputValue: "",
      result: "",
      activeIndex: 1,
      topic1: "ปัญหาที่มีคนเคยถาม",
      topic2: "ปัญหาที่กำลังถูกถาม",
      cur_reports: [
      ],
      socket: null,
      isLoading: false,
      latest_sent_tid: null,
    };
  },
  mounted() {
    this.connectToWebSocket();
    this.fetchReport();
  },

  methods: {

    fetchReport() {

      fetch("http://" + url + "/predicts", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((res) => {
          if (res.status === 200) {
            return res.json();
          } else {
            throw new Error("โหลดข้อมูลไม่สำเร็จ");
          }
        })
        .then((data) => {
          console.log(data);
          this.cur_reports = data.texts;
        })
        .catch((err) => {
          console.log(err);
          this.cur_reports = [];
          
        });

    },


    connectToWebSocket() {
      this.socket = new WebSocket("ws://"+ url + "/traffy");

      // receive json from websocket
      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log(data);
        if (data.tid === this.latest_sent_tid) {
          this.isLoading = false;
          this.result = "Text has processed successfully";
          this.cur_reports.unshift(data.result);
          return;
        }
        this.cur_reports.unshift(data.result);
      };


    },


    async sendData() {
      // This is where you would handle sending data from the input box and getting a result
      // You could update the `result` data property to display the result in the page

      // fetch to backend
      this.result = "";
      this.isLoading = true;
      this.latest_sent_tid = uuidv4();
      await fetch("http://" + url + "/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tid: this.latest_sent_tid,
          text: this.inputValue,
        }),
      })
        .then((res) => {
          if (res.status === 200) {
            return res.json();
          } else {
            throw new Error("ไม่สามารถทำนายได้");
          }
        })
        .then((data) => {
          console.log(data);
          this.inputValue = "";
        })
        .catch((err) => {
          console.log(err);
          this.isLoading = false;
          this.result = "ไม่สามารถทำนายได้";
        });

    

    },


  },
};
</script>
