import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

MODEL_NAME = "gemini-3.6-flash"
_client = None


def get_client():
    """Create the Gemini client lazily so the app still loads if the key is missing."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=api_key)
    return _client


def generate_county_summary(county: dict) -> str:
    """Plain-language summary grounded strictly in the county's real data."""
    segment_line = ""
    if county.get("segment"):
        segment_line = f"Priority segment from this project's analysis: {county['segment']}\n"

    prompt = f"""You are a healthcare policy analyst. Using ONLY the data below, write a short
(3-4 sentence) plain-language summary of this county's primary care access situation.
Do not invent facts that are not in the data. If the data does not support a strong
conclusion, say so honestly.

County: {county['county_name']}, {county['state_full']}
Population: {int(county['population']):,}
Median household income: ${int(county['median_income']):,}
Uninsured rate (all ages): {float(county['uninsured_pct']):.1f}%
Rural-Urban Continuum Code (1 = large metro, 9 = most rural): {int(county['rucc_code'])}
Designated primary care Health Professional Shortage Areas: {int(county['hpsa_count'])}
Average shortage severity score (0-25, higher = more severe): {float(county['avg_hpsa_score']):.1f}
{segment_line}"""

    response = get_client().models.generate_content(model=MODEL_NAME, contents=prompt)
    return response.text


if __name__ == "__main__":
    test_county = {
        "county_name": "Washington County",
        "state_full": "Pennsylvania",
        "population": 209778,
        "median_income": 77487,
        "uninsured_pct": 4.5,
        "rucc_code": 1,
        "hpsa_count": 18,
        "avg_hpsa_score": 10.06,
        "segment": "Lower Priority",
    }
    print(generate_county_summary(test_county))
