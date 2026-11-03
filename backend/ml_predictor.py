import joblib
import numpy as np
import os

# Find the trained model
model_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "ml",
    "isolation_forest.pkl"
)

# Load the trained model
model = joblib.load(model_path)


def predict_anomaly(
    query_length,
    execution_time,
    rows_affected,
    rows_returned,
    hour
):
    # Create input data
    data = np.array([[
        query_length,
        execution_time,
        rows_affected,
        rows_returned,
        hour
    ]])

    # Make prediction
    prediction = model.predict(data)

    # Convert result into readable status
    if prediction[0] == -1:
        return "ANOMALY"
    else:
        return "NORMAL"