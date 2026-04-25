# backend/app/routes/applications.py
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.db import get_db, Application, FairnessAudit
from app.schemas import ApplicationInput

router = APIRouter()


# ─────────────────────────────────────────────
# 1. CREATE APPLICATION
# Saves a new applicant to DB without running
# the full audit — used for draft saving
# ─────────────────────────────────────────────
@router.post("/", status_code=201)
async def create_application(
    payload: ApplicationInput,
    db: Session = Depends(get_db)
):
    """
    Saves applicant data to DB.
    Does NOT run the audit — just stores the record.
    The frontend calls /api/audit for the full pipeline.
    Use this if you want to save a draft first.
    """
    try:
        app = Application(**payload.dict())
        db.add(app)
        db.commit()
        db.refresh(app)
        return {
            "id":         app.id,
            "created_at": str(app.created_at),
            "message":    "Application saved successfully"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 2. GET ALL APPLICATIONS
# Dashboard table — list of all applicants
# Supports pagination and filtering
# ─────────────────────────────────────────────
@router.get("/")
async def get_all_applications(
    limit:     int            = Query(50, ge=1, le=200),
    offset:    int            = Query(0, ge=0),
    city_tier: Optional[str]  = Query(None),
    smoker:    Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns paginated list of all applications.
    Optional filters:
      ?city_tier=tier3         → rural only
      ?smoker=true             → smokers only
      ?city_tier=tier3&smoker=true → both filters
    """
    query = db.query(Application)

    # Apply filters if provided
    if city_tier:
        query = query.filter(
            Application.city_tier == city_tier
        )
    if smoker is not None:
        query = query.filter(
            Application.smoker == smoker
        )

    total = query.count()

    applications = (
        query
        .order_by(desc(Application.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total":        total,
        "limit":        limit,
        "offset":       offset,
        "applications": [
            {
                "id":             a.id,
                "age":            a.age,
                "bmi":            a.bmi,
                "city_tier":      a.city_tier,
                "annual_income":  a.annual_income,
                "past_claims":    a.past_claims,
                "coverage_amount":a.coverage_amount,
                "smoker":         a.smoker,
                "created_at":     str(a.created_at),
                # Include audit summary if it exists
                "has_audit":      a.audit is not None,
                "fairness_score": (
                    a.audit.fairness_score
                    if a.audit else None
                ),
                "proxy_flag": (
                    a.audit.proxy_flag
                    if a.audit else None
                ),
            }
            for a in applications
        ]
    }


# ─────────────────────────────────────────────
# 3. GET SINGLE APPLICATION
# Full detail view — application + its audit
# ─────────────────────────────────────────────
@router.get("/{application_id}")
async def get_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns one application by ID.
    Includes its linked fairness audit if it exists.
    """
    app = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not app:
        raise HTTPException(
            status_code=404,
            detail=f"Application {application_id} not found"
        )

    result = {
        "id":             app.id,
        "age":            app.age,
        "bmi":            app.bmi,
        "city_tier":      app.city_tier,
        "annual_income":  app.annual_income,
        "past_claims":    app.past_claims,
        "coverage_amount":app.coverage_amount,
        "smoker":         app.smoker,
        "created_at":     str(app.created_at),
    }

    # Attach audit data if available
    if app.audit:
        result["audit"] = {
            "audit_id":         app.audit.id,
            "original_premium": app.audit.original_premium,
            "adjusted_premium": app.audit.adjusted_premium,
            "proxy_feature":    app.audit.proxy_feature,
            "proxy_strength":   app.audit.proxy_strength,
            "fairness_score":   app.audit.fairness_score,
            "proxy_flag":       app.audit.proxy_flag,
            "explanation":      app.audit.explanation,
            "needs_human_review": app.audit.needs_human_review,
            "savings": round(
                app.audit.original_premium
                - app.audit.adjusted_premium, 2
            ),
        }
    else:
        result["audit"] = None

    return result


# ─────────────────────────────────────────────
# 4. UPDATE APPLICATION
# Lets you correct a typo before running audit
# ─────────────────────────────────────────────
@router.put("/{application_id}")
async def update_application(
    application_id: int,
    payload: ApplicationInput,
    db: Session = Depends(get_db)
):
    """
    Updates an existing application record.
    Only allowed if no audit has been run yet —
    you cannot change data after it has been audited
    (audit trail integrity).
    """
    app = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not app:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    # Block update if already audited
    if app.audit:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot update application after audit. "
                "Audit trail must remain immutable."
            )
        )

    # Apply updates
    for field, value in payload.dict().items():
        setattr(app, field, value)

    try:
        db.commit()
        db.refresh(app)
        return {
            "id":      app.id,
            "updated": True,
            "message": "Application updated"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 5. DELETE APPLICATION
# Hard delete — only if no audit exists
# ─────────────────────────────────────────────
@router.delete("/{application_id}")
async def delete_application(
    application_id: int,
    db: Session = Depends(get_db)
):
    """
    Deletes an application.
    Blocked if an audit exists — regulators require
    complete records to be retained.
    """
    app = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not app:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    if app.audit:
        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete audited application. "
                "IRDAI requires audit records to be retained."
            )
        )

    try:
        db.delete(app)
        db.commit()
        return {"deleted": True, "id": application_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 6. BULK UPLOAD
# Upload multiple applicants at once via JSON list
# Useful for insurer uploading a batch CSV
# ─────────────────────────────────────────────
@router.post("/bulk", status_code=201)
async def bulk_create_applications(
    payload: List[ApplicationInput],
    db: Session = Depends(get_db)
):
    """
    Creates multiple applications in one request.
    Max 100 at a time to prevent abuse.
    Returns list of created IDs.
    """
    if len(payload) > 100:
        raise HTTPException(
            status_code=400,
            detail="Max 100 applications per bulk upload"
        )

    created_ids = []
    try:
        for item in payload:
            app = Application(**item.dict())
            db.add(app)
            db.flush()          # gets the id without committing
            created_ids.append(app.id)

        db.commit()
        return {
            "created":  len(created_ids),
            "ids":      created_ids,
            "message":  f"{len(created_ids)} applications saved"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# 7. SUMMARY STATS BY CITY TIER
# Dashboard breakdown — bias by location
# ─────────────────────────────────────────────
@router.get("/stats/by-tier")
async def stats_by_tier(
    db: Session = Depends(get_db)
):
    """
    Returns per-tier breakdown:
    count, avg premium, avg fairness score, bias rate.
    Used by dashboard bar chart.
    """
    tiers = ["tier1", "tier2", "tier3"]
    result = []

    for tier in tiers:
        apps = (
            db.query(Application)
            .filter(Application.city_tier == tier)
            .all()
        )
        total = len(apps)
        if total == 0:
            continue

        audited = [a for a in apps if a.audit]
        biased  = [a for a in audited if a.audit.proxy_flag]

        avg_orig = (
            sum(a.audit.original_premium for a in audited)
            / len(audited)
        ) if audited else 0

        avg_adj = (
            sum(a.audit.adjusted_premium for a in audited)
            / len(audited)
        ) if audited else 0

        avg_fairness = (
            sum(a.audit.fairness_score for a in audited)
            / len(audited)
        ) if audited else 0

        result.append({
            "city_tier":       tier,
            "total":           total,
            "audited":         len(audited),
            "biased":          len(biased),
            "bias_rate_pct":   round(
                (len(biased) / len(audited) * 100)
                if audited else 0, 1
            ),
            "avg_original_premium": round(avg_orig, 2),
            "avg_fair_premium":     round(avg_adj, 2),
            "avg_savings":          round(avg_orig - avg_adj, 2),
            "avg_fairness_score":   round(avg_fairness, 3),
        })

    return result


# ─────────────────────────────────────────────
# 8. RECENT APPLICATIONS
# Last N applications — for dashboard live feed
# ─────────────────────────────────────────────
@router.get("/recent/feed")
async def recent_applications(
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Returns applications from last N hours.
    Default: last 24 hours.
    Max: last 7 days (168 hours).
    Used by dashboard live activity feed.
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    apps = (
        db.query(Application)
        .filter(Application.created_at >= cutoff)
        .order_by(desc(Application.created_at))
        .limit(20)
        .all()
    )

    return {
        "hours":   hours,
        "count":   len(apps),
        "applications": [
            {
                "id":         a.id,
                "city_tier":  a.city_tier,
                "age":        a.age,
                "smoker":     a.smoker,
                "created_at": str(a.created_at),
                "audited":    a.audit is not None,
                "proxy_flag": (
                    a.audit.proxy_flag if a.audit else None
                ),
            }
            for a in apps
        ]
    }