import os
import sys

# Make "from src..." imports work locally and on Streamlit Cloud
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from src.summarize import generate_county_summary

load_dotenv()

st.set_page_config(page_title="Healthcare Access Intelligence", layout="wide")

SEGMENT_ORDER = ["Rural & Uninsured", "Rural & Remote", "Urban Underserved", "Lower Priority"]

RECOMMENDATIONS = {
    "Rural & Uninsured": "Medicaid enrollment outreach plus FQHC expansion. Both coverage and provider supply are gaps here.",
    "Rural & Remote": "Telehealth and mobile clinics. Most residents are insured; distance to care is the barrier.",
    "Urban Underserved": "Community health workers and extended clinic hours. Care exists nearby, but access is uneven.",
    "Lower Priority": "Monitor. Shortage severity is below the national midpoint.",
}


@st.cache_resource
def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))


@st.cache_data(ttl=3600)
def load_data():
    query = text("""
        SELECT a.*, s.segment
        FROM county_access_national a
        LEFT JOIN county_segments s USING (fips)
    """)
    with get_engine().connect() as conn:
        df = pd.read_sql(query, conn)
    df["segment"] = df["segment"].fillna("Lower Priority")
    df["display_label"] = df["county_name"] + ", " + df["state_full"]
    return df


df = load_data()

seg = (
    df.groupby("segment")
    .agg(**{
        "Counties": ("fips", "count"),
        "Population": ("population", "sum"),
        "Avg Uninsured %": ("uninsured_pct", "mean"),
        "Avg Shortage Score": ("avg_hpsa_score", "mean"),
    })
    .reindex(SEGMENT_ORDER)
    .round(1)
)

st.title("Healthcare Access Intelligence")
st.caption(
    "Where should a health department prioritize primary care investment, "
    "and what type of intervention fits each area? Analysis of 3,220 U.S. counties."
)

tab_explore, tab_segments, tab_recs, tab_about = st.tabs(
    ["County Explorer", "Segments", "Recommendations", "Findings & Method"]
)

# ---------- County Explorer ----------
with tab_explore:
    seg_choice = st.selectbox("Filter by segment", ["All segments"] + SEGMENT_ORDER)
    view = df if seg_choice == "All segments" else df[df["segment"] == seg_choice]

    selected = st.selectbox("Select a county", sorted(view["display_label"].tolist()))
    row = view[view["display_label"] == selected].iloc[0]

    c1, c2, c3 = st.columns(3)
    c1.metric("Population", f"{int(row['population']):,}")
    c2.metric("Median Income", f"${int(row['median_income']):,}")
    c3.metric("Uninsured", f"{row['uninsured_pct']:.1f}%")
    c4, c5, c6 = st.columns(3)
    c4.metric("Shortage Areas (HPSA)", int(row["hpsa_count"]))
    c5.metric("Avg Shortage Score", f"{row['avg_hpsa_score']:.1f}" if row["avg_hpsa_score"] > 0 else "None")
    c6.metric("Segment", row["segment"])

    st.info(f"**Recommended intervention:** {RECOMMENDATIONS[row['segment']]}")

    st.subheader("AI-Generated Summary")
    if st.button("Generate summary for this county"):
        with st.spinner("Generating summary..."):
            try:
                st.write(generate_county_summary(row.to_dict()))
            except Exception as e:
                st.error(f"Summary unavailable right now ({type(e).__name__}).")

    st.subheader(f"Counties ranked by shortage severity: {seg_choice}")
    st.dataframe(
        view[["display_label", "segment", "population", "median_income", "uninsured_pct",
              "rucc_code", "hpsa_count", "avg_hpsa_score"]]
        .sort_values("avg_hpsa_score", ascending=False)
        .rename(columns={
            "display_label": "County", "segment": "Segment", "population": "Population",
            "median_income": "Median Income", "uninsured_pct": "Uninsured %",
            "rucc_code": "Rural-Urban Code", "hpsa_count": "Shortage Areas",
            "avg_hpsa_score": "Avg Score",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ---------- Segments ----------
with tab_segments:
    st.subheader("Four county archetypes")
    st.dataframe(seg, use_container_width=True)
    st.bar_chart(seg["Counties"])
    st.caption(
        "Rules: high shortage = above-median HPSA severity score; rural = USDA RUCC 4-9; "
        "high uninsured = above the median county uninsured rate. A k-means clustering check "
        "largely agreed on the Rural & Remote and Urban Underserved groups."
    )

# ---------- Recommendations ----------
with tab_recs:
    st.subheader("Top 3 recommendations")
    for i, name in enumerate(SEGMENT_ORDER[:3], start=1):
        s = seg.loc[name]
        st.markdown(
            f"**{i}. {name}** ({int(s['Counties'])} counties, "
            f"{s['Population'] / 1e6:.1f}M residents, {s['Avg Uninsured %']:.1f}% uninsured): "
            f"{RECOMMENDATIONS[name]}"
        )
    st.markdown(
        "**Long-term enabler:** roughly 71.5M residents live in designated primary care shortage areas. "
        "Serving them at HRSA's 3,500:1 threshold would take up to ~20,000 additional providers "
        "(upper bound). NHSC loan repayment and rural residency slots close this gap over several years."
    )

    st.subheader("Impact vs. feasibility")
    st.table(pd.DataFrame(
        {
            "Higher feasibility": [
                "Enrollment outreach (Rural & Uninsured); telehealth (Rural & Remote)",
                "Community health workers (Urban Underserved)",
            ],
            "Lower feasibility": [
                "Workforce pipeline: NHSC loan repayment, rural residencies",
                "Not prioritized",
            ],
        },
        index=["Higher impact", "Lower impact"],
    ))

# ---------- Findings & Method ----------
with tab_about:
    st.subheader("Key findings")
    st.markdown(
        "- **82%** of the 50 most severe shortage counties are rural, vs 61% of all counties.\n"
        "- Those counties average **12.1% uninsured vs 8.5% nationally** (+3.6 points) and a median "
        "income of $40.8K vs $63.2K.\n"
        "- Rural counties average a higher shortage score than metro counties (13.9 vs 11.8).\n"
        "- **~71.5M residents** live in primary care shortage areas; closing the gap would take up to "
        "**~20,000 providers**."
    )
    st.subheader("Predictive model")
    st.markdown(
        "Logistic regression on population (log), median income, uninsured rate, and rural-urban code. "
        "**ROC-AUC 0.70**; accuracy 62.5% vs a 59.9% majority-class baseline. Population size and "
        "median income were the strongest predictors, with lower income linked to higher shortage risk."
    )
    st.subheader("Data sources")
    st.markdown(
        "- Census ACS 5-Year (2023): population, median household income, % uninsured (S2701)\n"
        "- HRSA HPSA Dashboard: primary care shortage designations and severity scores\n"
        "- USDA Rural-Urban Continuum Codes (2023)"
    )
    st.subheader("Limitations")
    st.markdown(
        "- County-level data: shortage areas often cover part of a county, so segment populations "
        "overstate people directly affected.\n"
        "- The model is correlational and moderate in strength; it supports prioritization, not final decisions.\n"
        "- HPSA data has no FIPS code, so it is matched on county name; a small share of counties may "
        "show zero shortage areas due to matching gaps.\n"
        "- The provider estimate is an upper bound because existing providers are not subtracted.\n"
        "- Income is not adjusted for cost of living."
    )
