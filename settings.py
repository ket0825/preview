import logging
import os
from dotenv import load_dotenv

log_level = logging.INFO
load_dotenv(dotenv_path='env/.env')
STAGE = os.getenv('STAGE') if os.getenv('STAGE') else "local" 

if STAGE == 'local':
    URL = os.getenv('LOCAL_URL') if os.getenv('URL') else "http://localhost:5000/api"
    REVIEW_URL = os.getenv('LOCAL_REVIEW_URL')
elif STAGE == 'dev':
    URL = os.getenv('DEV_URL')
    REVIEW_URL = os.getenv('DEV_REVIEW_URL')
elif STAGE == 'prod':
    URL = os.getenv('PROD_URL')
    REVIEW_URL = os.getenv('PROD_REVIEW_URL')
    OCR_URL = os.getenv('PROD_OCR_URL')
    
