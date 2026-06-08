from fastapi import FastAPI
import pandas as pd
import joblib
import os

app = FastAPI(
    title="FraudGuard AI API",
    version="2.0",
    description="Bank-style Fraud Detection with Review + OTP + Block Logic"
)

# ---------------------------------
# LOAD MODEL (optional)
# ---------------------------------
MODEL_PATH = "saved_models/fraud_new.pkl"

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None


# ---------------------------------
# HOME
# ---------------------------------
@app.get("/")
def home():
    return {"message": "FraudGuard AI API Running"}


# ---------------------------------
# PREDICT
# ---------------------------------
@app.post("/predict")
def predict(data: dict):

    amount = float(data["amount"])
    country = data["country"]
    device = data["device"]
    merchant = data["merchant"]
    hour = int(data["time_hour"])

    # ----------------------------
    # BASE RISK SCORE
    # ----------------------------
    risk = 0
    reasons = []

    # Amount Risk
    if amount >= 70000:
        risk += 45
        reasons.append("Very high amount")
    elif amount >= 30000:
        risk += 30
        reasons.append("High amount")
    elif amount >= 10000:
        risk += 15
        reasons.append("Medium amount")
    else:
        risk += 5

    # Country Risk
    if country in ["Nigeria", "Russia"]:
        risk += 20
        reasons.append("High-risk country")
    elif country in ["UAE", "China"]:
        risk += 10

    # Device Risk
    if device == "Public Device":
        risk += 20
        reasons.append("Public device used")
    elif device in ["New Mobile", "New Laptop"]:
        risk += 12
        reasons.append("New device detected")

    # Merchant Risk
    if merchant == "Jewelry":
        risk += 18
        reasons.append("Luxury merchant")
    elif merchant in ["Gaming", "Electronics", "Travel"]:
        risk += 10
        reasons.append("Risky merchant category")

    # Time Risk
    if hour >= 23 or hour <= 5:
        risk += 15
        reasons.append("Odd transaction hour")
    elif hour >= 21:
        risk += 8

    # ----------------------------
    # OPTIONAL ML MODEL BOOST
    # ----------------------------
    if model is not None:
        try:
            df = pd.DataFrame([data])
            prob = float(model.predict_proba(df)[0][1])
            risk += prob * 15
        except:
            prob = 0.0
    else:
        prob = 0.0

    # ----------------------------
    # FINAL DECISION
    # ----------------------------
    if risk >= 85:
        status = "BLOCKED"
        action = "Transaction denied. Contact bank."

    elif risk >= 60:
        status = "UNDER REVIEW"
        action = "Transaction held for manual review."

    elif risk >= 35:
        status = "PENDING OTP"
        action = "OTP verification required."

    else:
        status = "APPROVED"
        action = "Transaction approved."

    # ----------------------------
    # RESPONSE
    # ----------------------------
    return {
        "fraud_probability": round(min(risk / 100, 0.99), 2),
        "status": status,
        "action": action,
        "reasons": reasons
    }