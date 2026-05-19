import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib  # To save the trained model for later

# 1. Load Data
print("Loading Database...")
df = pd.read_csv('jm1.csv')

# 2. Data Cleaning (The "Janitor" Phase)
# Some NASA files have '?' instead of numbers. We must fix this.
# We loop through all columns and force them to be numbers.
# If a value is '?', it becomes NaN (Not a Number), and we drop that row.
for col in df.columns:
    if col != 'defects':  # Don't touch the target column
        df[col] = pd.to_numeric(df[col], errors='coerce')

# Drop rows with missing values (clean up the bad data)
old_rows = len(df)
df = df.dropna()
print(f"Cleaned Data: Kept {len(df)} rows (Dropped {old_rows - len(df)} bad rows)")

# 3. Separate Features (X) and Target (y)
# X = All columns EXCEPT 'defects'
# y = ONLY the 'defects' column
X = df.drop('defects', axis=1)
y = df['defects']

# 4. Split: 80% for Training, 20% for Testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. The "Learning" Phase
print("-" * 30)
print("Training the Random Forest Model... (This might take 10-20 seconds)")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
print("Training Complete!")

# 6. The "Exam" Phase
print("-" * 30)
print("Testing on new data...")
y_pred = model.predict(X_test)

# 7. The Report Card
accuracy = accuracy_score(y_test, y_pred)
print(f"Model Accuracy: {accuracy * 100:.2f}%")
print("\nDetailed Report:")
print(classification_report(y_test, y_pred))

# 8. Save the brain!
joblib.dump(model, 'bug_predictor_model.pkl')
print("Model saved as 'bug_predictor_model.pkl'")