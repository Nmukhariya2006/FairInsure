from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func                        # ← add this

from app.schemas import ApplicationInput
from app.agent.graph import agent_graph
from app.db import get_db, FairnessAudit           # ← fix this

router = APIRouter()


@router.post("/audit")
async def run_full_audit(payload: ApplicationInput):
    initial_state = {
        "application": payload.dict(),
        "application_id": None,
        "original_premium": None,
        "feature_importance": None,
        "audit_result": None,
        "final_decision": None,
        "error": None,
    }

    result = agent_graph.invoke(initial_state)
    return result["final_decision"]


@router.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):

    def run_retrain():
        import subprocess
        subprocess.run(
            ["python", "ml/train_model.py"],
            capture_output=True
        )
        print("[INFO] Retraining complete")

    background_tasks.add_task(run_retrain)

    return {
        "status": "retraining started",
        "message": "Model will be updated in background. Restart server after completion."
    }


@router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    total = int(db.query(               # ← fix: int() wraps .scalar()
        func.count(FairnessAudit.id)
    ).scalar() or 0)

    if total == 0:
        return {
            "total_audits":  0,
            "biased_count":  0,
            "bias_rate_pct": 0.0,
            "avg_savings":   0.0,
            "avg_fairness":  0.0,
        }

    biased = db.query(
        func.count(FairnessAudit.id)
    ).filter(
        FairnessAudit.proxy_flag.is_(True)  # ← fix: removes yellow line
    ).scalar() or 0

    avg_orig = db.query(
        func.avg(FairnessAudit.original_premium)
    ).scalar() or 0

    avg_adj = db.query(
        func.avg(FairnessAudit.adjusted_premium)
    ).scalar() or 0

    avg_fairness = db.query(
        func.avg(FairnessAudit.fairness_score)
    ).scalar() or 0

    return {
        "total_audits":  total,
        "biased_count":  biased,
        "bias_rate_pct": round((biased / total) * 100, 1),
        "avg_savings":   round(avg_orig - avg_adj, 2),
        "avg_fairness":  round(float(avg_fairness), 3),
    }
    
@router.get("/audit/{audit_id}")
async def get_audit_by_id(
    audit_id: int,
    db: Session = Depends(get_db)
):
    audit = db.query(FairnessAudit).filter(
        FairnessAudit.id == audit_id
    ).first()

    if not audit:
        raise HTTPException(
            status_code=404,
            detail=f"Audit {audit_id} not found"
        )

    return {
        "application_id":     audit.application_id,
        "original_premium":   float(audit.original_premium or 0),
        "adjusted_premium":   float(audit.adjusted_premium or 0),
        "proxy_feature":      audit.proxy_feature,
        "proxy_strength":     float(audit.proxy_strength or 0),
        "fairness_score":     float(audit.fairness_score or 0),
        "proxy_flag":         bool(audit.proxy_flag),
        "explanation":        audit.explanation,
        "needs_human_review": bool(audit.needs_human_review),
        "shap_breakdown":     {},
        "status": (
            "ADJUSTED_FOR_FAIRNESS"
            if audit.proxy_flag
            else "IRDAI_COMPLIANT"
        ),
    }   
@router.get("/audits")
async def get_all_audits(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    audits = (
        db.query(FairnessAudit)
        .order_by(FairnessAudit.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id":               a.id,
            "application_id":   a.application_id,
            "original_premium": float(a.original_premium or 0),
            "adjusted_premium": float(a.adjusted_premium or 0),
            "fairness_score":   float(a.fairness_score or 0),
            "proxy_flag":       bool(a.proxy_flag),
            "city_tier":        None,
            "needs_human_review": bool(a.needs_human_review),
            "created_at":       str(a.created_at),
        }
        for a in audits
    ]