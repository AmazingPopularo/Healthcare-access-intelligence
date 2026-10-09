# Healthcare Access Intelligence

**[Live Demo](https://healthcare-access-intelligence-g26hezjxkd8lieasnu8dmq.streamlit.app)**

## Executive Summary

About **71.5 million** Americans live in federally designated primary care shortage areas, and closing that gap would take up to **~20,000** additional providers. Analyzing 3,220 U.S. counties, I found the most severe shortages concentrate in rural, lower-income, higher-uninsured counties: **82%** of the 50 worst counties are rural, with uninsured rates **3.6 points** above the national average. I grouped counties into four segments and matched each to an intervention, prioritizing Medicaid enrollment outreach, telehealth, and community health workers.

## Client Question

**Client:** a state health department or national health nonprofit
**Question:** Where should we prioritize primary care investment, and what type of intervention fits each area?

**Issue tree: why does a county lack primary care access?**
- Supply problem
  - Too few providers per capita
  - Providers are hard to recruit or retain (rural, remote)
- Demand / access problem
  - Residents can't pay (uninsured, low income)
  - Residents can't reach care (distance, rurality)

## Key Findings

| Hypothesis | Result | Evidence |
|---|---|---|
| H1: Rural counties have more severe shortages | Confirmed | Avg severity 13.9 rural vs 11.8 metro; 82% of top 50 counties are rural (vs 61% overall) |
| H2: High-uninsured counties have more severe shortages | Confirmed (moderate) | r = 0.25; top 50 counties average 12.1% uninsured vs 8.5% nationally |
| H3: Low-income counties have more shortage designations | Rejected as tested | Designation *count* scales with county size (r = 0.10 with income), but income does predict *severity* in the model |

The 50 most severe shortage counties have a median household income of **$40.8K vs $63.2K** nationally.

## Segments

| Segment | Counties | Population | Avg Uninsured | Avg Shortage Score |
|---|---|---|---|---|
| Rural & Uninsured | 544 | 13.3M | 13.6% | 17.7 |
| Rural & Remote | 298 | 7.4M | 6.0% | 17.1 |
| Urban Underserved | 449 | 130.6M | 9.1% | 17.3 |
| Lower Priority | 1,929 | 184.4M | 8.4% | 10.2 |

Rules: high shortage = above-median HPSA severity; rural = USDA RUCC 4-9; high uninsured = above the median county rate. A k-means clustering check largely agreed on the Rural & Remote and Urban Underserved groups.

## Recommendations

1. **Rural & Uninsured (544 counties):** Medicaid enrollment outreach plus FQHC expansion. Highest severity and highest uninsured rate.
2. **Rural & Remote (298 counties):** telehealth and mobile clinics. Residents are mostly insured; distance is the barrier.
3. **Urban Underserved (449 counties):** community health workers and extended clinic hours. Largest population reached.

**Long-term enabler:** NHSC loan repayment and rural residency slots to address the ~20,000-provider gap.

| | Higher feasibility | Lower feasibility |
|---|---|---|
| **Higher impact** | Enrollment outreach, telehealth | Workforce pipeline |
| **Lower impact** | Community health workers | Not prioritized |

## Sizing

- Residents in primary care HPSAs (geographic + population designations): **71.5M**
- Providers needed at HRSA's 3,500:1 threshold: **~20,000** (upper bound; existing providers not subtracted)
- Facility HPSAs were excluded because their service populations overlap with geographic designations.

## Predictive Model

Logistic regression (scikit-learn) predicting high shortage risk (above-median HPSA severity) from log population, median income, uninsured rate, and rural-urban code, with standardized features and balanced class weights.

- **ROC-AUC: 0.70**
- Accuracy: 62.5% vs a 59.9% majority-class baseline
- High-risk precision 52.6%, recall 64.7%
- Strongest predictors: population size (+0.71) and median income (-0.64)

Accuracy alone is misleading because 60% of counties fall in one class, so AUC is the main metric.

## Architecture

```
Census ACS API --+
HRSA HPSA File --+--> Python ETL --> PostgreSQL (Neon) --> FastAPI
USDA RUCC File --+                         |            --> Streamlit app
                                           |                 + Gemini county summaries
                                           +--> report.py (model, segments, sizing)
```

## Tech Stack

Python, Pandas, scikit-learn, PostgreSQL, SQLAlchemy, FastAPI, Streamlit, Gemini API, Neon

## Project Structure

```
src/
  ingest.py      # pulls Census, HRSA, and USDA data
  clean.py       # cleans and joins datasets (FIPS + county-name matching)
  load_db.py     # loads merged data into PostgreSQL
  report.py      # model metrics, findings, segmentation, sizing; writes segments to the DB
  summarize.py   # Gemini-powered county summaries grounded in the data
  api.py         # FastAPI REST layer (counties, search, segments, AI summaries)
  app.py         # Streamlit dashboard (explorer, segments, recommendations)
```

## Running Locally

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# .env needs DATABASE_URL, CENSUS_API_KEY, GEMINI_API_KEY

python src/ingest.py
python src/clean.py
python src/load_db.py
python src/report.py
streamlit run src/app.py
uvicorn src.api:app --reload    # API docs at http://127.0.0.1:8000/docs
```

## Limitations

- County-level data: shortage areas often cover only part of a county, so segment populations overstate people directly affected (use the 71.5M figure for impact).
- The model is correlational and moderate in strength (AUC 0.70). It supports prioritization, not final funding decisions.
- HPSA data has no FIPS code, so it is matched on county name; a small share of counties may show zero shortage areas due to matching gaps.
- Average shortage scores include facility HPSAs (e.g., FQHCs), which can raise scores in larger counties.
- The provider estimate is an upper bound.
- Income is not adjusted for cost of living.

## Status

- [x] Nationwide data pipeline (Census + HRSA + USDA)
- [x] PostgreSQL database and REST API
- [x] Predictive model with baseline and AUC
- [x] Segmentation, sizing, and recommendations
- [x] Deployed Streamlit app with AI summaries
- [ ] Consulting slide deck (PDF)
