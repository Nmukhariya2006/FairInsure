# backend/app/agent/nodes.py
from app.model import predict_premium, get_feature_importance
from app.fairness import audit_bias
from app.db import SessionLocal, Application, FairnessAudit


def intake_node(state: dict) -> dict:
    db = SessionLocal()
    try:
        db_app = Application(**state["application"])
        db.add(db_app)
        db.commit()
        db.refresh(db_app)
        return {**state, "application_id": db_app.id}
    finally:
        db.close()


def risk_node(state: dict) -> dict:
    premium = predict_premium(state["application"])
    importance = get_feature_importance(state["application"])

    return {
        **state,
        "original_premium": premium,
        "feature_importance": importance,
    }


def audit_node(state: dict) -> dict:
    result = audit_bias(state["application"], state["original_premium"])
    return {**state, "audit_result": result}


def compliance_node(state: dict) -> dict:
    db = SessionLocal()

    try:
        audit = state.get("audit_result") or {}

        record = FairnessAudit(
            application_id=state["application_id"],
            original_premium=state["original_premium"],
            adjusted_premium=audit.get("adjusted_premium"),
            proxy_feature=audit.get("proxy_feature"),
            proxy_strength=audit.get("proxy_strength"),
            fairness_score=audit.get("fairness_score"),
            proxy_flag=audit.get("proxy_flag"),
            explanation=audit.get("explanation"),
            needs_human_review=audit.get("needs_human_review", False),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return {
            **state,
            "final_decision": {
                "application_id": state["application_id"],
                "original_premium": state["original_premium"],
                "adjusted_premium": audit.get("adjusted_premium"),
                "fairness_score": audit.get("fairness_score"),
                "proxy_flag": audit.get("proxy_flag"),
                "proxy_strength": audit.get("proxy_strength"),   # ✅ added
                "proxy_feature": audit.get("proxy_feature"),     # ✅ added
                "explanation": audit.get("explanation"),
                "needs_human_review": audit.get("needs_human_review", False),
                "status": (
                    "IRDAI_COMPLIANT"
                    if not audit.get("proxy_flag")
                    else "ADJUSTED_FOR_FAIRNESS"
                ),

                # ✅ IMPORTANT for frontend chart
                "shap_breakdown": state.get("feature_importance", {}),
            },
        }

    finally:
        db.close()


def human_review_node(state: dict) -> dict:
    print(
        f"[HUMAN REVIEW REQUIRED] Application {state['application_id']} "
        f"has proxy_strength > 0.35"
    )

    audit = state.get("audit_result", {})
    audit["human_review_flagged"] = True

    return {**state, "audit_result": audit}