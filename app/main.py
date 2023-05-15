from fastapi import FastAPI
from pydantic import BaseModel,validator
from model.model import predict
from fastapi.exceptions import HTTPException

app = FastAPI()

class InputText(BaseModel):
    text: str

    @validator('text')
    def check_text(cls, v):
        if len(v) == 0:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must not be empty"})
        if type(v) is not str:
            raise HTTPException(status_code=400,detail={'status': "Bad request",'message':"texts must be string"})
        return v


class PredictedText(BaseModel):
    label: str
    text: str
    
    

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/predict", response_model=PredictedText)
def predictFromList(input_text: InputText):
    predicted = predict([input_text.text])
    return PredictedText(text=predicted[0], label=predicted[1])
    
