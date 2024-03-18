from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import logging, shutil, global_settings, os, utils, sys
from chatbot import Bot
from dbhandler import DBHandler
from datetime import datetime

load_dotenv()

preprocessor = Bot()
dbhandler = DBHandler()

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
async def predict(question: str = Form(...), file: UploadFile = File(...)) -> Any:
    try:
        status, isError = dbhandler.initial_check()
        if isError: raise Exception(status)
        # raise Exception('Testing')
        answer=''
        logging.info(f"Question received: {question}")
        
        file_location = f"uploads/{file.filename}"
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logging.info(f"File saved to: {file_location}")
        
        file_ext = os.path.splitext(file_location)[1]
        file_hash = utils.get_file_hash(file_location)
        file_size = round(utils.get_file_size(file_location), 4)
        
        if (file_size / 1024) >= 100: 
            raise Exception('File size exceeds 100 MB limit.')
        else:
            if file_ext.lower() in ['.txt', '.docx', '.pdf']: 
                logging.info('Detected text document')
                preprocessor.load_file(file_location, ext=file_ext.lower(), file_exists=dbhandler.check_hash_exists(file_hash), collection_name=file_hash[:63])
                answer = preprocessor.ask_ques(question)
            elif file_ext.lower() == '.csv':
                logging.info('Detected text document')
                preprocessor.load_csv(file_location)
                answer = str(preprocessor.ask_ques(question))
            else:
                raise Exception("Cannot read the file provided. Unsupported File type. Only .pdf, .csv, .txt and .docx extensions are supported.")
        
        # Save file metadata to MongoDB
        file_metadata = {
            "filename": file.filename,
            "filepath": file_location,
            "fileext": file_ext,
            "question": question,
            "upload_date": datetime.now(),
            "filesize (KB)": file_size,
            "filehash": file_hash,
            "content_type": file.content_type,
            "answer": answer
        }
        
        print('file_metadata', file_metadata)
        
        dbhandler.insert_one(file_metadata)   
        
        return {"result": {"answer": answer, "isError": "false"}}
    except Exception as ex:
        _, _, line = sys.exc_info()
        logging.error(f'Error in predict: {str(ex)}. Line No.{line.tb_lineno}')
        return {"result": {"answer": str(ex), "isError": "true"}}