# thai-problem-prediction-app
A __FastAPI__ application to predict classification's answer.
It uses __Wangchan berta's model__ to classify text into problem's topic in Thai.

- Please download folder "model.pth" and put it in /app/model/ ( The model.pth is too large for github )
  - from here https://drive.google.com/drive/folders/1g6M1DawwfxhyFbtSI1qJZ3u6O_2hG-Ud
- Run the docker-compose file by using
  - docker-compose up -d
- The server is started on port 8000
