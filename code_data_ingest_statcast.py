import pandas as pd
from pathlib import Path

def ingest_statcast(csv_2024: Path, csv_2025: Path, park_factors: Path) -> pd.DataFrame:
    """Load 2024/25 Statcast CSVs, append, merge park_factor column."""
    df_24 = pd.read_csv(csv_2024, parse_dates=['game_date'])
    df_25 = pd.read_csv(csv_2025, parse_dates=['game_date'])
    parks = pd.read_csv(park_factors)
    df = pd.concat([df_24, df_25], ignore_index=True)
    df = df.merge(parks, on='home_team', how='left')
    return df
