import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

app = FastAPI(title="Healthcare Access Intelligence API")

@app.get("/")
def root():
    return {"message": "Healthcare Access Intelligence API is running"}

@app.get("/counties")
def get_all_counties():
    """Return all counties with their access metrics."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM county_access ORDER BY avg_hpsa_score DESC NULLS LAST"))
        rows = [dict(row._mapping) for row in result]
    return {"count": len(rows), "counties": rows}

@app.get("/counties/{county_name}")
def get_county(county_name: str):
    """Return access metrics for a specific county."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM county_access WHERE LOWER(county_name) = LOWER(:name)"),
            {"name": county_name}
        )
        row = result.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"County '{county_name}' not found")
    return dict(row._mapping)

@app.get("/counties/at-risk/list")
def get_at_risk_counties():
    """Return counties with shortages AND below-median income."""
    with engine.connect() as conn:
        median_result = conn.execute(text("SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_income) FROM county_access"))
        median_income = median_result.scalar()

        result = conn.execute(
            text("""
                SELECT * FROM county_access 
                WHERE hpsa_count > 0 AND median_income < :median
                ORDER BY avg_hpsa_score DESC NULLS LAST
            """),
            {"median": median_income}
        )
        rows = [dict(row._mapping) for row in result]
    return {"count": len(rows), "counties": rows}