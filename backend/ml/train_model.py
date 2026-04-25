import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error,r2_score
from xgboost import XGBRegressor
import os

# load the data
df=pd.read_csv("insurance_data.csv")
print(f"loaded{len(df)} rows")

df_encoded = pd.get_dummies(df, columns=["city_tier", "occupation"])
#seperate the input(X)  and  output(y)
X=df_encoded.drop("premium", axis=1)
y=df_encoded["premium"]

#train test split
X_train,X_test,y_train,y_test=train_test_split(
    X,y,test_size=0.2,random_state=42
)

print(f"training on {len(X_train)} rows, testing on {len(X_test)} rows")

# --- Train XGBoost ---
model = XGBRegressor(
    n_estimators=300,
    max_depth=5,
    learning_rate=0.08,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1  # use all CPU cores
)
model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=50)

# evaluation
#X_test(predection data),y_test(actual data)
predection=model.predict(X_test)
mae=mean_absolute_error(y_test,predection)
r2=r2_score(y_test,predection)
print(f"\nModel evaluation:")
print(f"  MAE  = ₹{mae:.0f}  (average prediction error)")
print(f"  R²   = {r2:.3f}   (1.0 = perfect, >0.85 is good)")

#----Save artifacts-----
os.makedirs("artifacts", exist_ok=True)
joblib.dump(model, "artifacts/premium_model.pkl")
joblib.dump(list(X.columns), "artifacts/features.pkl")

print(f"Saved model with {len(X.columns)} features:")
print(list(X.columns))

