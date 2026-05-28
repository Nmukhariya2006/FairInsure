FAIRINSURE 🛡️
AI-Powered Fairness Auditing System for Insurance Premium Prediction

FairInsure is an AI-driven insurance premium auditing platform that detects and mitigates hidden socioeconomic bias in insurance pricing models.
It combines:

🤖 Machine Learning (XGBoost)
⚖️ Fairness Auditing
🔍 Explainable AI (SHAP)
🧠 LangGraph AI Agents
🚀 FastAPI Backend
🐘 PostgreSQL Database

The system predicts insurance premiums while ensuring that proxy variables such as pincode / city tier do not unfairly discriminate against users.

🚀 Features
✅ AI Premium Prediction

Uses an XGBoost regression model to calculate insurance premiums based on:

Age
BMI
Smoking status
Coverage amount
Past claims
Income
✅ Bias Detection Engine

Detects whether proxy variables like:

Pincode
City Tier
Income Region

are unfairly influencing premium pricing.

✅ Fairness Correction

If bias is detected:

Premium is adjusted
Unfair proxy contribution is reduced
Fairness score is generated
✅ Explainable AI (SHAP)

Uses SHAP values to explain:

Which features influenced prediction
How much each feature contributed
✅ LangGraph Multi-Agent Workflow

The system uses multiple AI agents:

Agent	Responsibility
Intake Agent	Stores application
Risk Agent	Predicts premium
Audit Agent	Detects bias
Compliance Agent	Saves fairness audit
Human Review Agent	Flags risky cases


⚙️ Installation Guide
1️⃣ Clone Repository
git clone https://github.com/YOUR_USERNAME/fairinsure.git
cd fairinsure/backend
2️⃣ Create Virtual Environment
python -m venv venv

Activate environment:

Windows
venv\Scripts\activate
Linux/Mac
source venv/bin/activate
3️⃣ Install Dependencies
pip install -r requirements.txt
🐘 PostgreSQL Setup
Create Database

Open PostgreSQL and create:

CREATE DATABASE fairhealth;

🤖 Train ML Model
Generate Dataset
python ml/generate_data.py
Train Model
python ml/train_model.py

This creates:

premium_model.pkl
features.pkl
🚀 Run Backend
uvicorn app.main:app --reload

Server runs at:

http://127.0.0.1:8000
📘 Swagger API Docs

Open:

http://127.0.0.1:8000/docs
🔥 Main API Endpoint

POST /api/audit

Runs the complete fairness auditing pipeline.

Sample Request
{
  "age": 25,
  "bmi": 22.5,
  "city_tier": "tier1",
  "annual_income": 500000,
  "past_claims": 1,
  "coverage_amount": 1000000,
  "smoker": false
}
Sample Response
{
  "application_id": 2,
  "original_premium": 43489,
  "adjusted_premium": 43489,
  "fairness_score": 0.95,
  "proxy_flag": false,
  "explanation": "No significant proxy bias detected.",
  "needs_human_review": false,
  "status": "IRDAI_COMPLIANT"
}
🧠 How the System Works
User Input
   ↓
Intake Agent
   ↓
Risk Agent (XGBoost)
   ↓
SHAP Feature Analysis
   ↓
Bias Audit Agent
   ↓
Fairness Adjustment
   ↓
Compliance Agent
   ↓
Database Storage
   ↓
Final Decision
⚖️ Fairness Logic

The system checks whether:

City Tier acts as a poverty proxy
Premium is unfairly inflated
Human review is required

If detected:

Proxy contribution is reduced
Premium is adjusted fairly
📊 Future Improvements
Frontend Dashboard (React)
Real-time Monitoring
Human Review Queue
PDF Audit Reports
AI Policy Explanation Chatbot
Kubernetes Deployment
CI/CD Pipeline
👨‍💻 Author

Nilay Mukhariya

📜 License

MIT License
