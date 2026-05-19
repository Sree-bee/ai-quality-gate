import pandas as pd
import os

# 1. Check if file exists
filename = 'jm1.csv'  # <--- Make sure this matches your file name!
if not os.path.exists(filename):
    print(f"ERROR: Could not find '{filename}' in this folder.")
    print("Files found here:", os.listdir())
else:
    # 2. Try to load the dataset
    try:
        df = pd.read_csv(filename)
        
        print("-" * 30)
        print("SUCCESS: Data Loaded!")
        print("-" * 30)
        print(f"Total Rows:    {len(df)}")
        print(f"Total Columns: {len(df.columns)}")
        print("\nFirst 3 rows of data:")
        print(df[['loc', 'v(g)', 'defects']].head(3))
        
        # 3. Check for the 'Question Mark' issue
        # We check if the 'branchCount' column is being read as text (Object) instead of numbers
        # This is the most common error in this dataset.
        print("\n[Data Type Check]")
        if df['v(g)'].dtype == 'object':
             print("ALERT: The dataset has '?' symbols mixed with numbers.")
             print("We will need to clean this in the next step.")
        else:
             print("Data looks clean!")
            # df = pd.read_csv('jm1.csv')
             print(df.columns)
             
    except Exception as e:
        print("CRITICAL ERROR:", e)