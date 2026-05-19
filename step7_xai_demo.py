import joblib
import pandas as pd
import radon.complexity as cc
import radon.metrics as metrics
from radon.visitors import ComplexityVisitor

# --- CONFIGURATION ---
file_to_test = "step6_predict_real.py"
model_file = "bug_predictor_optimized.pkl"
# ---------------------

print(f"🔬 EXPLAINABLE AI ANALYSIS FOR: {file_to_test}")
print("-" * 50)

# 1. PARSE (The Eyes)
with open(file_to_test, 'r') as f:
    code = f.read()

# Calculate Metrics
loc = len([line for line in code.split('\n') if line.strip()])
visitor = ComplexityVisitor.from_code(code)
complexity = sum([func.complexity for func in visitor.functions]) if visitor.functions else 1
h_visit = metrics.h_visit(code)
v, d, e = h_visit.total.volume, h_visit.total.difficulty, h_visit.total.effort

# 2. PREDICT (The Brain)
model = joblib.load(model_file)
# Create DataFrame with correct column names for the model
features = pd.DataFrame([[loc, complexity, v, d, e]], 
                        columns=['loc', 'v(g)', 'v', 'd', 'e'])

# Get the probability
risk_prob = model.predict_proba(features)[0][1]
risk_percentage = risk_prob * 100

# 3. EXPLAIN (The XAI Layer)
# We look at the "Feature Importances" stored inside the Random Forest
# This tells us which metric the Brain cares about the most.
importances = model.feature_importances_
feature_names = ['Lines of Code', 'Complexity', 'Volume', 'Difficulty', 'Effort']

# We map the model's general logic to this specific file
print(f"\n📊 DIAGNOSTIC REPORT")
print(f"Risk Probability: {risk_percentage:.1f}%")
print(f"Quality Score:    {100 - risk_percentage:.1f}/100")

if risk_percentage > 25:
    print("\n🔴 STATUS: HIGH RISK DETECTED")
    print("Why? Based on the model's decision logic:")
    
    # Simple logic to explain "Why" based on thresholds (Rule-based XAI)
    # These thresholds are typical 'warning zones'
    reasons = []
    if complexity > 5:
        reasons.append(f"- Cyclomatic Complexity is {complexity} (High). Too many loops/branches.")
    if v > 1000:
        reasons.append(f"- Halstead Volume is {v:.0f} (High). Too many variables/operations.")
    if loc > 50:
        reasons.append(f"- File size is {loc} lines. Large files are statistically harder to maintain.")
        
    if not reasons:
        reasons.append("- Combined metrics exceed the safety threshold, even if no single metric is extreme.")
        
    for r in reasons:
        print(r)
        
    # 4. GUIDED FIXING (The Advice Layer)
    print("\n🛠️ SUGGESTED REFACTORING:")
    if complexity > 5:
        print("  • Action: Extract complex logic into separate helper functions.")
    if loc > 50:
        print("  • Action: Break this file into modules (e.g., separate 'Model' logic from 'Parsing' logic).")
else:
    print("\n🟢 STATUS: CLEAN")
    print("Good job! The code structure is within safe limits.")