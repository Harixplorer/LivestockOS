import joblib
import pandas as pd


# ============================================
# LOAD TRAINED MODEL
# ============================================

model = joblib.load(
    "LivestockOS/ml/models/isolation_forest_model.pkl"
)


# ============================================
# HEALTH SCORE FUNCTION
# ============================================

def calculate_health_score(data):

    score = 100

    if data["Body_Temperature_C"] > 39.5:
        score -= 30

    if data["Rumination_Time_hrs"] < 5:
        score -= 25

    if data["Walking_Distance_km"] < 2:
        score -= 25

    if data["Resting_Hours"] > 14:
        score -= 20

    return max(score, 0)


# ============================================
# MAIN PREDICTION FUNCTION
# ============================================

def predict_health(data):

    input_df = pd.DataFrame([data])

    prediction = model.predict(input_df)

    anomaly = (
        "ANOMALY DETECTED"
        if prediction[0] == -1
        else "NORMAL"
    )

    health_score = calculate_health_score(data)

    if health_score >= 80:
        status = "HEALTHY"

    elif health_score >= 50:
        status = "WARNING"

    else:
        status = "CRITICAL"

    return {
        "anomaly_status": anomaly,
        "health_score": health_score,
        "status": status
    }