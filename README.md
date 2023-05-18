# thai-problem-prediction-app
A __FastAPI__ application to predict classification's answer.
It uses __Wangchan berta's model__ to classify text into problem's topic in Thai.

- Please download folder "model.pth" and put it in /app/model/ ( The model.pth is too large for github )
  - from here https://drive.google.com/drive/folders/1g6M1DawwfxhyFbtSI1qJZ3u6O_2hG-Ud
- Run the docker-compose file by using
  - docker-compose up -d
- The server is started on port 8000


Meaning :
- app : ML model which consume message from kafka to compute then it push the result back to kafka
- backend : web api to recieve text form frontend then push text to kafka after that it consume result from kafka then publish text via websocket
- frontend : web page to recieve text input from user and display the result from backend via websocket
- model-with-api : simple ML model with api
- db : simple postgres dockerfile
- demo_porducer : api call and kafka push testing

Usage :
- ลง dependencies
  - app : pip install requirements.txt
  - backend : pip install requiremensts.txt
  - frontend : npm i

- run server
  - docker-compose up -d
  - app : python ปกติ
  - backend: uvicorn main:app
  - frontend: npm run serve

เข้า web localhost:8000