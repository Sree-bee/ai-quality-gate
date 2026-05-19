# AI-Powered Hybrid Static Code Analysis & Refactoring Engine

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Machine Learning](https://img.shields.io/badge/Machine_Learning-Random_Forest-orange.svg)
![Generative AI](https://img.shields.io/badge/GenAI-Gemini_2.5_Flash-10b981.svg)

An enterprise-grade CI/CD quality gate developed as a Master's Thesis Project. This system evolves static analysis from a passive warning system into an intelligent, active remediation partner. It mathematically diagnoses architectural decay, predicts system-level risk using Machine Learning, and autonomously generates surgical code refactoring using Generative AI.

**Author:** Sreehari S | MSc Computer Science, Pondicherry University

---

## Key Features

* **Deep AST Diagnostics:** Parses Python source code into an Abstract Syntax Tree (AST) to extract Halstead complexity and McCabe metrics without executing the code.
* **Cost-Sensitive Machine Learning:** Utilizes a Random Forest Classifier trained on NASA MDP datasets to predict architectural risk. The model is tuned with a 25% probability threshold (Paranoia Level) to maximize the capture of failing architecture.
* **Transitive Risk Mapping:** Features a Two-Pass Infection Engine that calculates Fan-In and Fan-Out dependencies, flagging safe modules that import high-risk dependencies.
* **Generative AI Auto-Fix:** Integrates the Gemini 2.5 Flash LLM to autonomously generate modular, refactored code and Explainable AI (XAI) "Architect's Notes."
* **Enterprise Fault Tolerance:** Engineered with a Circuit Breaker pattern, REST tunneling, and graceful degradation to localized cache during API outages.

---

## Technology Stack
* **Backend:** Python, Flask
* **Machine Learning:** Scikit-Learn, Pandas
* **Generative AI:** Google Gemini 2.5 Flash API
* **Analysis:** Python `ast` module

---

## Installation & Setup

**1. Clone the repository**
```bash
git clone [https://github.com/Sree-bee/ai-quality-gate.git](https://github.com/Sree-bee/ai-quality-gate.git)
cd ai-quality-gate
```
**2. Create a Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```
**3. Install Dependencies**
```bash
pip install -r requirements.txt
```
**4. Set up Environment Variables**
**Create a .env file in the root directory and add your Google Gemini API key:**
```
GEMINI_API_KEY=your_api_key_here
```
**5. Run the Application**
```bash
python app.py
```
**Navigate to http://localhost:5000 in your browser to access the dashboard.**