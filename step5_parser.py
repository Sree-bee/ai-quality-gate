import radon.complexity as cc
import radon.metrics as metrics
from radon.visitors import ComplexityVisitor

# This is a sample code string we will test (a simple password checker)
# In the real website, this will be the file the user uploads.
sample_code = """
def check_password(password):
    if len(password) < 8:
        return False
    for char in password:
        if char.isdigit():
            return True
    return False
"""

print("Analyzing sample code...")
print("-" * 30)

# 1. Calculate Cyclomatic Complexity (v(g))
# We use Radon's visitor to walk through the code structure
visitor = ComplexityVisitor.from_code(sample_code)
complexity = 0
# A file might have multiple functions; we sum their complexity
for func in visitor.functions:
    complexity += func.complexity

print(f"Cyclomatic Complexity v(g): {complexity}")

# 2. Calculate Halstead Metrics (v, d, e)
# h_visit is the "Halstead Visitor"
try:
    h_visit = metrics.h_visit(sample_code)
    # The total metrics for the whole file
    total_metrics = h_visit.total
    
    # Extract the 3 specific numbers our AI needs
    h_volume = total_metrics.volume
    h_difficulty = total_metrics.difficulty
    h_effort = total_metrics.effort

    print(f"Halstead Volume (v):       {h_volume:.2f}")
    print(f"Halstead Difficulty (d):   {h_difficulty:.2f}")
    print(f"Halstead Effort (e):       {h_effort:.2f}")

except Exception as e:
    print(f"Error calculating Halstead: {e}")
    h_volume, h_difficulty, h_effort = 0, 0, 0

# 3. Calculate LOC (Lines of Code)
# We count non-empty lines
loc = len([line for line in sample_code.split('\n') if line.strip()])
print(f"Lines of Code (loc):       {loc}")