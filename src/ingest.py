import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")

def fetch_census_data():
    """Pull population, income, and insurance coverage by county, nationwide."""
    url = "https://api.census.gov/data/2023/acs/acs5"
    params = {
        "get": "NAME,B01003_001E,B19013_001E,B27010_017E",
        # B01003_001E = total population
        # B19013_001E = median household income
        # B27010_017E = no health insurance coverage (rough proxy)
        "for": "county:*",
        "in": "state:*",
        "key": CENSUS_API_KEY,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def fetch_hpsa_data():
    """Pull Health Professional Shortage Area (HPSA) designations, nationwide."""
    url = "https://data.hrsa.gov/DataDownload/DD_Files/HPSA_DASHBOARD.csv"
    df = pd.read_csv(url, low_memory=False)
    return df

def fetch_rucc_data():
    """Pull USDA Rural-Urban Continuum Codes by county, nationwide."""
    url = "https://www.ers.usda.gov/media/5768/2023-rural-urban-continuum-codes.csv?v=68442"
    df = pd.read_csv(url, encoding="latin1")
    return df

if __name__ == "__main__":
    census_df = fetch_census_data()
    print(census_df.head())
    census_df.to_csv("data/raw/census_county_national.csv", index=False)
    print(f"Saved {len(census_df)} counties to data/raw/census_county_national.csv\n")

    hpsa_df = fetch_hpsa_data()
    print(hpsa_df.head())
    hpsa_df.to_csv("data/raw/hpsa_national.csv", index=False)
    print(f"\nSaved {len(hpsa_df)} HPSA records to data/raw/hpsa_national.csv\n")

    rucc_df = fetch_rucc_data()
    print(rucc_df.head())
    rucc_df.to_csv("data/raw/rucc_national.csv", index=False)
    print(f"\nSaved {len(rucc_df)} RUCC records to data/raw/rucc_national.csv")