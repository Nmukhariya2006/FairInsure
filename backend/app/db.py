# backend/app/db.py
import os
from sqlalchemy import create_engine, Column, Integer, Float, Boolean, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:1234@localhost:5432/FairInsure")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True, index=True)
    age = Column(Integer)
    bmi = Column(Float)
    city_tier = Column(String)
    annual_income = Column(Float)
    past_claims = Column(Integer)
    coverage_amount = Column(Float)
    smoker = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

class FairnessAudit(Base):
    __tablename__ = "fairness_audits"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    original_premium = Column(Float)
    adjusted_premium = Column(Float)
    proxy_feature = Column(String)
    proxy_strength = Column(Float)
    fairness_score = Column(Float)
    proxy_flag = Column(Boolean)
    explanation = Column(Text)
    needs_human_review = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db        # gives the session to the route
    finally:
        db.close()      # closes it no matter what

