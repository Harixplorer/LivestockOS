from ml_service import predict_health


sample_data = {
    "Body_Temperature_C": 38.5,
    "Rumination_Time_hrs": 8.5,
    "Walking_Distance_km": 5.2,
    "Resting_Hours": 9
}


result = predict_health(sample_data)

print(result)