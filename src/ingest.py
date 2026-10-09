import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
ACS_YEAR = "2023"


def census_get(url, variables):
    """Call the Census API for every U.S. county and return a DataFrame."""
    params = {"get": variables, "for": "county:*", "in": "state:*", "key": CENSUS_API_KEY}
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    rows = response.json()
    return pd.DataFrame(rows[1:], columns=rows[0])


def fetch_census_data():
    """
    Population and median household income come from the ACS detail tables.
    Percent uninsured (all ages) comes from subject table S2701.
    An earlier version used B27010_017E, which only counts uninsured people
    under 19 and badly understated uninsured rates.
    """
    # B01003_001E = total population, B19013_001E = median household income
    base = census_get(
        f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5",
        "NAME,B01003_001E,B19013_001E",
    )
    # S2701_C05_001E = percent uninsured, civilian noninstitutionalized population
    uninsured = census_get(
        f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5/subject",
        "S2701_C05_001E",
    )
    return base.merge(uninsured, on=["state", "county"], how="left")


def fetch_hpsa_data():
    """Health Professional Shortage Area (HPSA) designations, nationwide."""
    url = "https://data.hrsa.gov/DataDownload/DD_Files/HPSA_DASHBOARD.csv"
    return pd.read_csv(url, low_memory=False)


def fetch_rucc_data():
    """USDA Rural-Urban Continuum Codes (2023), nationwide."""
    url = "https://www.ers.usda.gov/media/5768/2023-rural-urban-continuum-codes.csv?v=68442"
    return pd.read_csv(url, encoding="latin1")


if __name__ == "__main__":
    census_df = fetch_census_data()
    census_df.to_csv("data/raw/census_county_national.csv", index=False)
    print(f"Saved {len(census_df)} counties to data/raw/census_county_national.csv")

    hpsa_df = fetch_hpsa_data()
    hpsa_df.to_csv("data/raw/hpsa_national.csv", index=False)
    print(f"Saved {len(hpsa_df)} HPSA records to data/raw/hpsa_national.csv")

    rucc_df = fetch_rucc_data()
    rucc_df.to_csv("data/raw/rucc_national.csv", index=False)
    print(f"Saved {len(rucc_df)} RUCC records to data/raw/rucc_national.csv")
