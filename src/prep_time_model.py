# ML regression predicting pick-pack time from order features.
# Why: routing engine needs a realistic time-cost per order; can't just use the synthetic formula directly (that'd be cheating) - train a model on 
# the generated data so the pipeline mirrors a real ML→OR handoff.
# src/prep_time_model.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib

FEATURES = ["item_count", "hour", "store_load", "distance_km"]
TARGET = "pick_pack_time_min"  # rename column if you relabeled it to pick_pack_time_min

def train():
    df = pd.read_csv("data/generated/orders.csv")
    X, y = df[FEATURES], df[TARGET]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"MAE: {mae:.2f} min")

    joblib.dump(model, "data/generated/prep_time_model.pkl")
    return model

if __name__ == "__main__":
    train()