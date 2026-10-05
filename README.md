# Quick Commerce Batching

Synthetic Chennai grocery orders → Random Forest prep-time predictions → OR-Tools VRP rider batches → FastAPI + Streamlit map.

## Local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python -m src.simulate_orders
python -m src.prep_time_model
python -m src.routing_engine
python tests/test_pipeline.py
```

API (terminal 1):

```bash
uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Map UI (terminal 2):

```bash
streamlit run streamlit_app.py
```

Leave the API URL as `http://127.0.0.1:8000`, then click **Run Batching**.

- `GET /health` — liveness
- `POST /batch?num_riders=5&sample_size=30` — rider assignments
- `GET /docs` — OpenAPI

## Deploy (Render)

The GitHub repo includes `render.yaml`. After push:

1. [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect `vsh0711/quickcommerce-batching`
3. Apply the blueprint (Python web service, `uvicorn src.api:app --host 0.0.0.0 --port $PORT`)

The public URL will look like `https://quickcommerce-batching.onrender.com`. Point Streamlit’s API URL at that host after the first deploy finishes.
