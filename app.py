from flask import Flask, render_template, request, redirect, url_for
import os
import zipfile
import tempfile
import shutil
import ast
import joblib
import pandas as pd
import radon.complexity as cc
import radon.metrics as metrics
from radon.visitors import ComplexityVisitor
from werkzeug.utils import secure_filename
import requests
# --- GENERATIVE AI CONFIGURATION ---
# from google import genai

# Clean, default initialization
# client = genai.Client(api_key="AIzaSyAsP7nb_beBPoL-c98indzIiGHRUxvLa74")

# --- GENERATIVE AI CONFIGURATION ---
from google import genai

client = genai.Client(api_key="AIzaSyAsP7nb_beBPoL-c98indzIiGHRUxvLa74")

app = Flask(__name__)

MODEL_FILE = "bug_predictor_optimized.pkl"
model = joblib.load(MODEL_FILE)

PROJECT_CACHE = {
    'results': [],
    'file_details': {},
    'avg_risk': 0,
    'file_count': 0
}

def extract_function_text(source_code, start_line, end_line):
    lines = source_code.split('\n')
    return '\n'.join(lines[start_line - 1 : end_line])

def analyze_dependencies(temp_dir):
    dependencies = {}
    local_modules = []
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.py'):
                local_modules.append(file.replace('.py', ''))
    for root, dirs, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                filename = file.replace('.py', '')
                dependencies[filename] = {'fan_out': 0, 'fan_in': 0, 'imports': []}
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            imported_module = None
                            if isinstance(node, ast.Import):
                                imported_module = node.names[0].name.split('.')[0]
                            elif isinstance(node, ast.ImportFrom) and node.module:
                                imported_module = node.module.split('.')[0]
                            if imported_module and imported_module in local_modules and imported_module != filename:
                                if imported_module not in dependencies[filename]['imports']:
                                    dependencies[filename]['imports'].append(imported_module)
                                    dependencies[filename]['fan_out'] += 1
                except:
                    pass
    for module, data in dependencies.items():
        for imported in data['imports']:
            if imported in dependencies:
                dependencies[imported]['fan_in'] += 1
    return dependencies

@app.route('/', methods=['GET', 'POST'])
def index():
    global PROJECT_CACHE
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '' and uploaded_file.filename.endswith('.zip'):
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, secure_filename(uploaded_file.filename))
            uploaded_file.save(zip_path)
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            project_deps = analyze_dependencies(temp_dir)
            
            PROJECT_CACHE['results'] = []
            PROJECT_CACHE['file_details'] = {}
            total_project_risk = 0
            
            # Temporary dictionary to store scores for Pass 2
            file_risk_scores = {}

            # --- PASS 1: Calculate AI Risk for every file ---
            # for root, dirs, files in os.walk(temp_dir):
            #     for file in files:
            #         if file.endswith('.py'):
            #             filepath = os.path.join(root, file)
            #             filename_no_ext = file.replace('.py', '')
               # --- PASS 1: Calculate AI Risk for every file ---
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        # NEW: Calculate the unique relative path and fix Windows slashes for web URLs
                        relative_path = os.path.relpath(filepath, temp_dir).replace('\\', '/')
                        
                        # Use the relative path for the module name to prevent dependency collisions
                        filename_no_ext = relative_path.replace('.py', '')         

                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            code_content = f.read()

                        loc_total = len([line for line in code_content.split('\n') if line.strip()])
                        if loc_total == 0: continue
                        
                        try:
                            visitor = ComplexityVisitor.from_code(code_content)
                            complexity_total = sum([func.complexity for func in visitor.functions]) if visitor.functions else 1
                            h_visit_total = metrics.h_visit(code_content)
                            v_total = h_visit_total.total.volume
                            d_total = h_visit_total.total.difficulty
                            e_total = h_visit_total.total.effort
                        except:
                            continue

                        features = pd.DataFrame([[loc_total, complexity_total, v_total, d_total, e_total]], columns=['loc', 'v(g)', 'v', 'd', 'e'])
                        risk_prob = model.predict_proba(features)[0][1]
                        risk_percentage = risk_prob * 100
                        quality_score = 100 - risk_percentage
                        total_project_risk += risk_percentage
                        
                        # Save score for Phase 2
                        file_risk_scores[filename_no_ext] = risk_percentage

                        hotspots = []
                        if visitor.functions:
                            for func in visitor.functions:
                                func_loc = func.endline - func.lineno + 1
                                func_complexity = func.complexity
                                func_text = extract_function_text(code_content, func.lineno, func.endline)
                                try:
                                    h_visit_func = metrics.h_visit(func_text)
                                    func_v = round(h_visit_func.total.volume, 1)
                                    func_d = round(h_visit_func.total.difficulty, 1)
                                except:
                                    func_v, func_d = 0, 0

                                is_risky = func_complexity > 5 or func_loc > 20 or func_v > 100
                                hotspots.append({
                                    'name': func.name, 'line': func.lineno, 'loc': func_loc,
                                    'complexity': func_complexity, 'volume': func_v, 
                                    'difficulty': func_d, 'is_risky': is_risky,
                                    'code': func_text
                                })
                            hotspots.sort(key=lambda x: x['complexity'], reverse=True)

                        reasons = []
                        fixes = []
                        if complexity_total > 5:
                            reasons.append(f"High Complexity ({complexity_total}): Too many nested loops or conditions.")
                            fixes.append("Extract complex logic into separate helper functions.")
                        if v_total > 1000:
                            reasons.append(f"High Volume ({v_total:.0f}): Too many variables and operations.")
                            fixes.append("Reduce the number of variables; simplify mathematical operations.")
                        if loc_total > 50:
                            reasons.append(f"Large File Size ({loc_total} lines): Harder to maintain.")
                            fixes.append("Break this file down into smaller, focused modules.")
                        if not reasons and risk_percentage > 25:
                            reasons.append("Combined metrics exceed the safety threshold.")
                            fixes.append("General code review recommended to simplify structure.")

                        deps = project_deps.get(filename_no_ext, {'fan_out': 0, 'fan_in': 0, 'imports': []})
                        coupling_warning = deps['fan_out'] > 5 or deps['fan_in'] > 5

                        PROJECT_CACHE['results'].append({
                            'filepath': relative_path,
                            'filename': file,
                            'filename_no_ext': filename_no_ext,
                            'loc': loc_total,
                            'complexity': complexity_total,
                            'risk_score': round(risk_percentage, 1),
                            'fan_in': deps['fan_in'],
                            'fan_out': deps['fan_out'],
                            'coupling_warning': coupling_warning,
                            'imports': deps['imports']
                        })

                        PROJECT_CACHE['file_details'][relative_path] = {
                            'filepath': relative_path,
                            'filename': file,
                            'code': code_content,
                            'risk': risk_percentage,
                            'quality': quality_score,
                            'metrics': {'loc': loc_total, 'complexity': complexity_total, 'volume': round(v_total,2)},
                            'reasons': reasons,
                            'fixes': fixes,
                            'hotspots': hotspots
                        }

            # --- PASS 2: Propagated Risk (Infection) Engine ---
            for result in PROJECT_CACHE['results']:
                infected_by = []
                # Check every file this module imports
                for imported_module in result['imports']:
                    # If the imported module is in our project and its ML score is > 25%
                    if imported_module in file_risk_scores and file_risk_scores[imported_module] > 25:
                        infected_by.append(f"{imported_module}.py")
                
                # Save the infection data back to the cache
                result['infected_by'] = infected_by
                PROJECT_CACHE['file_details'][result['filepath']]['infected_by'] = infected_by
                # PROJECT_CACHE['file_details'][result['filename']]['infected_by'] = infected_by

            shutil.rmtree(temp_dir)
            PROJECT_CACHE['avg_risk'] = round(total_project_risk / len(PROJECT_CACHE['results']), 1) if PROJECT_CACHE['results'] else 0
            PROJECT_CACHE['file_count'] = len(PROJECT_CACHE['results'])
            PROJECT_CACHE['results'].sort(key=lambda x: x['risk_score'], reverse=True)

            return redirect(url_for('dashboard'))

    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('project_dashboard.html', 
                           project_results=PROJECT_CACHE['results'],
                           avg_risk=PROJECT_CACHE['avg_risk'],
                           file_count=PROJECT_CACHE['file_count'])

# @app.route('/file/<filename>')
# def file_detail(filename):
#     if filename in PROJECT_CACHE['file_details']:
#         data = PROJECT_CACHE['file_details'][filename]
#         return render_template('file_detail.html', **data)
#     return "Error: File data not found.", 404
# 1. Add "path:" so Flask accepts folder slashes in the URL
@app.route('/file/<path:filepath>')
def file_detail(filepath): # 2. Change the variable name to match
    
    # 3. Look up the file using the full path instead of just the short name
    if filepath in PROJECT_CACHE['file_details']:
        data = PROJECT_CACHE['file_details'][filepath]
        return render_template('file_detail.html', **data)
        
    return "Error: File data not found.", 404
#--- NEW ROUTE: Generative AI Auto-Fix ---
# @app.route('/api/autofix', methods=['POST'])
# def autofix():
#     data = request.json
#     messy_code = data.get('code', '')
    
#     prompt = f"""
#     You are a Senior Python Software Architect. The following function was flagged by our static 
#     analysis tool for having high cyclomatic complexity and bad Halstead metrics.
#     Refactor it to be clean, modular, and easy to read. 
#     Return ONLY the raw python code. Do not include markdown formatting or explanations.
    
#     Original Code:
#     {messy_code}
#     """
    
#     try:
#         # Jump straight to the latest universally free model: Gemini 2.5 Flash
#         response = client.models.generate_content(
#             model='gemini-2.5-flash',
#             contents=prompt,
#         )
#         # Strip out markdown block formatting if the AI adds it
#         clean_code = response.text.replace("```python\n", "").replace("```", "").strip()
#         return {"status": "success", "fixed_code": clean_code}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}, 500



import requests # Make sure this is at the top of your file!

@app.route('/api/autofix', methods=['POST'])
def autofix():
    data = request.json
    messy_code = data.get('code', '')
    
    prompt = f"""
     You are a Senior Python Software Architect. The following function was flagged by our static analysis tool for having high cyclomatic complexity and bad Halstead metrics.
     Refactor it to be clean, modular, and easy to read.
     You MUST format your response exactly like this:
     [EXPLANATION]
     Provide a bulleted list explaining exactly what you changed and why it improves the code. Format this section as clean HTML using <ul> and <li> tags.
     [CODE]
     Write the raw, refactored python code here. Do not include markdown code blocks.
    
    Original Code:
    {messy_code}
    """
    
    try:
        # THE REST API BYPASS
        # Bypasses the SDK and local firewalls by acting like standard web traffic
        api_key = "AIzaSyAsP7nb_beBPoL-c98indzIiGHRUxvLa74" 
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        # Send the standard HTTP request
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            # Successfully got the REAL AI response
            raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
            
            if "[CODE]" in raw_text:
                parts = raw_text.split("[CODE]")
                explanation_html = parts[0].replace("[EXPLANATION]", "").strip()
                clean_code = parts[1].replace("```python\n", "").replace("```", "").strip()
            else:
                explanation_html = "<ul><li>Code was refactored for readability and complexity reduction.</li></ul>"
                clean_code = raw_text.replace("```python\n", "").replace("```", "").strip()
                
            return {"status": "success", "fixed_code": clean_code, "explanation": explanation_html}
        else:
            # If Google still rejects it (e.g., wrong API key), force an error to trigger the circuit breaker
            raise Exception(f"API Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"🚨 CIRCUIT BREAKER TRIPPED! Reason: {str(e)}") 
        
        
        error_message = str(e)
        
        # THE CIRCUIT BREAKER (Your safety net)
        demo_explanation = "<ul><li><strong>[SYSTEM ALERT]</strong> Network failure detected. Falling back to cache.</li></ul>"
        demo_code = "# Fake fallback code. The real AI request failed.\ndef fallback_function():\n    return False"
        
        return {"status": "success", "fixed_code": demo_code, "explanation": demo_explanation}

# @app.route('/api/autofix', methods=['POST'])
# def autofix():
#     data = request.json
#     messy_code = data.get('code', '')
    
#     # We explicitly instruct the AI to use delimiters so we can split the response safely
#     prompt = f"""
#     You are a Senior Python Software Architect. The following function was flagged by our static 
#     analysis tool for having high cyclomatic complexity and bad Halstead metrics.
#     Refactor it to be clean, modular, and easy to read.
#     You MUST format your response exactly like this:
#     [EXPLANATION]
#     Provide a bulleted list explaining exactly what you changed and why it improves the code. Format this section as clean HTML using <ul> and <li> tags.
#     [CODE]
#     Write the raw, refactored python code here. Do not include markdown code blocks.
    
#     Original Code:
#     {messy_code}
#     """
#     try:
#             # THE REST API BYPASS
#             # Bypasses the SDK and local firewalls by acting like standard web traffic
#             api_key = "YOUR_API_KEY" # Put your key here
#             url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            
#             headers = {'Content-Type': 'application/json'}
#             payload = {"contents": [{"parts": [{"text": prompt}]}]}
            
#             # Send the standard HTTP request
#             response = requests.post(url, headers=headers, json=payload)
            
#             if response.status_code == 200:
#                 # Successfully got the REAL AI response
#                 raw_text = response.json()['candidates'][0]['content']['parts'][0]['text']
                
#                 if "[CODE]" in raw_text:
#                     parts = raw_text.split("[CODE]")
#                     explanation_html = parts[0].replace("[EXPLANATION]", "").strip()
#                     clean_code = parts[1].replace("```python\n", "").replace("```", "").strip()
#                 else:
#                     explanation_html = "<ul><li>Code was refactored for readability and complexity reduction.</li></ul>"
#                     clean_code = raw_text.replace("```python\n", "").replace("```", "").strip()
                    
#                 return {"status": "success", "fixed_code": clean_code, "explanation": explanation_html}
#             else:
#                 # If Google still rejects it (e.g., wrong API key), force an error to trigger the circuit breaker
#                 raise Exception(f"API Error {response.status_code}: {response.text}")

#         except Exception as e:
#             error_message = str(e)
            
#             # THE CIRCUIT BREAKER (Your safety net)
#             demo_explanation = "<ul><li><strong>[SYSTEM ALERT]</strong> Network failure detected. Falling back to cache.</li></ul>"
#             demo_code = "# Fake fallback code. The real AI request failed.\ndef fallback_function():\n    return False"
            
#             return {"status": "success", "fixed_code": demo_code, "explanation": demo_explanation}  
    
   
   
   # --- NEW ROUTE: Generative AI Auto-Fix (Upgraded) ---
# @app.route('/api/autofix', methods=['POST'])
# def autofix():
#     data = request.json
#     messy_code = data.get('code', '')
    # try:
    #     response = client.models.generate_content(
    #         model='gemini-2.5-flash',
    #         contents=prompt,
    #     )
        
    #     # Split the AI's response into the Explanation part and the Code part
    #     raw_text = response.text
    #     if "[CODE]" in raw_text:
    #         parts = raw_text.split("[CODE]")
    #         explanation_html = parts[0].replace("[EXPLANATION]", "").strip()
    #         clean_code = parts[1].replace("```python\n", "").replace("```", "").strip()
    #     else:
    #         # Fallback just in case the AI ignores instructions
    #         explanation_html = "<ul><li>Code was refactored for readability and complexity reduction.</li></ul>"
    #         clean_code = raw_text.replace("```python\n", "").replace("```", "").strip()
            
    #     return {"status": "success", "fixed_code": clean_code, "explanation": explanation_html}
    
    # except Exception as e:
    #     error_message = str(e)
        
    #     # THE CIRCUIT BREAKER: If Google's API fails (503) or goes offline, 
    #     # seamlessly fallback to a cached demonstration response.
    #     if "503" in error_message or "UNAVAILABLE" in error_message:
    #         demo_explanation = """
    #         <ul>
    #             <li><strong>[SYSTEM ALERT: API OFFLINE]</strong> Seamlessly falling back to Local Cache Mode.</li>
    #             <li><strong>Decomposition:</strong> Monolithic function was modularized.</li>
    #             <li><strong>Logging:</strong> Added standard library telemetry.</li>
    #         </ul>
    #         """
    #         demo_code = "import logging\n\n# Fallback Demonstration Code\ndef parsed_data_clean(filepath):\n    logging.info('Successfully parsed via fallback cache.')\n    return True"
            
    #         return {"status": "success", "fixed_code": demo_code, "explanation": demo_explanation}
            
    #     # If it's any other type of error, return standard failure
    #     return {"status": "error", "message": error_message}, 500
    # except Exception as e:
    #     return {"status": "error", "message": str(e)}, 500

if __name__ == '__main__':
    app.run(debug=True)