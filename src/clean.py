import pandas as pd

COUNTY_SUFFIXES = r"\s+(County|Parish|Borough|Census Area|Municipality)$"


def load_census():
    df = pd.read_csv("data/raw/census_county_national.csv")
    df = df.rename(columns={
        "B01003_001E": "population",
        "B19013_001E": "median_income",
        "S2701_C05_001E": "uninsured_pct",
    })
    for col in ["population", "median_income", "uninsured_pct"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Census reports suppressed values as large negative numbers; drop those counties
    df = df[(df["median_income"] > 0) & (df["uninsured_pct"] >= 0)].copy()

    df["fips"] = (
        df["state"].astype(str).str.zfill(2) + df["county"].astype(str).str.zfill(3)
    ).astype(int)
    df["county_name"] = df["NAME"].str.extract(r"^(.+?),", expand=False)
    df["state_full"] = df["NAME"].str.extract(r",\s*(.+)$", expand=False)
    # HPSA uses bare county names ("Ventura", not "Ventura County")
    df["county_match"] = df["county_name"].str.replace(COUNTY_SUFFIXES, "", regex=True)
    return df[["fips", "county_name", "county_match", "state_full",
               "population", "median_income", "uninsured_pct"]]


def load_hpsa():
    df = pd.read_csv("data/raw/hpsa_national.csv", low_memory=False)
    df = df[df["Discipline"] == "Primary Care"].copy()
    df["county_clean"] = df["County"].str.strip()
    df["state_clean"] = df["State"].str.strip()
    return df


def load_rucc():
    df = pd.read_csv("data/raw/rucc_national.csv")
    pivoted = df.pivot(index=["FIPS", "State", "County_Name"],
                       columns="Attribute", values="Value").reset_index()
    pivoted = pivoted.rename(columns={"FIPS": "fips", "RUCC_2023": "rucc_code"})
    pivoted["rucc_code"] = pd.to_numeric(pivoted["rucc_code"], errors="coerce")
    return pivoted[["fips", "rucc_code"]]


def merge_datasets():
    census = load_census()
    rucc = load_rucc()
    hpsa = load_hpsa()

    # Census + RUCC join cleanly on FIPS
    merged = census.merge(rucc, on="fips", how="left")

    # HPSA has no FIPS column, so match on state name + county name
    hpsa_summary = hpsa.groupby(["state_clean", "county_clean"]).agg(
        hpsa_count=("HPSA ID", "count"),
        avg_hpsa_score=("HPSA Score", "mean"),
    ).reset_index()

    merged = merged.merge(
        hpsa_summary,
        left_on=["state_full", "county_match"],
        right_on=["state_clean", "county_clean"],
        how="left",
    )
    merged["hpsa_count"] = merged["hpsa_count"].fillna(0)
    merged["avg_hpsa_score"] = merged["avg_hpsa_score"].fillna(0)

    # Drop join helper columns so they don't leak into the API/app
    return merged.drop(columns=["county_match", "state_clean", "county_clean"])


if __name__ == "__main__":
    df = merge_datasets()
    print(f"Total counties: {len(df)}")
    print(f"Missing RUCC: {df['rucc_code'].isna().sum()}")
    print(f"Counties with zero shortage areas: {(df['hpsa_count'] == 0).sum()}")
    print(f"Population-weighted uninsured rate: "
          f"{(df['uninsured_pct'] * df['population']).sum() / df['population'].sum():.1f}%")
    df.to_csv("data/processed/national_access_merged.csv", index=False)
    print("Saved to data/processed/national_access_merged.csv")
