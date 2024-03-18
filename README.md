# ProtonDatalabs AI developer Assignment - Chatbot application

## Assumption made
User will upload at least one file before starting a chat with a bot.
File selection/upload and a chat message is mandatory to proceed with the bot.

## The Approach to completing the assignment

### Backend

First I updated the predict function in main.py to receive data from the frontend. Then I added logging functionality to log Info level logs in file. Then I saved the received file in the uploads folder. Calculated metadata for this file like file hash, file size, file type, etc. As this data will help us later in identifying whether the file was previously uploaded, size is below 100MB and type of the file is among the accepted file type i.e .csv, .txt, .docx and .pdf. This data is uploaded to the Mongo Atlas DB to refrence later as well as keep track of this data. Once everything is as expected this file will be further processed to create vector embeddings and then store in vectorstore, in our case ChromaDB. If this file was referred earlier no processing will be carried out on that file instead it will refer previously created vector embeddings. Now whenever a query is made on this file, the most relevant data will be gathered and passed as a context and the query itself to the LLM which is in our case gpt-3.5-turbo. This prompt along with history of previous query and response will be created using LangChain library. Exception for this is only csv file which is passed directly to pandasai which is utilizing the same LLM and its independent sets of tools. This app is further deployed in AWS EC2 instance and configured under gunicorn and Apache2.

##### Tech Stack and Libraries
Python 3.10, FastAPI, Pypdf2, Pandasai, Langchain, ChromaDB, MongoDB, Gunicorn and Apache2

### Frontend

First I updated the file input to accept desired file types only i.e .csv, .txt, .docx and .pdf. Added validation to check whether file is below 100MB and of desired file type only. Created chat window, file attach button, message box and a send button. Added a Dark Theme for asthetic purpose. Added a custom scrollbar. Added an indicator for file Referring at. Added toast as notifications for user-friendly alerts. Bot and user chat bubbles added in chat window. Most of the components are used from Chakra UI Library. Updated fetch endpoint. Updated UI for good look. This is further deployed in AWS S3 Bucket.

##### Tech Stack and Libraries
React, ChakraUI and AWS S3

