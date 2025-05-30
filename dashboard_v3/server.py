import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path

class Edge(BaseModel):
    player: str
    edge: float
    spark: float

app = FastAPI()
CSV = Path(__file__).resolve().parents[1] / "data" / "slip_results.csv"

@app.get("/api/edges", response_model=list[Edge])
def get_edges():
    df = pd.read_csv(CSV)
    return [Edge(player=r.player, edge=r.edge, spark=r.spark)
            for r in df.itertuples()]
