import pandas as pd

def load_census():
    df = pd.read_csv("data/raw/census_county_national.csv")
    df = df.rename(columns={
        "B01003_001E": "population",
        "B19013_001E": "median_income",
        "B27010_017E": "uninsured_est",
    })
    df["state"] = df["state"].astype(str).str.zfill(2)
    df["county"] = df["county"].astype(str).str.zfill(3)
    df["fips"] = df["state"] + df["county"]
    df["fips"] = df["fips"].astype(int)
    df["county_name"] = df["NAME"].str.extract(r"^(.+?),")
    df["state_full"] = df["NAME"].str.extract(r",\s*(.+)$")
    # Strip common county-type suffixes so it matches HPSA's bare county names
    df["county_match"] = df["county_name"].str.replace(
        r"\s+(County|Parish|Borough|Census Area|Municipality)$", "", regex=True
    )
    return df[["fips", "county_name", "county_match", "state_full", "population", "median_income", "uninsured_est"]]

def load_hpsa():
    df = pd.read_csv("data/raw/hpsa_national.csv", low_memory=False)
    df = df[df["Discipline"] == "Primary Care"]
    df["county_clean"] = df["County"].str.strip()
    df["state_clean"] = df["State"].str.strip()
    return df

def load_rucc():
    df = pd.read_csv("data/raw/rucc_national.csv")
    pivoted = df.pivot(index=["FIPS", "State", "County_Name"], columns="Attribute", values="Value").reset_index()
    pivoted = pivoted.rename(columns={"FIPS": "fips", "RUCC_2023": "rucc_code"})
    pivoted["rucc_code"] = pd.to_numeric(pivoted["rucc_code"], errors="coerce")
    return pivoted[["fips", "rucc_code"]]

def merge_datasets():
    census = load_census()
    rucc = load_rucc()
    hpsa = load_hpsa()

    merged = census.merge(rucc, on="fips", how="left")

    hpsa_summary = hpsa.groupby(["state_clean", "county_clean"]).agg(
        hpsa_count=("HPSA ID", "count"),
        avg_hpsa_score=("HPSA Score", "mean")
    ).reset_index()

    merged = merged.merge(
        hpsa_summary,
        left_on=["state_full", "county_match"],
        right_on=["state_clean", "county_clean"],
        how="left"
    )

    merged["hpsa_count"] = merged["hpsa_count"].fillna(0)
    merged["avg_hpsa_score"] = merged["avg_hpsa_score"].fillna(0)

    return merged

if __name__ == "__main__":
    df = merge_datasets()
    print(f"Total counties: {len(df)}")
    print(f"Missing RUCC: {df['rucc_code'].isna().sum()}")
    print(f"Counties with zero shortage areas (hpsa_count == 0): {(df['hpsa_count'] == 0).sum()}")
    print(df.head(10))
    df.to_csv("data/processed/national_access_merged.csv", index=False)
    print(f"\nSaved to data/processed/national_access_merged.csv")