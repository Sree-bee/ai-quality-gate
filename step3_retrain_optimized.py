import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# 1. Load Data
df = pd.read_csv('jm1.csv')

# 2. Select ONLY the columns we can easily calculate in Python (Radon metrics)
selected_features = ['loc', 'v(g)', 'v', 'd', 'e']
target = 'defects'

# 3. Clean Data
for col in selected_features:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df = df.dropna()

# 4. Split X and y
X = df[selected_features]
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Train with the "Recall Fix"
print("-" * 30)
print("Training with class_weight='balanced' to fix low recall...")
# We add class_weight='balanced' to tell the model to pay attention to the minority class (Bugs)
model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
model.fit(X_train, y_train)

# 6. Test
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

# 7. Detailed Report
print("-" * 30)
print(f"New Accuracy: {accuracy * 100:.2f}%")
print("\nNew Report Card:")
print(classification_report(y_test, y_pred))

# 8. Save
joblib.dump(model, 'bug_predictor_optimized.pkl')
print("Saved optimized model.")