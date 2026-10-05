from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from src.paths import ORDERS_CSV
from src.routing_engine import solve_routes

app = FastAPI(title="Quick Commerce Batching Engine")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok"}


@app.get("/health")
def health_alias():
    return {"status": "ok"}


@app.post("/batch")
def batch_orders(
    num_riders: int = Query(5, ge=1, le=20),
    sample_size: int = Query(30, ge=1, le=150),
):
    if not ORDERS_CSV.exists():
        raise HTTPException(status_code=500, detail="orders.csv is missing. Generate data first.")

    df = pd.read_csv(ORDERS_CSV)
    if df.empty:
        raise HTTPException(status_code=500, detail="orders.csv is empty.")

    sample_size = min(sample_size, len(df))
    sample = df.sample(sample_size, random_state=42)
    routes = solve_routes(sample, num_riders=num_riders)
    if routes is None:
        raise HTTPException(
            status_code=422,
            detail="No feasible rider assignment for this sample. Try more riders or a smaller sample.",
        )
    return {"routes": routes, "sample_size": sample_size, "num_riders": len(routes)}
