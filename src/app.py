import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

engine = create_engine(os.getenv("DATABASE_URL"))

@st.cache_data
def load_data():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM county_access"), conn)
    return df

st.set_page_config(page_title="Healthcare Access Intelligence", layout="wide")
st.title("Healthcare Access Intelligence")
st.caption("Which Pennsylvania counties face healthcare provider shortages, and does it track with income?")

df = load_data()
df["uninsured_rate"] = df["uninsured_est"] / df["population"] * 100

county_list = sorted(df["county_name"].tolist())
selected = st.selectbox("Select a county", county_list)

row = df[df["county_name"] == selected].iloc[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Population", f"{int(row['population']):,}")
col2.metric("Median Income", f"${int(row['median_income']):,}")
col3.metric("Shortage Areas (HPSA)", int(row["hpsa_count"]))
col4.metric("Avg Shortage Score", f"{row['avg_hpsa_score']:.1f}" if row["avg_hpsa_score"] > 0 else "None")

st.divider()

st.subheader("All 67 Counties Ranked by Shortage Severity")
st.dataframe(
    df[["county_name", "population", "median_income", "uninsured_rate", "hpsa_count", "avg_hpsa_score"]]
      .sort_values("avg_hpsa_score", ascending=False)
      .rename(columns={
          "county_name": "County", "population": "Population",
          "median_income": "Median Income", "uninsured_rate": "Uninsured %",
          "hpsa_count": "Shortage Areas", "avg_hpsa_score": "Avg Score"
      }),
    use_container_width=True
)

st.subheader("Key Finding")
st.write(
    "Provider shortage severity shows weak correlation with income (r = -0.07) and insurance "
    "coverage (r = -0.06), suggesting shortages are driven more by geography and provider supply "
    "than by poverty alone. 29 of 67 counties (43%) show both below-median income and active "
    "shortage designations — including Philadelphia, challenging the assumption that shortages "
    "are a purely rural phenomenon."
)