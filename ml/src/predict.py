import joblib
import pandas as pd


# ============================================
# LOAD TRAINED MODEL
# ============================================

model = joblib.load(
    "LivestockOS/ml/models/isolation_forest_model.pkl"
)

print("\nModel loaded successfully!")


# ============================================
# NEW SENSOR DATA
# ============================================

new_data = pd.DataFrame([
    {
        "Body_Temperature_C": 38.5,
        "Rumination_Time_hrs": 8.5,
        "Walking_Distance_km": 5.2,
        "Resting_Hours": 9
    }
])


# ============================================
# PREDICT ANOMALY
# ============================================

prediction = model.predict(new_data)

if prediction[0] == -1:
    anomaly_status = "ANOMALY DETECTED"
else:
    anomaly_status = "NORMAL"


# ============================================
# HEALTH SCORE FUNCTION
# ============================================

def calculate_health_score(row):

    score = 100

    if row["Body_Temperature_C"] > 39.5:
        score -= 30

    if row["Rumination_Time_hrs"] < 5:
        score -= 25

    if row["Walking_Distance_km"] < 2:
        score -= 25

    if row["Resting_Hours"] > 14:
        score -= 20

    return max(score, 0)


health_score = calculate_health_score(
    new_data.iloc[0]
)


# ============================================
# FINAL OUTPUT
# ============================================

print("\nPrediction Result:")
print(anomaly_status)

print(f"\nHealth Score: {health_score}")


if health_score >= 80:
    print("Status: HEALTHY")

elif health_score >= 50:
    print("Status: WARNING")

else:
    print("Status: CRITICAL")