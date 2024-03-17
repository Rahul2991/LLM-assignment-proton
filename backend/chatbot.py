from langchain_community.document_loaders import TextLoader
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain import hub
import logging, os, chromadb, global_settings
import pandas as pd
from pandasai import SmartDataframe
from operator import itemgetter
from langchain.memory import ConversationBufferMemory
from langchain.prompts.prompt import PromptTemplate
from langchain_core.messages import get_buffer_string
from langchain_core.prompts import format_document, ChatPromptTemplate

class Bot:
    def __init__(self) -> None:
        self.text_splitter = CharacterTextSplitter(        
            separator = "\n",
            chunk_size = 1000,
            chunk_overlap  = 200, #striding over the text
            length_function = len,
        )
        # self.rag_prompt = hub.pull("rlm/rag-prompt")
        
        self.llm=ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0,
                openai_api_key=os.getenv('OPEN_AI_API')
            )
        self.vdb_loc = os.path.join(global_settings.vector_db_loc, 'emb.db')
        self.chroma_client = chromadb.PersistentClient(path=self.vdb_loc)
        self.memory = ConversationBufferMemory(
            return_messages=True, output_key="answer", input_key="question"
        )
        self.loaded_memory = RunnablePassthrough.assign(
            chat_history=RunnableLambda(self.memory.load_memory_variables) | itemgetter("history"),
        )
        
        _template = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

        Chat History:
        {chat_history}
        Follow Up Input: {question}
        Standalone question:"""
        
        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_template)
        
        self.standalone_question = {
            "standalone_question": {
                "question": lambda x: x["question"],
                "chat_history": lambda x: get_buffer_string(x["chat_history"]),
            }
            | CONDENSE_QUESTION_PROMPT
            | self.llm
            | StrOutputParser(),
        }
        # self.emb_db = Chroma(persist_directory=self.vdb_loc, embedding_function=OpenAIEmbeddings(), client=self.chroma_client)
    
    def load_file(self, file_loc, ext='.txt', file_exists=False, collection_name='default'):
        self.ext=ext
        logging.info('Loading document')
        if not file_exists:
            if self.ext.lower() in ['.txt', '.docx']:   
                loader = TextLoader(file_loc)
                text_data = loader.load()
                source_data = self.text_splitter.split_documents(text_data)
            elif self.ext.lower() == '.pdf':
                pdf_data = PdfReader(file_loc)
                raw_text = ''
                for page in pdf_data.pages:
                    text = page.extract_text()
                    if text:
                        raw_text += text
                source_data = self.text_splitter.split_text(raw_text)
                           
            self.ingest_to_vectordb(source_data, collection_name)
        else: self.ingest_to_vectordb(collection_name=collection_name, collection_exists=True)
        logging.info('Loading document successful')
        
    def load_csv(self, csv_file_loc):
        self.ext='.csv'
        df = pd.read_csv(csv_file_loc)
        self.csv_llm = SmartDataframe(df, config={"llm": self.llm, "verbose": True, "save_charts":True, "open_charts":False})
    
    def format_docs(self, docs):
        prompt = "\n\n".join(doc.page_content for doc in docs)
        return prompt
        
    def ingest_to_vectordb(self, source_data=None, collection_name='default', collection_exists=False):
        if collection_exists:
            self.emb_db = Chroma(
                client=self.chroma_client,
                collection_name=collection_name,
                embedding_function=OpenAIEmbeddings(openai_api_key=os.getenv('OPEN_AI_API')),
            )
            logging.info('Loading previously created vectors for this file')
        else:
            logging.info('Ingesting to chromadb')
            for i in range(0, len(source_data), 500):
                if len(source_data)<i+500:
                    if self.ext=='.pdf':
                        self.emb_db = Chroma.from_texts(
                            source_data[i:], 
                            OpenAIEmbeddings(openai_api_key=os.getenv('OPEN_AI_API')), 
                            client=self.chroma_client, 
                            collection_name=collection_name
                        )
                    elif self.ext.lower() in ['.txt', '.docx']:
                        self.emb_db = Chroma.from_documents(
                            source_data[i:], 
                            OpenAIEmbeddings(openai_api_key=os.getenv('OPEN_AI_API')), 
                            client=self.chroma_client, 
                            collection_name=collection_name
                        )
                else:
                    if self.ext=='.pdf':
                        self.emb_db = Chroma.from_texts(
                            source_data[i:i+500], 
                            OpenAIEmbeddings(openai_api_key=os.getenv('OPEN_AI_API')), 
                            client=self.chroma_client, 
                            collection_name=collection_name
                        )
                    elif self.ext.lower() in ['.txt', '.docx']:
                        self.emb_db = Chroma.from_documents(
                            source_data[i:i+500], 
                            OpenAIEmbeddings(openai_api_key=os.getenv('OPEN_AI_API')), 
                            client=self.chroma_client, 
                            collection_name=collection_name
                        )
            # vectorstore = Chroma.from_documents(documents=source_data, embedding=OpenAIEmbeddings(openai_api_key=os.getenv('OPEN_AI_API')))
            logging.info('Ingestion to chromadb successful')
    
    def _combine_documents(
        self, docs, document_prompt=PromptTemplate.from_template(template="{page_content}"), document_separator="\n\n"
    ):
        doc_strings = [format_document(doc, document_prompt) for doc in docs]
        return document_separator.join(doc_strings)

    def prepare_chain(self):
        retriever = self.emb_db.as_retriever()
        logging.info('Preparing Conversational Chain')
        # self.qa_chain = (
        #     {"context": retriever | self.format_docs, "question": RunnablePassthrough()}
        #     | self.rag_prompt
        #     | self.llm
        #     | StrOutputParser()
        # )
        retrieved_documents = {
            "docs": itemgetter("standalone_question") | retriever,
            "question": lambda x: x["standalone_question"],
        }
        final_inputs = {
            "context": lambda x: self._combine_documents(x["docs"]),
            "question": itemgetter("question"),
        }
        template = """Answer the question based only on the following context:
        {context}

        Question: {question}
        """
        ANSWER_PROMPT = ChatPromptTemplate.from_template(template)
        
        answer = {
            "answer": final_inputs | ANSWER_PROMPT | self.llm,
            "docs": itemgetter("docs"),
        }
        
        self.final_chain = self.loaded_memory | self.standalone_question | retrieved_documents | answer
        logging.info('Preparation of Conversational Chain Successful')
    
    def ask_ques(self, question):
        self.prepare_chain()
        if self.ext=='.csv':
            answer = str(self.csv_llm.chat(question))
        else:
            logging.info('Answering question now')
            # answer = self.qa_chain.invoke(question)
            inputs = {"question": question}
            result = self.final_chain.invoke(inputs)
            self.memory.save_context(inputs, {"answer": result["answer"].content})
            self.memory.load_memory_variables({})
            answer = result["answer"].content
            logging.info('Answering received sending back to frontend')
        return answer