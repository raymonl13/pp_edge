from pathlib import Path
from code_data_ingest_statcast import ingest_statcast
def test_ingest_shape():
    root = Path('data/raw')
    df = ingest_statcast(root/'statcast_2024.csv', root/'statcast_2025.csv', Path('park_factors.csv'))
    assert len(df) > 0
