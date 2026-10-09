"""
Consulting analysis: model metrics, descriptive findings, segmentation, sizing.
Reads county_access_national, writes segment labels to county_segments
(used by the app and API) and to data/processed/segments.csv.
"""
import os
import warnings
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score, roc_auc_score, precision_score, recall_score

warnings.filterwarnings("ignore", category=RuntimeWarning)  # spurious macOS numpy matmul warnings

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))
with engine.connect() as conn:
    df = pd.read_sql(text("SELECT * FROM county_access_national ORDER BY fips"), conn)

df = df[(df["median_income"] > 0) & (df["uninsured_pct"] >= 0)].dropna(subset=["rucc_code"]).copy()

# ---------- PHASE 2: model metrics ----------
cut = df.loc[df["avg_hpsa_score"] > 0, "avg_hpsa_score"].median()
df["high_risk"] = (df["avg_hpsa_score"] > cut).astype(int)
df["log_pop"] = np.log(df["population"])
feats = ["log_pop", "median_income", "uninsured_pct", "rucc_code"]

X_tr, X_te, y_tr, y_te = train_test_split(
    df[feats], df["high_risk"], test_size=0.25, random_state=42, stratify=df["high_risk"])
sc = StandardScaler().fit(X_tr)
m = LogisticRegression(class_weight="balanced", max_iter=1000).fit(sc.transform(X_tr), y_tr)
prob = m.predict_proba(sc.transform(X_te))[:, 1]
pred = (prob >= 0.5).astype(int)
baseline = max(y_te.mean(), 1 - y_te.mean())

print("=== PHASE 2: MODEL ===")
print(f"Counties: {len(df)}")
print(f"Accuracy: {accuracy_score(y_te, pred):.1%}  | Baseline (majority class): {baseline:.1%}")
print(f"ROC-AUC: {roc_auc_score(y_te, prob):.3f}")
print(f"Precision (high-risk): {precision_score(y_te, pred):.1%}  | Recall: {recall_score(y_te, pred):.1%}")
coefs = pd.Series(m.coef_[0], index=feats).sort_values(key=abs, ascending=False)
print("Standardized coefficients (ranked):")
print(coefs.round(3).to_string())

# ---------- PHASE 3: descriptive findings ----------
nat_unins = np.average(df["uninsured_pct"], weights=df["population"])
nat_income = df["median_income"].median()
top50 = df.sort_values(["avg_hpsa_score", "hpsa_count"], ascending=False).head(50)
top_unins = np.average(top50["uninsured_pct"], weights=top50["population"])
rural = df["rucc_code"] >= 4

print("\n=== PHASE 3: FINDINGS ===")
print(f"% of top 50 shortage counties that are rural (RUCC 4-9): {(top50['rucc_code'] >= 4).mean():.0%}")
print(f"National share of counties that are rural: {rural.mean():.0%}")
print(f"Uninsured: top 50 {top_unins:.1f}% vs national {nat_unins:.1f}% (gap {top_unins - nat_unins:+.1f} pts)")
print(f"Median income: top 50 ${top50['median_income'].median():,.0f} vs national ${nat_income:,.0f}")
print(f"H1 avg severity: rural {df.loc[rural, 'avg_hpsa_score'].mean():.2f} vs metro {df.loc[~rural, 'avg_hpsa_score'].mean():.2f}")
print(f"H2 corr(uninsured %, severity): {df['uninsured_pct'].corr(df['avg_hpsa_score']):.3f}")
print(f"H3 corr(income, # shortage areas): {df['median_income'].corr(df['hpsa_count']):.3f}")

# ---------- PHASE 4: segmentation ----------
hi_unins = df["uninsured_pct"] > df["uninsured_pct"].median()
short = df["high_risk"] == 1
df["segment"] = np.select(
    [short & rural & hi_unins, short & rural & ~hi_unins, short & ~rural],
    ["Rural & Uninsured", "Rural & Remote", "Urban Underserved"],
    default="Lower Priority")
seg = df.groupby("segment").agg(
    counties=("fips", "count"),
    population=("population", "sum"),
    avg_uninsured_pct=("uninsured_pct", "mean"),
    avg_severity=("avg_hpsa_score", "mean"),
).round(1)
print("\n=== PHASE 4: SEGMENTS ===")
print(seg.to_string())

km = KMeans(n_clusters=4, n_init=10, random_state=42).fit(
    StandardScaler().fit_transform(df[feats + ["avg_hpsa_score"]]))
print("\nK-means check (rows = rules-based segment, cols = cluster):")
print(pd.crosstab(df["segment"], km.labels_).to_string())

# ---------- PHASE 5: sizing ----------
h = pd.read_csv("data/raw/hpsa_national.csv", low_memory=False)
h = h[(h["Discipline"] == "Primary Care") & (h["HPSA Status"] == "Designated")
      & (h["HPSA Type (Category)"] != "Facility")]
h = h.drop_duplicates("HPSA ID")
desig_pop = pd.to_numeric(h["HPSA Designation Population"], errors="coerce").sum()
priority_pop = df.loc[df["segment"] != "Lower Priority", "population"].sum()

print("\n=== PHASE 5: SIZING ===")
print(f"Residents in HPSA-designated areas: {desig_pop / 1e6:.1f}M")
print(f"Providers needed at 3,500:1 (upper bound, existing providers not subtracted): {desig_pop / 3500:,.0f}")
print(f"Residents in the 3 priority segments: {priority_pop / 1e6:.1f}M")

# ---------- Save segments for app + API ----------
df[["fips", "segment", "high_risk"]].to_sql("county_segments", engine, if_exists="replace", index=False)
df.to_csv("data/processed/segments.csv", index=False)
print("\nSaved segments to 'county_segments' table and data/processed/segments.csv")
