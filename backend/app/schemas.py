# backend/app/schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class ApplicationInput(BaseModel):
    age: int = Field(..., ge=18, le=80)
    bmi: float = Field(..., ge=10.0, le=60.0)
    city_tier: str = Field(..., pattern="^(tier1|tier2|tier3)$")
    annual_income: float
    past_claims: int = Field(..., ge=0, le=20)
    coverage_amount: float
    smoker: bool

class AuditResult(BaseModel):
    application_id: int
    original_premium: float
    adjusted_premium: float
    proxy_feature: str
    proxy_strength: float
    fairness_score: float
    proxy_flag: bool
    explanation: str
    needs_human_review: bool