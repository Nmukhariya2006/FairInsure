# backend/app/model.py
import joblib
import pandas as pd

model = joblib.load("artifacts/premium_model.pkl")
features = joblib.load("artifacts/features.pkl")

def predict_premium(data: dict) -> float:
    df = pd.DataFrame([data])
    df = pd.get_dummies(df, columns=["city_tier"])
    for col in features:
        if col not in df.columns:
            df[col] = 0
    df = df[features]
    return float(round(model.predict(df)[0], 2))

def get_feature_importance(data: dict) -> dict:
    import shap
    df = pd.DataFrame([data])
    df = pd.get_dummies(df, columns=["city_tier"])
    for col in features:
        if col not in df.columns:
            df[col] = 0
    df = df[features]
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(df)
    return dict(zip(features, [round(float(v), 4) for v in shap_values[0]]))