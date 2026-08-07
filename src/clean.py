import pandas as pd

def load_census():
    df = pd.read_csv("data/raw/pa_census_county.csv")
    df = df.rename(columns={
        "B01003_001E": "population",
        "B19013_001E": "median_income",
        "B27010_017E": "uninsured_est",
    })
    # NAME looks like "Adams County, Pennsylvania" — extract just "Adams"
    df["county_name"] = df["NAME"].str.extract(r"^(.+?) County,")
    return df[["county_name", "population", "median_income", "uninsured_est"]]

def load_hpsa():
    df = pd.read_csv("data/raw/hpsa_national.csv", low_memory=False)
    # Filter to Pennsylvania and Primary Care shortage areas only, for v1
    df = df[(df["State"] == "Pennsylvania") & (df["Discipline"] == "Primary Care")]
    # County column may have extra whitespace/casing issues — clean it
    df["county_name"] = df["County"].str.strip()
    return df

def merge_datasets():
    census = load_census()
    hpsa = load_hpsa()

    # Count HPSA designations per county, and average HPSA score (higher = more severe shortage)
    hpsa_summary = hpsa.groupby("county_name").agg(
        hpsa_count=("HPSA ID", "count"),
        avg_hpsa_score=("HPSA Score", "mean")
    ).reset_index()

    merged = census.merge(hpsa_summary, on="county_name", how="left")
    # Counties with no HPSA match likely have zero shortage areas
    merged["hpsa_count"] = merged["hpsa_count"].fillna(0)
    merged["avg_hpsa_score"] = merged["avg_hpsa_score"].fillna(0)

    return merged

if __name__ == "__main__":
    df = merge_datasets()
    print(df.sort_values("avg_hpsa_score", ascending=False).head(10))
    df.to_csv("data/processed/pa_access_merged.csv", index=False)
    print(f"\nSaved {len(df)} counties to data/processed/pa_access_merged.csv")