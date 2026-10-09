import os
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

TABLE = "county_access_national"


def load_to_db():
    df = pd.read_csv("data/processed/national_access_merged.csv")
    engine = create_engine(os.getenv("DATABASE_URL"))
    df.to_sql(TABLE, engine, if_exists="replace", index=False)
    print(f"Loaded {len(df)} rows into '{TABLE}' table")


if __name__ == "__main__":
    load_to_db()
