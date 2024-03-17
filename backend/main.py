from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import logging, shutil, global_settings, os
from preprocess import Preprocess
from datetime import datetime

# Load environment variables from .env file (if any)
load_dotenv()

preprocessor = Preprocess()

class Response(BaseModel):
    result: str | None

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000"
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/predict", response_model = Response)
def predict(question: str = Form(...), file: UploadFile = File(...)) -> Any:
    answer=''
    logging.info(f"Question received: {question}")
    
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    logging.info(f"File saved to: {file_location}")
    
    file_ext = os.path.splitext(file_location)[1]
    
    if file_ext.lower() in ['.txt', '.docx']: 
        logging.info('Detected text document')
        preprocessor.load_txt(file_location)
        answer = preprocessor.ask_ques(question)
    elif file_ext.lower() == '.csv':
        logging.info('Detected text document')
        preprocessor.load_csv(file_location)
        answer = str(preprocessor.ask_ques(question))
    
    # Save file metadata to MongoDB
    file_metadata = {
        "filename": file.filename,
        "filepath": file_location,
        "fileext": file_ext,
        "question": question,
        "upload_date": datetime.utcnow()
    }
    
    return {"result": answer}