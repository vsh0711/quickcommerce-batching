# ML regression predicting pick-pack time from order features.
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib

from src.paths import ORDERS_CSV, MODEL_PATH

FEATURES = ["item_count", "hour", "store_load", "distance_km"]
TARGET = "pick_pack_time_min"


def train():
    df = pd.read_csv(ORDERS_CSV)
    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"MAE: {mae:.2f} min")
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    return model


if __name__ == "__main__":
    train()
