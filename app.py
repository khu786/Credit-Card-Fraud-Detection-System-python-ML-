import streamlit as st
import pandas as pd
import os
import csv
import random
import requests
from datetime import datetime

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="FraudGuard AI",
    page_icon="🛡️",
    layout="wide"
)

# =====================================================
# SESSION STATE
# =====================================================
if "otp" not in st.session_state:
    st.session_state.otp = ""

if "txn_status" not in st.session_state:
    st.session_state.txn_status = "NONE"

if "last_payload" not in st.session_state:
    st.session_state.last_payload = None

# =====================================================
# FILE PATH
# =====================================================
HISTORY_FILE = "history.csv"

# =====================================================
# CREATE NEW CSV IF NOT EXISTS
# =====================================================
def create_history_file():
    with open(HISTORY_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "DateTime",
            "Amount",
            "Country",
            "Device",
            "Merchant",
            "Hour",
            "Risk",
            "Status",
            "Final_Result"
        ])

if not os.path.exists(HISTORY_FILE):
    create_history_file()

# =====================================================
# LOAD HISTORY SAFELY
# =====================================================
def load_history():
    try:
        df = pd.read_csv(HISTORY_FILE, on_bad_lines="skip")

        # If old file missing Final_Result column → recreate
        needed_cols = [
            "DateTime", "Amount", "Country", "Device",
            "Merchant", "Hour", "Risk", "Status", "Final_Result"
        ]

        for col in needed_cols:
            if col not in df.columns:
                create_history_file()
                return pd.read_csv(HISTORY_FILE)

        return df

    except:
        create_history_file()
        return pd.read_csv(HISTORY_FILE)

# =====================================================
# SAVE HISTORY
# =====================================================
def save_history(amount, country, device, merchant, hour, risk, status, final_result):
    with open(HISTORY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            amount,
            country,
            device,
            merchant,
            hour,
            risk,
            status,
            final_result
        ])

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("🛡️ FraudGuard AI")
menu = st.sidebar.radio(
    "Navigation",
    ["Fraud Detection", "Dashboard", "History"]
)

# =====================================================
# PAGE 1 - FRAUD DETECTION
# =====================================================
if menu == "Fraud Detection":

    st.title("💳 Real-Time Transaction Security")

    col1, col2 = st.columns(2)

    with col1:
        amount = st.number_input("Amount", 0.0, 100000.0, 1000.0)

        country = st.selectbox(
            "Country",
            ["India", "USA", "UK", "UAE", "Nigeria", "Russia", "China"]
        )

        device = st.selectbox(
            "Device",
            ["Known Mobile", "Known Laptop", "New Mobile",
             "New Laptop", "Public Device"]
        )

    with col2:
        merchant = st.selectbox(
            "Merchant",
            ["Grocery", "Restaurant", "Travel",
             "Electronics", "Jewelry", "Gaming"]
        )

        time_hour = st.slider("Transaction Hour", 0, 23, 12)

    # -------------------------------------------------
    # SUBMIT
    # -------------------------------------------------
    if st.button("🔍 Submit Transaction Request"):

        payload = {
            "amount": amount,
            "country": country,
            "device": device,
            "merchant": merchant,
            "time_hour": time_hour
        }

        st.session_state.last_payload = payload

        try:
            response = requests.post(
                "http://127.0.0.1:8000/predict",
                json=payload
            )

            result = response.json()

            risk = result["fraud_probability"]
            status = result["status"]

            st.subheader("Fraud Analysis Result")
            st.write("Risk Score:", f"{risk:.2%}")
            st.write("Decision:", status)

            # APPROVED
            if status == "APPROVED":
                st.success("✅ Transaction completed successfully.")

                save_history(
                    amount, country, device,
                    merchant, time_hour,
                    risk, status,
                    "COMPLETED"
                )

            # OTP
            elif status == "PENDING OTP":
                otp = str(random.randint(1000, 9999))
                st.session_state.otp = otp
                st.session_state.txn_status = "PENDING OTP"

                st.warning("⚠ Transaction not completed yet.")
                st.info("OTP required before payment.")
                st.info(f"Demo OTP: {otp}")

            # REVIEW
            elif status == "UNDER REVIEW":
                st.warning("🕒 Transaction on hold.")
                st.info("Funds not transferred yet.")

                save_history(
                    amount, country, device,
                    merchant, time_hour,
                    risk, status,
                    "ON HOLD"
                )

            # BLOCKED
            else:
                st.error("🚫 Transaction denied.")

                save_history(
                    amount, country, device,
                    merchant, time_hour,
                    risk, status,
                    "DENIED"
                )

        except:
            st.error("Backend server not running.")
            st.code("uvicorn api:app --reload")

    # -------------------------------------------------
    # OTP VERIFY
    # -------------------------------------------------
    if st.session_state.txn_status == "PENDING OTP":

        st.markdown("---")
        st.subheader("🔐 OTP Verification")

        user_otp = st.text_input("Enter OTP")

        if st.button("Verify OTP"):

            payload = st.session_state.last_payload

            if user_otp == st.session_state.otp:
                st.success("✅ OTP Verified")
                st.success("💰 Transaction completed.")

                save_history(
                    payload["amount"],
                    payload["country"],
                    payload["device"],
                    payload["merchant"],
                    payload["time_hour"],
                    "OTP VERIFIED",
                    "PENDING OTP",
                    "COMPLETED"
                )

            else:
                st.error("❌ Wrong OTP")
                st.error("🚫 Transaction cancelled.")

                save_history(
                    payload["amount"],
                    payload["country"],
                    payload["device"],
                    payload["merchant"],
                    payload["time_hour"],
                    "OTP FAILED",
                    "PENDING OTP",
                    "DENIED"
                )

            st.session_state.txn_status = "NONE"

# =====================================================
# PAGE 2 - DASHBOARD
# =====================================================
elif menu == "Dashboard":

    st.title("📊 Fraud Dashboard")

    df = load_history()

    if df.empty:
        st.warning("No history available.")

    else:
        total = len(df)
        completed = len(df[df["Final_Result"] == "COMPLETED"])
        denied = len(df[df["Final_Result"] == "DENIED"])
        hold = len(df[df["Final_Result"] == "ON HOLD"])

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Requests", total)
        c2.metric("Completed", completed)
        c3.metric("Denied", denied)
        c4.metric("On Hold", hold)

        st.markdown("---")
        st.subheader("Transaction Summary")
        st.bar_chart(df["Final_Result"].value_counts())

# =====================================================
# PAGE 3 - HISTORY
# =====================================================
elif menu == "History":

    st.title("📜 Transaction History")

    df = load_history()

    if df.empty:
        st.warning("No history available.")
    else:
        st.dataframe(df, use_container_width=True)