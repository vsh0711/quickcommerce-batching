# Synthetic orders with locations, timestamps, item counts, and pick n pack time
import numpy as np
import pandas as pd
from datetime import datetime

from src.paths import ORDERS_CSV

CHENNAI_STORES = [
   ("More Supermarket, T Nagar", 13.0418, 80.2341),
    ("Nilgiris, Nungambakkam", 13.0604, 80.2496),
    ("Spencer's, Guindy", 13.0067, 80.2206),
    ("Reliance Fresh, Royapettah", 13.0524, 80.2593),
    ("Star Bazaar, Anna Nagar", 13.0850, 80.2101),
    ("D-Mart, Sholinganallur OMR", 12.9010, 80.2279),
    ("Nilgiris, Alwarpet", 13.0338, 80.2547),
    ("More Supermarket, Velachery", 12.9791, 80.2181),
    ("Spencer's, Egmore", 13.0779, 80.2578),
    ("D-Mart, Siruseri OMR", 12.8290, 80.2245),
    ("Reliance Smart, Porur", 13.0359, 80.1567),
    ("Nilgiris, Adyar", 13.0067, 80.2570),
    ("Star Bazaar, Chetpet", 13.0692, 80.2410),
    ("More Supermarket, Tambaram", 12.9249, 80.1000),
]
def offset_point(lat, lng, distance_km, bearing_deg):
    """Move (lat,lng) by distance_km along bearing_deg (0=N,90=E)."""
    R = 6371.0
    brng = np.radians(bearing_deg)
    lat1, lng1 = np.radians(lat), np.radians(lng)
    lat2 = np.arcsin(np.sin(lat1)*np.cos(distance_km/R) +
                      np.cos(lat1)*np.sin(distance_km/R)*np.cos(brng))
    lng2 = lng1 + np.arctan2(
        np.sin(brng)*np.sin(distance_km/R)*np.cos(lat1),
        np.cos(distance_km/R) - np.sin(lat1)*np.sin(lat2)
    )
    return np.degrees(lat2), np.degrees(lng2)
CHENNAI_BOUNDS = {"lat_min": 12.80, "lat_max": 13.15, "lng_min": 79.95, "lng_max": 80.30}

def offset_point_bounded(lat, lng, min_km=10, max_km=20, bounds=CHENNAI_BOUNDS, rng=None, max_tries=50):
    for _ in range(max_tries):
        dist_km = rng.uniform(min_km, max_km)
        bearing = rng.uniform(0, 360)
        dlat, dlng = offset_point(lat, lng, dist_km, bearing)
        if bounds["lat_min"] <= dlat <= bounds["lat_max"] and bounds["lng_min"] <= dlng <= bounds["lng_max"]:
            return dlat, dlng, dist_km
    # fallback: shrink distance range and force a valid point
    return offset_point(lat, lng, min_km, 225) + (min_km,) # SW bearing, safely inland

def generate_orders(n_orders=150, seed=42):
    rng = np.random.default_rng(seed)

    store_idx = rng.integers(0, len(CHENNAI_STORES), size=n_orders)
    item_count = rng.integers(1, 15, size=n_orders)
    hour = rng.integers(8, 23, size=n_orders)
    store_load = rng.integers(1, 50, size=n_orders)

    rows = []
    for i in range(n_orders):
        name, slat, slng = CHENNAI_STORES[store_idx[i]]
        dlat, dlng, dist_km = offset_point_bounded(slat, slng, rng=rng)

        base_time = 3 + 0.8*item_count[i] + 0.15*store_load[i]
        prep_time = max(2, base_time + rng.normal(0, 1.5))

        rows.append({
            "order_id": i+1,
            "store_name": name,
            "store_lat": slat, "store_lng": slng,
            "delivery_lat": dlat, "delivery_lng": dlng,
            "distance_km": dist_km,
            "item_count": item_count[i],
            "hour": hour[i],
            "store_load": store_load[i],
            "timestamp": datetime(2026, 8, 27, hour[i], int(rng.integers(0,60))),
            "pick_pack_time_min": round(prep_time, 2),
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = generate_orders()
    ORDERS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ORDERS_CSV, index=False)
    print(df.head())
    print(f"\nGenerated {len(df)} orders, min dist={df.distance_km.min():.1f}km, max={df.distance_km.max():.1f}km")
