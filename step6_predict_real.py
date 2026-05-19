import pandas as pd
import joblib
import radon.complexity as cc
import radon.metrics as metrics
from radon.visitors import ComplexityVisitor
import os

# --- CONFIGURATION ---
# We will test the script on ITSELF! (Meta, right?)
file_to_test = "step6_predict_real.py"
model_file = "bug_predictor_optimized.pkl"
# ---------------------

print(f"Analyzing file: {file_to_test}...")

# 1. READ THE FILE
if not os.path.exists(file_to_test):
    print("Error: File not found.")
    exit()

with open(file_to_test, 'r') as f:
    code_content = f.read()

# 2. EXTRACT METRICS (The Parser Logic)
# (Same logic as step 5, but condensed)
try:
    # A. LOC
    loc = len([line for line in code_content.split('\n') if line.strip()])
    
    # B. Complexity
    visitor = ComplexityVisitor.from_code(code_content)
    complexity = 0
    # If the file has functions, sum them. If it's a script, guess 1.
    if visitor.functions:
        for func in visitor.functions:
            complexity += func.complexity
    else:
        complexity = 1  # Base complexity for a script

    # C. Halstead
    h_visit = metrics.h_visit(code_content)
    v = h_visit.total.volume
    d = h_visit.total.difficulty
    e = h_visit.total.effort

    print("-" * 30)
    print(f"Extracted Metrics:")
    print(f"LOC: {loc}, Complexity: {complexity}, Vol: {v:.2f}, Diff: {d:.2f}, Effort: {e:.2f}")

except Exception as err:
    print(f"Error parsing code: {err}")
    exit()

# 3. LOAD THE BRAIN
print("-" * 30)
if not os.path.exists(model_file):
    print(f"Error: Model file '{model_file}' not found. Did you run step 3/4?")
    exit()

model = joblib.load(model_file)
print("AI Model Loaded successfully.")

# 4. PREDICT (Using our 'Paranoid' Threshold of 0.25)
# Prepare the data frame (The AI expects a table, even for 1 row)
input_data = pd.DataFrame([[loc, complexity, v, d, e]], 
                          columns=['loc', 'v(g)', 'v', 'd', 'e'])

# Get probability score (0.0 to 1.0)
risk_score = model.predict_proba(input_data)[0][1] 

print("-" * 30)
print(f"RISK SCORE: {risk_score * 100:.1f}%")

# Apply our threshold (0.25)
if risk_score > 0.25:
    print("🔴 VERDICT: HIGH RISK / POTENTIALLY BUGGY")
    print("Recommendation: Review logic and reduce complexity.")
else:
    print("🟢 VERDICT: LOW RISK / CLEAN")