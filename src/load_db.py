import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def get_engine():
    url = os.getenv("DATABASE_URL")
    return create_engine(url)

def load_to_db():
    df = pd.read_csv("data/processed/pa_access_merged.csv")
    engine = get_engine()
    df.to_sql("county_access", engine, if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into 'county_access' table")

if __name__ == "__main__":
    load_to_db()