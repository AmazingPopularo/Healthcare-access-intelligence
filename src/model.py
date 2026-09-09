import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"))

def load_data():
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM county_access_national"), conn)
    df["uninsured_rate"] = df["uninsured_est"] / df["population"] * 100
    return df

def build_model():
    df = load_data()
    df = df.dropna(subset=["rucc_code"])

    median_score = df[df["avg_hpsa_score"] > 0]["avg_hpsa_score"].median()
    df["high_risk"] = (df["avg_hpsa_score"] > median_score).astype(int)

    features = ["population", "median_income", "uninsured_rate", "rucc_code"]
    X = df[features]
    y = df["high_risk"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)

    # Scale features so no single variable dominates due to its raw magnitude
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(class_weight="balanced", max_iter=1000)
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    print(f"Total counties used: {len(df)}")
    print("\n=== Classification Report ===")
    print(classification_report(y_test, y_pred))

    print("=== Feature coefficients (standardized scale, higher = stronger predictor) ===")
    for feature, coef in zip(features, model.coef_[0]):
        print(f"{feature}: {coef:.4f}")

    return model, features, scaler

if __name__ == "__main__":
    build_model()