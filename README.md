# Healthcare Access Intelligence

**[🔗 Live Demo](https://healthcare-access-intelligence-g26hezjxkd8lieasnu8dmq.streamlit.app)**

An end-to-end data pipeline and web app that identifies healthcare provider shortages across Pennsylvania counties and examines whether those shortages track with income and insurance coverage.

## Problem

Which counties in Pennsylvania have inadequate healthcare access, and does that access gap correlate with income and insurance coverage?

## Key Finding

Provider shortage severity shows weak correlation with median income (r = -0.07) and insurance coverage (r = -0.06), suggesting shortages are driven more by geography and provider supply than by poverty alone. 29 of 67 counties (43%) show both below-median income and an active shortage designation — including Philadelphia, which challenges the common assumption that healthcare shortages are a purely rural phenomenon.

## Architecture

```
Census ACS API ──┐
                  ├──▶ Python (ingest + clean) ──▶ PostgreSQL (Neon) ──▶ FastAPI ──▶ Streamlit UI
HRSA HPSA File ───┘
```

## Data Sources

- **Census ACS 5-Year Estimates** — population, median household income, insurance coverage, by county
- **HRSA Health Professional Shortage Area (HPSA) Dashboard** — provider shortage designations by county

## Tech Stack

Python · Pandas · PostgreSQL · SQLAlchemy · FastAPI · Streamlit · Neon (cloud Postgres)

## Project Structure

```
src/
├── ingest.py    # pulls raw data from Census and HRSA
├── clean.py     # cleans and joins datasets on county name
├── load_db.py   # loads processed data into PostgreSQL
├── analyze.py   # correlation analysis, at-risk county identification
├── api.py       # FastAPI REST layer over the database
└── app.py       # Streamlit interactive dashboard
```

## Running Locally

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Set DATABASE_URL and CENSUS_API_KEY in a .env file

python src/ingest.py
python src/clean.py
python src/load_db.py
streamlit run src/app.py
```

## Limitations

- Analysis currently covers Pennsylvania only
- Median income figures are not adjusted for regional cost-of-living differences
- Correlation does not establish causation — shortage designation criteria involve factors beyond what's captured here

## Status / Next Steps

- [x] Data pipeline (Census + HRSA)
- [x] PostgreSQL database
- [x] REST API
- [x] Deployed interactive UI
- [ ] FHIR-based patient data mini-project
- [ ] Predictive model for shortage risk
- [ ] LLM-powered "why is this county underserved" feature grounded in the datax