from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.agent import router as agent_router
from app.routes.applications import router as applications_router 

app=FastAPI(title="FAIRINSURE AGENT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[  "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",  # ← VS Code Live Server
        "*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(agent_router,prefix="/api",tags=["agent"])

app.include_router(applications_router, prefix="/api/applications", tags=["applications"]) 

@app.get("/health")
def heatlth():
    return{"status":"ok"}