import os, logging
from datetime import datetime

os.makedirs('uploads', exist_ok=True)
os.makedirs('logs', exist_ok=True)

vector_db_loc = 'vectordb'

os.makedirs(vector_db_loc, exist_ok=True)

logFile = os.path.join('logs', datetime.now().strftime('%y_%m_%d_%H_%M_%S_%f'))
logFormat = '%(asctime)s | %(name)s | %(module)s %(filename)s %(funcName)s | %(levelname)s | %(message)s'
logging.basicConfig(filename=logFile, level=logging.INFO, format=logFormat, filemode='w', force=True)