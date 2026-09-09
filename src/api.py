import os
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

app = FastAPI(title="Healthcare Access Intelligence API")

@app.get("/")
def root():
    return {"message": "Healthcare Access Intelligence API is running"}

@app.get("/counties")
def get_all_counties():
    """Return all counties with their access metrics."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM county_access_national ORDER BY avg_hpsa_score DESC NULLS LAST"))
        rows = [dict(row._mapping) for row in result]
    return {"count": len(rows), "counties": rows}

@app.get("/counties/by-fips/{fips}")
def get_county_by_fips(fips: int):
    """Return access metrics for a specific county by its unique FIPS code."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM county_access_national WHERE fips = :fips"),
            {"fips": fips}
        )
        row = result.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"FIPS code '{fips}' not found")
    return dict(row._mapping)

@app.get("/counties/search")
def search_counties(county_name: str, state: str | None = None):
    """
    Search counties by name. Since county names repeat across states
    (e.g. many 'Washington County's), optionally filter by state to disambiguate.
    Returns all matches if state isn't provided.
    """
    with engine.connect() as conn:
        if state:
            result = conn.execute(
                text("""
                    SELECT * FROM county_access_national 
                    WHERE LOWER(county_name) LIKE LOWER(:name) 
                    AND LOWER(state_full) = LOWER(:state)
                """),
                {"name": f"%{county_name}%", "state": state}
            )
        else:
            result = conn.execute(
                text("SELECT * FROM county_access_national WHERE LOWER(county_name) LIKE LOWER(:name)"),
                {"name": f"%{county_name}%"}
            )
        rows = [dict(row._mapping) for row in result]
    if not rows:
        raise HTTPException(status_code=404, detail=f"No county matching '{county_name}' found")
    return {"count": len(rows), "counties": rows}

@app.get("/counties/at-risk/list")
def get_at_risk_counties():
    """Return counties with shortages AND below-median income."""
    with engine.connect() as conn:
        median_result = conn.execute(text("SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_income) FROM county_access_national"))
        median_income = median_result.scalar()

        result = conn.execute(
            text("""
                SELECT * FROM county_access_national 
                WHERE hpsa_count > 0 AND median_income < :median
                ORDER BY avg_hpsa_score DESC NULLS LAST
            """),
            {"median": median_income}
        )
        rows = [dict(row._mapping) for row in result]
    return {"count": len(rows), "counties": rows}