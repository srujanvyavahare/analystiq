# AnalystIQ 📊

AnalystIQ is a local, privacy-first Conversational Data Analytics platform built with Python, Streamlit, and the Gemini API. 

Designed to compete with commercial tools like Julius AI and ChatGPT Data Analysis, AnalystIQ focuses on **trust**, **reproducibility**, and **zero-LLM deterministic workflows**.

*(Imagine a beautiful GIF of AnalystIQ analyzing data here)*

---

## 🌟 Key Features

*   **Natural Language Analysis:** Upload CSV/Excel and ask plain English questions. AnalystIQ writes, executes, and renders pandas/Plotly code locally.
*   **The Trust Layer:** An AI shouldn't just give you a number. AnalystIQ forces the LLM to declare its *assumptions*, evaluates the final output against *statistical guardrails* (Simpson's Paradox, outlier skew, small samples), and displays deterministic execution facts alongside a Red/Amber/Green confidence score.
*   **Zero-LLM Analysis Recipes:** Save your chat history as a JSON "Recipe" and run it on new datasets instantly. Recipes execute natively without API calls and feature strict schema drift validation.
*   **Reproducible Export:** Export your entire session into a standalone Python script, a Jupyter Notebook, an HTML Report, or a cleaned CSV in one click.
*   **Metric Registry:** Define your company's custom business logic (e.g. `Active User = login within 30 days`) once, and it is permanently injected into the AI's system prompt.
*   **Zero-State Auto-Insights:** Instantly calculates dataset skewness, correlation matrices, missing data, and imbalances via deterministic pandas code on file load, translated into an immediate 5-point brief.

## 🏗️ Architecture Overview

AnalystIQ intentionally separates UI logic from business execution:

*   **`core/pipeline.py` (The Orchestrator):** Manages the retry loop. If the LLM writes broken code, the pipeline feeds the traceback back to the LLM for self-correction before rendering.
*   **`utils/sandbox.py` (The Execution Engine):** Executes LLM-generated code inside a locked-down python `globals()` namespace (regex blocklist to prevent dangerous OS/Sys calls).
*   **`core/guardrails.py` (The Verifier):** Runs deterministic heuristics (mean vs. median skew checks, missing data rates, correlation reversal) against the final output *after* execution.
*   **`core/exporter.py` (The Generator):** Translates Streamlit session state and python strings into fully executable `.py` and `.ipynb` files that do not rely on AnalystIQ to run.

## 🆚 Honest Comparison

| Feature | AnalystIQ | ChatGPT Advanced Data Analysis | Julius AI |
| :--- | :--- | :--- | :--- |
| **Privacy / Local Execution** | **Yes** (Code runs entirely on your local machine) | No (Runs in OpenAI servers) | No (Runs in cloud containers) |
| **Reproducible Code Export** | **Yes** (1-click `.py` and `.ipynb` generation) | Limited (Must copy-paste cells manually) | Yes (Notebook export) |
| **Deterministic Guardrails** | **Yes** (Flags statistical skew & sample sizes) | No | No |
| **LLM Dependency on Re-runs** | **Zero** (Recipes run purely on Pandas) | High (Requires new prompts) | Medium |
| **Custom Metric Registry** | **Yes** (Saved locally, injected into prompts) | No (Requires Custom GPT setup) | No |
| **Chart Interactivity** | High (Plotly native) | Low (Static matplotlib PNGs) | High |
| **Compute Power** | Limited to your local hardware | High (Cloud CPU/RAM) | High (Cloud CPU/RAM) |

## 🚀 Quickstart

1.  **Clone the repository.**
2.  **Install dependencies:** `pip install streamlit pandas numpy plotly google-generativeai`
3.  **Set your API Key:** Export `GEMINI_API_KEY=your_key` in your environment or a `.env` file. (Only required for initial analysis; Recipes and Exports run without it).
4.  **Run the app:**
    ```bash
    streamlit run app.py
    ```

## 🧪 Testing

AnalystIQ includes a robust test suite covering the LLM pipeline, sandboxed execution, recipe validation, and statistical guardrails.

Run the entire suite locally:
```powershell
.\run_checks.ps1
```
