import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
STATE_FIPS = "42"  # Pennsylvania. Full list: https://www.census.gov/library/reference/code-lists/ansi.html

def fetch_census_data():
    """Pull population, income, and insurance coverage by county from Census ACS 5-Year data."""
    url = "https://api.census.gov/data/2023/acs/acs5"
    params = {
        "get": "NAME,B01003_001E,B19013_001E,B27010_017E",
        # B01003_001E = total population
        # B19013_001E = median household income
        # B27010_017E = no health insurance coverage (rough proxy, we'll refine later)
        "for": "county:*",
        "in": f"state:{STATE_FIPS}",
        "key": CENSUS_API_KEY,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def fetch_hpsa_data():
    """Pull Health Professional Shortage Area (HPSA) designations, filtered to Pennsylvania."""
    url = "https://data.hrsa.gov/DataDownload/DD_Files/HPSA_DASHBOARD.csv"
    df = pd.read_csv(url, low_memory=False)
    df = df[df["State"] == "Pennsylvania"]
    return df

if __name__ == "__main__":
    census_df = fetch_census_data()
    print(census_df.head())
    census_df.to_csv("data/raw/pa_census_county.csv", index=False)
    print(f"Saved {len(census_df)} counties to data/raw/pa_census_county.csv\n")

    hpsa_df = fetch_hpsa_data()
    print(hpsa_df.head())
    hpsa_df.to_csv("data/raw/hpsa_national.csv", index=False)
    print(f"\nSaved {len(hpsa_df)} HPSA records to data/raw/hpsa_national.csv")