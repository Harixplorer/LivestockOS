import pandas as pd
import time
import joblib

from sklearn.ensemble import IsolationForest


# ============================================
# LOAD DATASET
# ============================================

print("\nLoading dataset...")

df = pd.read_csv(
    "LivestockOS/ml/data/raw/global_cattle_disease_detection_dataset.csv"
)

print("Dataset loaded successfully!")

print("\nDataset Shape:")
print(df.shape)


# ============================================
# SELECT MVP FEATURES
# ============================================

features = [
    "Body_Temperature_C",
    "Rumination_Time_hrs",
    "Walking_Distance_km",
    "Resting_Hours"
]

X = df[features]

print("\nSelected Features:")
print(X.head())


# ============================================
# CHECK MISSING VALUES
# ============================================

print("\nMissing Values:")
print(X.isnull().sum())


# ============================================
# TRAIN ISOLATION FOREST MODEL
# ============================================

print("\nTraining Isolation Forest Model...")

start_time = time.time()

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,
    random_state=42,
    verbose=1,
    n_jobs=-1
)

model.fit(X)

end_time = time.time()

print("\nModel trained successfully!")

print(f"\nTraining Time: {end_time - start_time:.2f} seconds")


# ============================================
# SAVE MODEL
# ============================================

model_path = "LivestockOS/ml/models/isolation_forest_model.pkl"

joblib.dump(model, model_path)

print(f"\nModel saved successfully at:\n{model_path}")


# ============================================
# GENERATE PREDICTIONS
# ============================================

print("\nGenerating predictions...")

predictions = model.predict(X)

df["Anomaly"] = predictions

print("\nPrediction Counts:")
print(df["Anomaly"].value_counts())


# ============================================
# SHOW SAMPLE ANOMALIES
# ============================================

anomalies = df[df["Anomaly"] == -1]

print("\nSample Detected Anomalies:\n")

print(
    anomalies[
        [
            "Body_Temperature_C",
            "Rumination_Time_hrs",
            "Walking_Distance_km",
            "Resting_Hours"
        ]
    ].head(10)
)


# ============================================
# HEALTH SCORE SYSTEM
# ============================================

def calculate_health_score(row):

    score = 100

    # High temperature penalty
    if row["Body_Temperature_C"] > 39.5:
        score -= 30

    # Low rumination penalty
    if row["Rumination_Time_hrs"] < 5:
        score -= 25

    # Low activity penalty
    if row["Walking_Distance_km"] < 2:
        score -= 25

    # Excessive resting penalty
    if row["Resting_Hours"] > 14:
        score -= 20

    return max(score, 0)


df["Health_Score"] = df.apply(
    calculate_health_score,
    axis=1
)


# ============================================
# HEALTH SCORE OUTPUT
# ============================================

print("\nSample Health Scores:\n")

print(
    df[
        [
            "Body_Temperature_C",
            "Rumination_Time_hrs",
            "Walking_Distance_km",
            "Resting_Hours",
            "Health_Score"
        ]
    ].head(10)
)


# ============================================
# SAVE RESULTS
# ============================================

output_path = "LivestockOS/ml/outputs/predictions.csv"

df.to_csv(output_path, index=False)

print(f"\nPredictions saved successfully at:\n{output_path}")


print("\nML Pipeline Completed Successfully!")