import google.generativeai as genai
import os
import json
import re

def configure_llm():
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key.strip())
    else:
        print("WARNING: GEMINI_API_KEY is not set.")

def get_insights_and_code(question: str, df_info: str, retries=3, previous_code=None, error_msg=None, model_name="gemini-3.6-flash", temperature=0.2, user_overrides=None):
    """
    Calls the LLM to generate code and insights.
    Returns a dictionary with 'python_code', 'insights', and 'assumptions'.
    """
    try:
        model = genai.GenerativeModel(model_name)
        
        override_text = ""
        if user_overrides:
            override_text = f"\nUSER CORRECTIONS TO YOUR PREVIOUS ASSUMPTIONS:\n{user_overrides}\nYou MUST apply these corrections to your new code and interpretation."

        from core.registry import get_metrics_prompt
        metrics_text = get_metrics_prompt()

        prompt = f"""
You are a Conversational Data Analyst AI.
I have a pandas DataFrame named `df` with the following schema and sample data:
{df_info}
{metrics_text}
{override_text}

The user just sent this message: "{question}"

STEP 1: INTENT CLASSIFICATION
Does the user's message ask a specific question about the dataset or request a data manipulation/visualization?
- If the message is a simple greeting (like "hello", "hi"), a casual chat, or completely unrelated to analyzing the dataset, YOU MUST NOT write any code and MUST NOT analyze the data.
- In this case, you must set `"needs_plot": false`, `"python_code": ""`, and your `insights` should just be a polite conversational response (e.g., "Hello! I am your AI Data Analyst. What would you like to know about your data?").

STEP 2: DATA ANALYSIS (ONLY if the user is asking about the data)
Determine if a visualization (chart, plot, graph) is requested or helpful.
- If the user explicitly says "no plot", "don't give visualization", or asks a simple factual question ("What is the total revenue?"), set `"needs_plot": false`.
- If a visualization is needed, set `"needs_plot": true`.

When writing Python code (only for data questions):
- The code MUST assume `df` is already loaded.
- DO NOT import dangerous modules (os, sys). Use pd, plt, px, go, np.
- If `needs_plot` is true, store the final figure in a variable named `fig` (DO NOT use plt.show() or fig.show()).
- Store the relevant data subset in a variable named `result_df`.

IMPORTANT TONE RULES for `insights`:
- Speak naturally and conversationally, like a professional human data analyst.
- NEVER mention internal variables like `result_df`, `fig`, "Python", or "processing overhead".
- The first item in the `insights` array should directly answer the user's question or summarize the finding in plain English.
"""
        if previous_code and error_msg:
             prompt += f"""
PREVIOUS CODE FAILED:
{previous_code}

ERROR:
{error_msg}

Please fix the code and return the correct version.
"""

        prompt += """
Respond ONLY with a JSON object in this exact format, with no markdown formatting outside the JSON:
{
    "needs_plot": true/false,
    "python_code": "your python code here as a string",
    "insights": ["conversational answer / insight 1", "insight 2"],
    "assumptions": {
        "columns_used": ["List exact column names from the dataset you are using"],
        "inferred_mapping": {"user_term": "actual_column_name"},
        "interpretation": "Plain English explanation of how you interpreted ambiguous terms (e.g., 'last quarter' -> 'Q3 2026')",
        "filters_applied": "Plain English list of filters applied to the data"
    }
}
"""

        response = model.generate_content(prompt, generation_config={"temperature": temperature})
        text = response.text
        
        # Clean up the response to extract JSON
        text = text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
        
        text = text.strip()
        
        result = json.loads(text)
        return result
    except Exception as e:
        return {"error": str(e)}
