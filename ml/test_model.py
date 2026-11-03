import numpy as np
import joblib

# Load trained model
model = joblib.load("isolation_forest.pkl")

# Normal activity
normal_activity = np.array([
    [50, 0.2, 1, 5, 10]
])

# Unusual activity
unusual_activity = np.array([
    [500, 5.0, 50, 200, 3]
])

# Predict
normal_result = model.predict(normal_activity)
unusual_result = model.predict(unusual_activity)

print("Normal activity prediction:", normal_result)
print("Unusual activity prediction:", unusual_result)

if normal_result[0] == 1:
    print("Normal activity detected.")

if unusual_result[0] == -1:
    print("Anomaly detected!")