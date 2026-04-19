"""
FastAPI Backend for Loan System
Run with: uvicorn api:app --reload
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LoanApplication(BaseModel):
    full_name: str
    email: str
    phone: str
    monthly_income: float
    employment_type: str
    loan_amount: float
    loan_purpose: str
    credit_score: Optional[int] = 750

@app.post("/api/apply")
async def apply_loan(application: LoanApplication):
    # Simple risk calculation
    risk = 0
    if application.monthly_income < 25000:
        risk += 40
    elif application.monthly_income < 50000:
        risk += 20
    
    if application.loan_amount > application.monthly_income * 12:
        risk += 30
    
    if application.credit_score and application.credit_score < 650:
        risk += 20
    
    if risk < 35:
        approved = application.loan_amount
        rate = 9.5
        status = "approved"
    elif risk < 65:
        approved = application.loan_amount * 0.7
        rate = 12.5
        status = "partial"
    else:
        approved = 0
        rate = 0
        status = "rejected"
    
    return {
        "application_id": str(uuid.uuid4())[:8],
        "status": status,
        "risk_score": risk,
        "approved_amount": approved,
        "interest_rate": rate,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
