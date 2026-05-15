import pandas as pd
import os

# ============================================
# DATASET 1: CATTLE DISEASE DETECTION
# ============================================

print("=" * 60)
print("DATASET 1: CATTLE DISEASE DETECTION")
print("=" * 60)

df1 = pd.read_csv(
    "LivestockOS/ml/data/raw/global_cattle_disease_detection_dataset.csv"
)

print(f"\nShape: {df1.shape[0]} rows x {df1.shape[1]} columns")
print(f"File Size: {os.path.getsize('LivestockOS/ml/data/raw/global_cattle_disease_detection_dataset.csv') / 1e6:.1f} MB")

print("\n--- ALL COLUMNS ---")
for i, col in enumerate(df1.columns, 1):
    print(f"  {i:2d}. {col} ({df1[col].dtype})")

print("\n--- FIRST 3 ROWS ---")
print(df1.head(3).to_string())

print("\n--- MISSING VALUES ---")
missing = df1.isnull().sum()
missing_cols = missing[missing > 0]
if len(missing_cols) == 0:
    print("  No missing values!")
else:
    print(missing_cols.to_string())

print("\n--- BASIC STATS (Numeric) ---")
print(df1.describe().round(2).to_string())

# Check for potential label/target columns
print("\n--- POTENTIAL LABEL COLUMNS ---")
for col in df1.columns:
    if df1[col].dtype == 'object' or df1[col].nunique() < 20:
        print(f"\n  {col} ({df1[col].nunique()} unique values):")
        print(f"  {df1[col].value_counts().head(10).to_string()}")


# ============================================
# DATASET 2: MILK YIELD PREDICTION
# ============================================

print("\n\n" + "=" * 60)
print("DATASET 2: MILK YIELD PREDICTION")
print("=" * 60)

df2 = pd.read_csv(
    "LivestockOS/ml/data/raw/global_cattle_milk_yield_prediction_dataset.csv"
)

print(f"\nShape: {df2.shape[0]} rows x {df2.shape[1]} columns")
print(f"File Size: {os.path.getsize('LivestockOS/ml/data/raw/global_cattle_milk_yield_prediction_dataset.csv') / 1e6:.1f} MB")

print("\n--- ALL COLUMNS ---")
for i, col in enumerate(df2.columns, 1):
    print(f"  {i:2d}. {col} ({df2[col].dtype})")

print("\n--- FIRST 3 ROWS ---")
print(df2.head(3).to_string())

print("\n--- MISSING VALUES ---")
missing2 = df2.isnull().sum()
missing_cols2 = missing2[missing2 > 0]
if len(missing_cols2) == 0:
    print("  No missing values!")
else:
    print(missing_cols2.to_string())

print("\n--- BASIC STATS (Numeric) ---")
print(df2.describe().round(2).to_string())

# Check for potential label/target columns
print("\n--- POTENTIAL LABEL COLUMNS ---")
for col in df2.columns:
    if df2[col].dtype == 'object' or df2[col].nunique() < 20:
        print(f"\n  {col} ({df2[col].nunique()} unique values):")
        print(f"  {df2[col].value_counts().head(10).to_string()}")


# ============================================
# SUMMARY
# ============================================

print("\n\n" + "=" * 60)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 60)

print(f"\nDataset 1: {df1.shape[0]} rows, {df1.shape[1]} cols — Disease Detection")
print(f"Dataset 2: {df2.shape[0]} rows, {df2.shape[1]} cols — Milk Yield Prediction")

print("\nDone!")
