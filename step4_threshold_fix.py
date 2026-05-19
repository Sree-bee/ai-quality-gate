import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import recall_score, accuracy_score, precision_score
import joblib

# 1. Load & Prepare (Same as before)
df = pd.read_csv('jm1.csv')
features = ['loc', 'v(g)', 'v', 'd', 'e']
target = 'defects'

for col in features:
    df[col] = pd.to_numeric(df[col], errors='coerce')
df = df.dropna()

X = df[features]
y = df[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 2. Train the Model
model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
model.fit(X_train, y_train)

# 3. GET PROBABILITIES (The Secret Weapon)
# Instead of yes/no, this gives us the % chance of a bug
probs = model.predict_proba(X_test)[:, 1]

# 4. Test different "Paranoia Levels"
print(f"{'Threshold':<15} {'Recall (Bugs Found)':<25} {'Accuracy':<15}")
print("-" * 60)

for threshold in [0.5, 0.4, 0.3, 0.25]:
    # If chance > threshold, call it a Bug (True)
    y_pred_adjusted = (probs >= threshold).astype(bool)
    
    rec = recall_score(y_test, y_pred_adjusted)
    acc = accuracy_score(y_test, y_pred_adjusted)
    
    print(f"{threshold:<15} {rec*100:.1f}%{' '*18} {acc*100:.1f}%")

print("-" * 60)
print("Recommendation: Pick a threshold where Recall is > 60% but Accuracy is still > 60%")