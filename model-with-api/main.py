from fastapi import FastAPI
from pydantic import BaseModel,validator
from model.model import predict
from fastapi.exceptions import HTTPException

app = FastAPI()

class InputText(BaseModel):
    texts: list

    @validator('texts')
    def check_texts(cls, v):
        if len(v) == 0:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must not be empty"})
        if type(v) is not list:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must be list"})
        if len(v) > 100:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must not be more than 100"})
        # check if each element is string
        for text in v:
            if type(text) is not str:
                raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must be string"})
        return v


class PredictedText(BaseModel):
    predicted: list
    
    

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictedText)
def predictFromList(input_text: InputText):
    predicted = predict(input_text.texts)
    return PredictedText(predicted=predicted)
    
