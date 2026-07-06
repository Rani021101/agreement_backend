# import psycopg
# import os

# from dotenv import load_dotenv

# load_dotenv()

# def get_connection():

#     return psycopg.connect(
#         host=os.getenv("DB_HOST"),
#         port=os.getenv("DB_PORT"),
#         dbname=os.getenv("DB_NAME"),
#         user=os.getenv("DB_USER"),
#         password=os.getenv("DB_PASSWORD")
#     )


import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg2.connect(
        # "postgresql://postgres:d8MGwz48Agn2LADe@db.lobfdenviwhbaqclxrmf.supabase.co:5432/postgres"
        "postgresql://postgres.lobfdenviwhbaqclxrmf:d8MGwz48Agn2LADe@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"
    )