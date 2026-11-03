import numpy as np
from sklearn.ensemble import IsolationForest
import joblib

print("Starting ML model training...")

# Generate normal activity data
np.random.seed(42)

X = np.column_stack([
    np.random.randint(20, 100, 200),
    np.random.uniform(0.01, 1.0, 200),
    np.random.randint(0, 5, 200),
    np.random.randint(0, 20, 200),
    np.random.randint(8, 18, 200)
])

print("Training data created.")

# Create Isolation Forest
model = IsolationForest(
    contamination=0.05,
    random_state=42
)

print("Training model...")

model.fit(X)

print("Model trained successfully!")

# Save model
joblib.dump(model, "isolation_forest.pkl")

print("Model saved as isolation_forest.pkl")