# Healthcare Access Intelligence

**[🔗 Live Demo](https://healthcare-access-intelligence-g26hezjxkd8lieasnu8dmq.streamlit.app)**

An end-to-end data pipeline, predictive model, and web app that identifies healthcare provider shortages across U.S. counties and examines whether those shortages track with income, insurance coverage, and rural/urban classification.

## Problem

Which U.S. counties have inadequate healthcare access, and does that access gap correlate with income, insurance coverage, or rural/urban status?

## Key Findings

**Correlation analysis:** Provider shortage severity shows weak correlation with median income and insurance coverage, suggesting shortages are driven more by geography and provider supply than by poverty alone.

**Predictive model:** A logistic regression model using population, median income, uninsured rate, and USDA rural-urban classification (RUCC) predicted shortage risk across 3,222 U.S. counties with 54% accuracy — modestly better than chance (50%), but no single feature emerged as a strong predictor (all standardized coefficients fell in a similar, modest range of 0.09–0.12). This reinforces the correlation finding: healthcare shortages are not well explained by simple socioeconomic or rural/urban factors alone. The likely drivers — provider recruitment and retention, facility distribution, local healthcare infrastructure — aren't captured in this dataset.

Negative and modest results are still real results. Being upfront about what the data does and doesn't explain is part of doing this analysis honestly.

## Architecture

```
Census ACS API ──┐
HRSA HPSA File ──┼──▶ Python (ingest + clean) ──▶ PostgreSQL (Neon) ──▶ FastAPI ──▶ Streamlit UI
USDA RUCC File ──┘                                        │
                                                            └──▶ scikit-learn model
```

## Data Sources

- **Census ACS 5-Year Estimates** — population, median household income, insurance coverage, by county (all 50 states)
- **HRSA Health Professional Shortage Area (HPSA) Dashboard** — provider shortage designations by county, nationwide
- **USDA Rural-Urban Continuum Codes (2023)** — rural/urban classification by county, nationwide

## Tech Stack

Python · Pandas · scikit-learn · PostgreSQL · SQLAlchemy · FastAPI · Streamlit · Neon (cloud Postgres)

## Project Structure

```
src/
├── ingest.py    # pulls raw data from Census, HRSA, and USDA
├── clean.py     # cleans and joins datasets on FIPS code / county name
├── load_db.py   # loads processed data into PostgreSQL
├── analyze.py   # correlation analysis, at-risk county identification
├── model.py     # logistic regression shortage-risk classifier
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
python src/model.py
streamlit run src/app.py
```

## Limitations

- Median income figures are not adjusted for regional cost-of-living differences
- Correlation does not establish causation — shortage designation criteria involve factors beyond what's captured here
- The predictive model is exploratory (54% accuracy on a binary classification) — not intended for real-world risk decisions, but useful for testing whether these specific variables carry predictive signal (they carry only modest signal)
- County name matching for HPSA data (no FIPS code in that source) resolved ~90% of counties; a small number of counties may show zero shortage areas due to name-matching gaps rather than a true absence of shortages

## Status / Next Steps

- [x] Nationwide data pipeline (Census + HRSA + USDA RUCC)
- [x] PostgreSQL database
- [x] REST API
- [x] Deployed interactive UI
- [x] Predictive model for shortage risk (exploratory, modest signal)
- [ ] FHIR-based patient data mini-project
- [ ] LLM-powered "why is this county underserved" feature grounded in the data