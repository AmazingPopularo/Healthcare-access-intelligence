README_TEXT = """
# Healthcare Access Intelligence

## Problem
Which counties in Pennsylvania have inadequate healthcare access,
and does that access gap correlate with worse health outcomes?

## Data sources
- HRSA HPSA Dashboard: provider shortage designations by county
- Census ACS 5-Year: population, median income, insurance coverage

## Key Finding
Analyzed all 67 Pennsylvania counties by joining Census ACS and HRSA HPSA
shortage data. Provider shortage severity showed weak correlation with
income (r=-0.07) and insurance coverage (r=-0.06) -- shortages appear
more geography/supply-driven than purely poverty-driven. 29 counties
(43%) show both below-median income AND active shortage designations,
including Philadelphia, challenging the assumption that shortages are
purely a rural phenomenon.

## Status
In progress -- Pennsylvania county-level analysis complete,
next: database layer + interactive UI
"""

if __name__ == "__main__":
    print(README_TEXT)