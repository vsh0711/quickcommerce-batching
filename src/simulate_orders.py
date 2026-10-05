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

# East of this polyline is the Bay of Bengal. Keep a ~1km inland buffer.
_COAST_LAT = np.array([12.80, 12.85, 12.90, 12.95, 13.00, 13.04, 13.08, 13.12, 13.16])
_COAST_LNG = np.array([80.245, 80.242, 80.238, 80.255, 80.273, 80.288, 80.295, 80.302, 80.305])
LAND_BUFFER_DEG = 0.01  # ~1.1 km


def coast_lng(lat):
    return float(np.interp(lat, _COAST_LAT, _COAST_LNG))


def is_on_land(lat, lng):
    if not (12.82 <= lat <= 13.15 and 80.09 <= lng <= 80.29):
        return False
    return lng < coast_lng(lat) - LAND_BUFFER_DEG


def offset_point(lat, lng, distance_km, bearing_deg):
    """Move (lat,lng) by distance_km along bearing_deg (0=N,90=E)."""
    R = 6371.0
    brng = np.radians(bearing_deg)
    lat1, lng1 = np.radians(lat), np.radians(lng)
    lat2 = np.arcsin(
        np.sin(lat1) * np.cos(distance_km / R)
        + np.cos(lat1) * np.sin(distance_km / R) * np.cos(brng)
    )
    lng2 = lng1 + np.arctan2(
        np.sin(brng) * np.sin(distance_km / R) * np.cos(lat1),
        np.cos(distance_km / R) - np.sin(lat1) * np.sin(lat2),
    )
    return float(np.degrees(lat2)), float(np.degrees(lng2))


def offset_point_on_land(lat, lng, min_km=2, max_km=6, rng=None, max_tries=80):
    """Drop deliveries on land only. Coastal stores bias west so pins stay off the sea."""
    eastish = lng >= 80.22
    for _ in range(max_tries):
        dist_km = rng.uniform(min_km, max_km)
        if eastish:
            bearing = rng.uniform(180, 360)  # S/W/N, not out to sea
        else:
            bearing = rng.uniform(0, 360)
        dlat, dlng = offset_point(lat, lng, dist_km, bearing)
        if is_on_land(dlat, dlng):
            return dlat, dlng, dist_km
    dlat, dlng = offset_point(lat, lng, min_km, 270)
    if not is_on_land(dlat, dlng):
        dlat, dlng = offset_point(lat, lng, min_km, 225)
    return dlat, dlng, min_km


def generate_orders(n_orders=150, seed=42):
    rng = np.random.default_rng(seed)

    store_idx = rng.integers(0, len(CHENNAI_STORES), size=n_orders)
    item_count = rng.integers(1, 15, size=n_orders)
    hour = rng.integers(8, 23, size=n_orders)
    store_load = rng.integers(1, 50, size=n_orders)

    rows = []
    for i in range(n_orders):
        name, slat, slng = CHENNAI_STORES[store_idx[i]]
        dlat, dlng, dist_km = offset_point_on_land(slat, slng, rng=rng)

        base_time = 3 + 0.8 * item_count[i] + 0.15 * store_load[i]
        prep_time = max(2, base_time + rng.normal(0, 1.5))

        rows.append({
            "order_id": i + 1,
            "store_name": name,
            "store_lat": slat,
            "store_lng": slng,
            "delivery_lat": dlat,
            "delivery_lng": dlng,
            "distance_km": dist_km,
            "item_count": item_count[i],
            "hour": hour[i],
            "store_load": store_load[i],
            "timestamp": datetime(2026, 8, 27, hour[i], int(rng.integers(0, 60))),
            "pick_pack_time_min": round(prep_time, 2),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_orders()
    ORDERS_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ORDERS_CSV, index=False)
    print(df.head())
    off_land = (~df.apply(lambda r: is_on_land(r.delivery_lat, r.delivery_lng), axis=1)).sum()
    print(
        f"\nGenerated {len(df)} orders, min dist={df.distance_km.min():.1f}km, "
        f"max={df.distance_km.max():.1f}km, off_land={off_land}"
    )
