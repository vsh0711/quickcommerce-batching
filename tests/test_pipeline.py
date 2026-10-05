import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.paths import ORDERS_CSV
from src.routing_engine import solve_routes
from src.simulate_orders import generate_orders, is_on_land


def test_generate_orders_stays_on_land():
    df = generate_orders(n_orders=40, seed=7)
    assert len(df) == 40
    assert df["distance_km"].between(2, 6).all()
    on_land = df.apply(lambda r: is_on_land(r.delivery_lat, r.delivery_lng), axis=1)
    assert on_land.all(), df.loc[~on_land, ["delivery_lat", "delivery_lng", "store_name"]]


def test_vrp_assigns_every_sampled_order():
    df = pd.read_csv(ORDERS_CSV)
    sample = df.sample(12, random_state=0)
    routes = solve_routes(sample, num_riders=3, rider_capacity=8, time_limit_seconds=3)
    assert routes, "expected a feasible VRP solution"
    assigned = {oid for orders in routes.values() for oid in orders}
    assert assigned == set(sample["order_id"].astype(int))


if __name__ == "__main__":
    test_generate_orders_stays_on_land()
    test_vrp_assigns_every_sampled_order()
    print("pipeline tests passed")
