# backend/app/agent/tools.py
import requests
import os
from typing import Any

# Base URL of your own FastAPI backend
# Tools call the backend endpoints — clean separation
BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def predict_premium_tool(application_data: dict) -> dict:
    """
    Tool: calls /predict endpoint.
    Returns the raw premium prediction from XGBoost.
    Called by the Risk Agent node.
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/predict",
            json=application_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Prediction service timed out"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Prediction failed: {str(e)}"}


def audit_bias_tool(application_data: dict) -> dict:
    """
    Tool: calls /audit-bias endpoint.
    Returns SHAP values + fairness score + adjusted premium.
    Called by the Bias Audit Agent node.
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/audit-bias",
            json=application_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        return {"error": "Audit service timed out"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Audit failed: {str(e)}"}


def save_audit_report_tool(
    application_id: int,
    audit_result: dict
) -> dict:
    """
    Tool: calls /save-report endpoint.
    Saves the final audit result to PostgreSQL.
    Called by the Compliance Agent node.
    """
    try:
        payload = {
            "application_id": application_id,
            **audit_result
        }
        response = requests.post(
            f"{BASE_URL}/api/save-report",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Save failed: {str(e)}"}


def get_feature_importance_tool(
    application_data: dict
) -> dict:
    """
    Tool: calls /feature-importance endpoint.
    Returns SHAP breakdown for dashboard bar chart.
    """
    try:
        response = requests.post(
            f"{BASE_URL}/api/feature-importance",
            json=application_data,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"SHAP failed: {str(e)}"}


def flag_human_review_tool(
    application_id: int,
    reason: str,
    proxy_strength: float
) -> dict:
    """
    Tool: flags a case for human review.
    In production: sends Slack webhook or email.
    For hackathon: logs to DB + prints alert.
    """
    try:
        payload = {
            "application_id": application_id,
            "reason":         reason,
            "proxy_strength": proxy_strength,
        }
        response = requests.post(
            f"{BASE_URL}/api/flag-review",
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Non-critical — don't crash the whole pipeline
        print(f"[WARN] Human review flag failed: {e}")
        return {"flagged": False, "error": str(e)}
