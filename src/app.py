import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(os.getenv("DATABASE_URL"))

@st.cache_data
def load_data():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM county_access_national"), conn)
    return df

st.set_page_config(page_title="Healthcare Access Intelligence", layout="wide")
st.title("Healthcare Access Intelligence")
st.caption("Which U.S. counties face healthcare provider shortages, and does it track with income, insurance, or rural/urban status?")

df = load_data()
df["uninsured_rate"] = df["uninsured_est"] / df["population"] * 100

# Build a disambiguated label since county names repeat across states
df["display_label"] = df["county_name"] + ", " + df["state_full"]

county_list = sorted(df["display_label"].tolist())
selected = st.selectbox("Select a county", county_list)

row = df[df["display_label"] == selected].iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Population", f"{int(row['population']):,}")
col2.metric("Median Income", f"${int(row['median_income']):,}")
col3.metric("Shortage Areas (HPSA)", int(row["hpsa_count"]))
col4.metric("Avg Shortage Score", f"{row['avg_hpsa_score']:.1f}" if row["avg_hpsa_score"] > 0 else "None")

st.divider()

st.subheader("All U.S. Counties Ranked by Shortage Severity")
st.dataframe(
    df[["display_label", "population", "median_income", "uninsured_rate", "rucc_code", "hpsa_count", "avg_hpsa_score"]]
      .sort_values("avg_hpsa_score", ascending=False)
      .rename(columns={
          "display_label": "County", "population": "Population",
          "median_income": "Median Income", "uninsured_rate": "Uninsured %",
          "rucc_code": "Rural-Urban Code", "hpsa_count": "Shortage Areas", "avg_hpsa_score": "Avg Score"
      }),
    use_container_width=True
)

st.subheader("Key Findings")
st.write(
    "**Correlation:** Provider shortage severity shows weak correlation with income and insurance "
    "coverage, suggesting shortages are driven more by geography and provider supply than by poverty alone."
)
st.write(
    "**Predictive model:** A logistic regression model using population, income, insurance rate, and "
    "rural-urban classification predicted shortage risk across 3,222 U.S. counties with 54% accuracy — "
    "modestly better than chance, with no single feature emerging as a dominant predictor."
)