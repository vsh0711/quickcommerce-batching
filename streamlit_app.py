import os

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

from src.paths import ORDERS_CSV

st.title("Quick Commerce Batching & Routing")

default_api = os.environ.get("API_URL", "http://127.0.0.1:8000")
API_URL = st.text_input("API URL", default_api).rstrip("/")
num_riders = st.slider("Number of riders", 2, 10, 5)
sample_size = st.slider("Sample orders", 10, 100, 30)

if st.button("Run Batching"):
    resp = None
    try:
        resp = requests.post(
            f"{API_URL}/batch",
            params={"num_riders": num_riders, "sample_size": sample_size},
            timeout=60,
        )
        resp.raise_for_status()
        payload = resp.json()
    except requests.RequestException as exc:
        st.error(f"API request failed: {exc}")
        if resp is not None:
            st.write("Status:", resp.status_code)
            st.write("Body:", resp.text)
        st.stop()

    routes = payload.get("routes") or {}
    if not routes:
        st.warning("API returned no routes.")
        st.stop()

    df = pd.read_csv(ORDERS_CSV)
    colors = [
        [255, 0, 0], [0, 255, 0], [0, 0, 255], [255, 165, 0], [128, 0, 128],
        [0, 255, 255], [255, 0, 255], [128, 128, 0], [0, 128, 128], [255, 255, 0],
    ]

    layers = []
    for i, (rider, order_ids) in enumerate(routes.items()):
        rider_df = df[df.order_id.isin(order_ids)]
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=rider_df,
                get_position="[delivery_lng, delivery_lat]",
                get_color=colors[i % len(colors)],
                get_radius=200,
            )
        )
        st.write(f"**{rider}**: {len(order_ids)} orders")

    st.pydeck_chart(
        pdk.Deck(
            layers=layers,
            initial_view_state=pdk.ViewState(latitude=13.05, longitude=80.22, zoom=9.5),
        )
    )
