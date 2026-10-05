from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "generated"
ORDERS_CSV = DATA_DIR / "orders.csv"
MODEL_PATH = DATA_DIR / "prep_time_model.pkl"
