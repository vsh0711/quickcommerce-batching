# OR-Tools VRP, using the trained model's predicted times as part of the cost matrix.
import math
import pandas as pd
import numpy as np
import joblib
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from src.paths import MODEL_PATH, ORDERS_CSV

FEATURES = ["item_count", "hour", "store_load", "distance_km"]


def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(np.radians, [lat1, lng1, lat2, lng2])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def build_time_matrix(df, avg_speed_kmph=25):
    """Time (min) between depot (index 0) and every delivery point.

    Depot is the mean of the stores in this batch so no real order is used as a
    dummy start node (which previously dropped one order from every solution).
    """
    depot = np.array(
        [[df["store_lat"].mean(), df["store_lng"].mean()]],
        dtype=float,
    )
    deliveries = df[["delivery_lat", "delivery_lng"]].to_numpy(dtype=float)
    points = np.vstack([depot, deliveries])
    n = len(points)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist = haversine_km(points[i][0], points[i][1], points[j][0], points[j][1])
                matrix[i][j] = (dist / avg_speed_kmph) * 60
    return matrix


def solve_routes(df, num_riders=5, rider_capacity=8, time_limit_seconds=3):
    if df.empty:
        return {}

    model = joblib.load(MODEL_PATH)
    df = df.reset_index(drop=True)
    df["pred_prep_time"] = model.predict(df[FEATURES])

    n_orders = len(df)
    min_riders = max(1, math.ceil(n_orders / rider_capacity))
    num_riders = max(int(num_riders), min_riders)

    time_matrix = build_time_matrix(df)
    n_nodes = n_orders + 1  # depot + deliveries
    prep = [0.0] + df["pred_prep_time"].tolist()

    manager = pywrapcp.RoutingIndexManager(n_nodes, num_riders, 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(time_matrix[from_node][to_node] + prep[to_node])

    transit_idx = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    routing.AddDimension(transit_idx, 0, 300, True, "Time")

    def demand_callback(idx):
        node = manager.IndexToNode(idx)
        return 0 if node == 0 else 1

    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [rider_capacity] * num_riders, True, "Capacity"
    )

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.seconds = time_limit_seconds

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        return None

    assigned = []
    for rider in range(num_riders):
        idx = routing.Start(rider)
        route = []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node != 0:
                route.append(int(df.loc[node - 1, "order_id"]))
            idx = solution.Value(routing.NextVar(idx))
        if route:
            assigned.append(route)
    return {f"rider_{i}": route for i, route in enumerate(assigned)}


if __name__ == "__main__":
    df = pd.read_csv(ORDERS_CSV)
    sample = df.sample(30, random_state=42)
    routes = solve_routes(sample, num_riders=5)
    if not routes:
        print("No solution found")
    else:
        assigned = sum(len(v) for v in routes.values())
        print(f"assigned {assigned}/{len(sample)} orders")
        for rider, orders in routes.items():
            print(rider, "->", orders)
