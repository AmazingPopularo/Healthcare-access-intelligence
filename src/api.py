import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.summarize import generate_county_summary

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))
app = FastAPI(title="Healthcare Access Intelligence API")

BASE_QUERY = """
    SELECT a.*, s.segment
    FROM county_access_national a
    LEFT JOIN county_segments s USING (fips)
"""
DEFAULT_ORDER = "ORDER BY a.avg_hpsa_score DESC NULLS LAST"


def fetch_rows(where: str = "", params: Optional[dict] = None, order: str = DEFAULT_ORDER):
    with engine.connect() as conn:
        result = conn.execute(text(f"{BASE_QUERY} {where} {order}"), params or {})
        return [dict(row._mapping) for row in result]


@app.get("/")
def root():
    return {"message": "Healthcare Access Intelligence API is running"}


@app.get("/counties")
def get_all_counties():
    """All counties with access metrics and priority segment."""
    rows = fetch_rows()
    return {"count": len(rows), "counties": rows}


@app.get("/counties/by-fips/{fips}")
def get_county_by_fips(fips: int):
    """One county by its unique FIPS code."""
    rows = fetch_rows("WHERE a.fips = :fips", {"fips": fips}, order="")
    if not rows:
        raise HTTPException(status_code=404, detail=f"FIPS code '{fips}' not found")
    return rows[0]


@app.get("/counties/by-fips/{fips}/summary")
def get_county_summary(fips: int):
    """AI-generated plain-language summary grounded in the county's data."""
    rows = fetch_rows("WHERE a.fips = :fips", {"fips": fips}, order="")
    if not rows:
        raise HTTPException(status_code=404, detail=f"FIPS code '{fips}' not found")
    county = rows[0]
    try:
        summary = generate_county_summary(county)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Summary service unavailable: {type(e).__name__}")
    return {"fips": fips, "county_name": county["county_name"],
            "state": county["state_full"], "summary": summary}


@app.get("/counties/search")
def search_counties(county_name: str, state: Optional[str] = None):
    """
    Search by county name. County names repeat across states, so filter by
    state to disambiguate. Returns all matches if state is not provided.
    """
    params = {"name": f"%{county_name}%"}
    where = "WHERE LOWER(a.county_name) LIKE LOWER(:name)"
    if state:
        where += " AND LOWER(a.state_full) = LOWER(:state)"
        params["state"] = state
    rows = fetch_rows(where, params)
    if not rows:
        raise HTTPException(status_code=404, detail=f"No county matching '{county_name}' found")
    return {"count": len(rows), "counties": rows}


@app.get("/counties/at-risk/list")
def get_at_risk_counties():
    """Counties with shortage designations AND below-median income."""
    with engine.connect() as conn:
        median_income = conn.execute(text(
            "SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY median_income) FROM county_access_national"
        )).scalar()
    rows = fetch_rows("WHERE a.hpsa_count > 0 AND a.median_income < :median", {"median": median_income})
    return {"count": len(rows), "counties": rows}


@app.get("/segments")
def get_segments():
    """Profile of each priority segment."""
    sql = """
        SELECT s.segment,
               COUNT(*) AS counties,
               SUM(a.population) AS population,
               ROUND(AVG(a.uninsured_pct)::numeric, 1) AS avg_uninsured_pct,
               ROUND(AVG(a.avg_hpsa_score)::numeric, 1) AS avg_severity
        FROM county_access_national a
        JOIN county_segments s USING (fips)
        GROUP BY s.segment
        ORDER BY avg_severity DESC
    """
    with engine.connect() as conn:
        rows = [dict(r._mapping) for r in conn.execute(text(sql))]
    return {"segments": rows}


@app.get("/segments/{segment}/counties")
def get_segment_counties(segment: str):
    """All counties in one segment, e.g. 'Rural & Uninsured'."""
    rows = fetch_rows("WHERE LOWER(s.segment) = LOWER(:segment)", {"segment": segment})
    if not rows:
        raise HTTPException(status_code=404, detail=f"Segment '{segment}' not found")
    return {"segment": segment, "count": len(rows), "counties": rows}
