# OR-Tools VRP, using the trained model's predicted times as part of the cost matrix.
# Why: real routing optimizes total time = travel time + prep/pick-pack time. We predict prep time per order (done), now need travel time between all points (distance matrix) 
# and a VRP solver to assign orders to riders minimizing total route time under capacity/time-window constraints.
# src/routing_engine.py
import pandas as pd
import numpy as np
import joblib
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

FEATURES = ["item_count", "hour", "store_load", "distance_km"]

def haversine_km(lat1, lng1, lat2, lng2):
    R = 6371.0
    lat1, lng1, lat2, lng2 = map(np.radians, [lat1, lng1, lat2, lng2])
    dlat, dlng = lat2 - lat1, lng2 - lng1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlng/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def build_time_matrix(df, avg_speed_kmph=25):
    """Time (min) between every pair of delivery points, plus a depot at index 0 (store)."""
    points = df[["delivery_lat", "delivery_lng"]].values
    n = len(points)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                dist = haversine_km(points[i][0], points[i][1], points[j][0], points[j][1])
                matrix[i][j] = (dist / avg_speed_kmph) * 60  # minutes
    return matrix

def solve_routes(df, num_riders=5, rider_capacity=8):
    model = joblib.load("data/generated/prep_time_model.pkl")
    df = df.reset_index(drop=True)
    df["pred_prep_time"] = model.predict(df[FEATURES])

    time_matrix = build_time_matrix(df)
    n = len(df)

    manager = pywrapcp.RoutingIndexManager(n, num_riders, 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(time_matrix[from_node][to_node] + df.loc[to_node, "pred_prep_time"])

    transit_idx = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    routing.AddDimension(transit_idx, 0, 300, True, "Time")  # 300 min max route time
    demand_idx = routing.RegisterUnaryTransitCallback(lambda idx: 1)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [rider_capacity] * num_riders, True, "Capacity"
    )

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 15

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        print("No solution found")
        return None

    routes = {}
    for rider in range(num_riders):
        idx = routing.Start(rider)
        route = []
        while not routing.IsEnd(idx):
            node = manager.IndexToNode(idx)
            if node != 0:
                route.append(int(df.loc[node, "order_id"]))
            idx = solution.Value(routing.NextVar(idx))
        routes[f"rider_{rider}"] = route
    return routes

if __name__ == "__main__":
    df = pd.read_csv("data/generated/orders.csv")
    sample = df.sample(30, random_state=42)  # start small — full VRP on 150 pts is slow to eyeball
    routes = solve_routes(sample, num_riders=5)
    for rider, orders in routes.items():
        print(rider, "->", orders)