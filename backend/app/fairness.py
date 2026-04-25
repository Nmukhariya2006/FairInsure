# backend/app/fairness.py
from app.model import get_feature_importance

TIER_PROXY_STRENGTH = {
    "tier1": 0.05,
    "tier2": 0.18,
    "tier3": 0.42,
}

PROXY_THRESHOLD  = 0.25
REVIEW_THRESHOLD = 0.35

def audit_bias(application: dict, premium: float) -> dict:
    # Proxy strength: how much city_tier correlates with income inequality
    tier_proxy_map = {"tier1": 0.05, "tier2": 0.18, "tier3": 0.42}
    proxy_strength = tier_proxy_map.get(application.get("city_tier", "tier1"), 0.1)

    proxy_flag = proxy_strength > 0.25
    fairness_score = round(1.0 - proxy_strength, 2)
    needs_human_review = proxy_strength > 0.35

    adjusted_premium = premium
    if proxy_flag:
        # Reweight: reduce the proxy contribution, keep legit risk
        adjustment_factor = 1 - (proxy_strength * 0.5)
        adjusted_premium = round(premium * adjustment_factor, 2)

    savings = round(premium - adjusted_premium, 2)
    explanation = (
        f"Pincode (city_tier='{application['city_tier']}') contributes {round(proxy_strength*100)}% "
        f"as a poverty proxy. Fair adjustment removes this bias. "
        f"Premium reduced by ₹{savings} ({round((savings/premium)*100, 1)}%)."
        if proxy_flag else
        f"No significant proxy bias detected. Pincode contribution: {round(proxy_strength*100)}%. Premium stands."
    )

    return {
        "proxy_feature": "city_tier (pincode proxy)",
        "proxy_strength": proxy_strength,
        "fairness_score": fairness_score,
        "proxy_flag": proxy_flag,
        "adjusted_premium": adjusted_premium,
        "needs_human_review": needs_human_review,
        "explanation": explanation,}

    