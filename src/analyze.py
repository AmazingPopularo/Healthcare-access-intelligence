import pandas as pd

def analyze():
    df = pd.read_csv("data/processed/pa_access_merged.csv")

    # Uninsured rate as a % of population, more meaningful than raw count
    df["uninsured_rate"] = df["uninsured_est"] / df["population"] * 100

    print("=== Top 10 counties by shortage severity (avg HPSA score) ===")
    print(df.sort_values("avg_hpsa_score", ascending=False)
            [["county_name", "population", "median_income", "uninsured_rate", "hpsa_count", "avg_hpsa_score"]]
            .head(10).to_string(index=False))

    print("\n=== Correlation between shortage severity and other factors ===")
    correlations = df[["avg_hpsa_score", "median_income", "uninsured_rate", "population"]].corr()["avg_hpsa_score"]
    print(correlations)

    print("\n=== Counties with shortages AND low income (below PA median) ===")
    median_income_pa = df["median_income"].median()
    at_risk = df[(df["hpsa_count"] > 0) & (df["median_income"] < median_income_pa)]
    print(f"{len(at_risk)} counties meet both criteria out of 67 total")
    print(at_risk[["county_name", "median_income", "hpsa_count", "avg_hpsa_score"]]
          .sort_values("avg_hpsa_score", ascending=False).to_string(index=False))

if __name__ == "__main__":
    analyze()