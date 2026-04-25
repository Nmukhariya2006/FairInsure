import pandas as pd
import numpy as np

np.random.seed(42)  # makes results reproducible every run
n = 2000            # number of fake applicants

# --- Step 1: Pick city tier for each person ---
# 30% metro, 40% city, 30% rural — realistic India distribution
city_tiers = np.random.choice(
    ["tier1", "tier2", "tier3"],
    n,
    p=[0.3, 0.4, 0.3]
)

# --- Step 2: Generate each column ---
ages = np.random.randint(22, 65, n)

bmis = np.round(np.random.normal(26, 4, n), 1)
bmis = np.clip(bmis, 15, 45)  # no impossible values

# Income tied to city (realistic — urban earns more)
income_base = {"tier1": 900000, "tier2": 520000, "tier3": 240000}
annual_incomes = np.array([
    income_base[t] + np.random.randint(-80000, 80000)
    for t in city_tiers
])

# Past claims: most people have 0, few have many
past_claims = np.random.choice([0, 1, 2, 3, 4], n, p=[0.55, 0.25, 0.12, 0.05, 0.03])

coverage_amounts = np.random.choice([300000, 500000, 750000, 1000000], n)

smokers = np.random.choice([0, 1], n, p=[0.78, 0.22])

# Occupations — linked to city tier for realism
occ_map = {
    "tier1": ["salaried", "business", "professional"],
    "tier2": ["salaried", "business", "shopkeeper"],
    "tier3": ["farmer", "laborer", "shopkeeper"]
}
occupations = [
    np.random.choice(occ_map[t]) for t in city_tiers
]

# --- Step 3: Calculate BIASED premium ---
# This is the unfair formula — city_tier has way too much influence
tier_bias = {"tier1": 0.90, "tier2": 1.10, "tier3": 1.38}  # rural pays 38% more

# Add to generate_data.py
conditions = np.random.choice(
    ["none", "diabetes", "hypertension", "heart_disease"],
    n, p=[0.60, 0.20, 0.15, 0.05]
)
# Add "conditions" to the DataFrame and the premium formula
premiums = (
    ages * 420                              # age is legitimate risk
    + bmis * 280                            # BMI is legitimate
    + past_claims * 2800                    # claims history is legitimate
    + smokers * 9000                        # smoking is legitimate
    + coverage_amounts * 0.018              # coverage amount is legitimate
    + np.array([tier_bias[t] * 6000 for t in city_tiers])  # ← THIS IS THE BIAS
    + np.random.normal(0, 1200, n)          # random noise (real world variation)
).round(0)

# --- Step 4: Build DataFrame and save ---
df = pd.DataFrame({
    "age": ages,
    "bmi": bmis,
    "city_tier": city_tiers,
    "annual_income": annual_incomes,
    "past_claims": past_claims,
    "coverage_amount": coverage_amounts,
    "smoker": smokers,
    "occupation": occupations,
    "premium": premiums,
})

df.to_csv("backend/ml/insurance_data.csv", index=False)

# --- Step 5: Print a summary so you can verify it worked ---
print(f"Dataset created: {len(df)} rows")
print("\nAverage premium by city tier (shows the bias):")
print(df.groupby("city_tier")["premium"].mean().round(0))
print("\nSample rows:")
print(df.head(3).to_string())