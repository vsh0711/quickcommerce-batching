# src/api.py
from fastapi import FastAPI
import pandas as pd
from src.routing_engine import solve_routes

app = FastAPI(title="Quick Commerce Batching Engine")

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/batch")
def batch_orders(num_riders: int = 5, sample_size: int = 30):
    df = pd.read_csv("data/generated/orders.csv")
    sample = df.sample(sample_size, random_state=42)
    routes = solve_routes(sample, num_riders=num_riders)
    return {"routes": routes}