from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain import hub
import logging, os
import pandas as pd
from pandasai import SmartDataframe
from pandasai.llm import OpenAI

class Preprocess:
    def __init__(self) -> None:
        self.text_splitter = CharacterTextSplitter(        
            separator = "\n",
            chunk_size = 1000,
            chunk_overlap  = 200, #striding over the text
            length_function = len,
        )
        self.rag_prompt = hub.pull("rlm/rag-prompt")
        
        self.llm=ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=os.getenv('OPEN_AI_API')
            )
    
    def load_txt(self, txt_file_loc, ext='.txt'):
        self.ext=ext
        logging.info('Loading text document')
        loader = TextLoader(txt_file_loc)
        text_data = loader.load()
        source_data = self.text_splitter.split_documents(text_data)
        logging.info('Loading text document successful')
        self.ingest_to_vectordb(source_data)
        
    def load_csv(self, csv_file_loc):
        self.ext='.csv'
        df = pd.read_csv(csv_file_loc)
        self.csv_llm = SmartDataframe(df, config={"llm": self.llm, "verbose": True, "save_charts":True, "open_charts":False})
    
    def format_docs(self, docs):
        return "\n\n".join(doc.page_content for doc in docs)
        
    def ingest_to_vectordb(self, source_data):
        logging.info('Ingesting to chromadb')
        vectorstore = Chroma.from_documents(documents=source_data, embedding=OpenAIEmbeddings(openai_api_key=os.getenv('OPEN_AI_API')))
        logging.info('Ingestion to chromadb successful')
        retriever = vectorstore.as_retriever()
        logging.info('Preparing RAG based QA Chain')
        self.qa_chain = (
            {"context": retriever | self.format_docs, "question": RunnablePassthrough()}
            | self.rag_prompt
            | self.llm
            | StrOutputParser()
        )
        logging.info('Preparation of RAG based QA Chain Successful')
    
    def ask_ques(self, question):
        if self.ext=='.csv':
            answer = self.csv_llm.chat(question)
            print(answer)
        else:
            logging.info('Answering question now')
            answer = self.qa_chain.invoke(question)
            logging.info('Answering received sending back to frontend')
        return answer