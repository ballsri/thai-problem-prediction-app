# thai-problem-prediction-app
A __FastAPI__ application to predict classification's answer.
It uses __Wangchan berta's model__ to classify text into problem's topic in Thai.

- Please download folder "model.pth" and put it in /app/model/ ( The model.pth is too large for github )
  - from here https://drive.google.com/drive/folders/1g6M1DawwfxhyFbtSI1qJZ3u6O_2hG-Ud
- Run the docker-compose file by using
  - docker-compose up -d
- The server is started on port 8000


Meaning :
- __app__ : ML model which consume message from kafka to compute then it push the result back to kafka
- __backend__ : web api to recieve text form frontend then push text to kafka after that it consume result from kafka then publish text via websocket
- __frontend__ : web page to recieve text input from user and display the result from backend via websocket
- __model-with-api__ : simple ML model with api
- __db__ : simple postgres dockerfile
- __demo_producer___ : api call and kafka push testing

Usage :
- __ลง dependencies__
  - app : pip install requirements.txt
  - backend : pip install requiremensts.txt
  - frontend : npm i

- __run server__
  - docker-compose up -d
  - app : python ปกติ
  - backend: uvicorn main:app
  - frontend: npm run serve

เข้า web localhost:8000
