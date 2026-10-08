import pandas as pd
import numpy as np
import google.generativeai as genai
import json

def compute_deterministic_stats(df: pd.DataFrame) -> dict:
    stats = {
        "missing_data": {},
        "correlations": [],
        "imbalances": {},
        "skewness": {}
    }
    
    # Missing
    missing = df.isnull().sum()
    missing = missing[missing > 0]
    if not missing.empty:
        stats["missing_data"] = (missing / len(df) * 100).round(1).to_dict()
        
    # Numeric stats
    num_df = df.select_dtypes(include=[np.number])
    if not num_df.empty:
        if len(num_df.columns) > 1:
            corr = num_df.corr().abs()
            np.fill_diagonal(corr.values, 0)
            c = corr.unstack().dropna()
            if not c.empty:
                c = c.sort_values(ascending=False)
                if c.iloc[0] > 0.5:
                    idx = c.index[0]
                    stats["correlations"].append({
                        "col1": idx[0],
                        "col2": idx[1],
                        "val": round(num_df[idx[0]].corr(num_df[idx[1]]), 2)
                    })
        
        # Skew
        skew = num_df.skew()
        high_skew = skew[skew.abs() > 1.5]
        if not high_skew.empty:
            stats["skewness"] = high_skew.round(2).to_dict()
            
    # Categorical imbalances
    cat_df = df.select_dtypes(exclude=[np.number, 'datetime'])
    for col in cat_df.columns:
        if df[col].nunique() > 0 and df[col].nunique() < 10:
            top_val = df[col].value_counts(normalize=True).iloc[0]
            if top_val > 0.6:
                stats["imbalances"][col] = f"'{df[col].mode()[0]}' makes up {top_val*100:.1f}%"
                
    return stats

def get_auto_insights_brief(stats_dict: dict, model_name: str = "gemini-3.6-flash") -> list:
    # If quota is exhausted or API is down, fallback
    fallback = []
    if stats_dict.get("correlations"):
        c = stats_dict["correlations"][0]
        fallback.append(f"Strong correlation ({c['val']}) between {c['col1']} and {c['col2']}.")
    for k, v in stats_dict.get("imbalances", {}).items():
        fallback.append(f"Column '{k}' is highly imbalanced: {v}.")
    for k, v in stats_dict.get("missing_data", {}).items():
        fallback.append(f"Column '{k}' is missing {v}% of its data.")
        
    if not fallback:
        fallback = ["Dataset appears well-balanced with no extreme skew, missing values, or obvious colinearity."]
        
    try:
        model = genai.GenerativeModel(model_name)
        prompt = f"""
        You are a data analyst. I ran deterministic checks on a dataset and found these statistical facts:
        {stats_dict}
        
        Write exactly 5 short, punchy bullet points translating these facts into plain English insights. 
        Focus on what's interesting. If the facts are empty, provide 3 general observations about what questions could be asked.
        Respond ONLY with a JSON array of strings: ["insight 1", "insight 2", ...]
        """
        response = model.generate_content(prompt)
        text = response.text.strip()
        import re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return fallback
    except Exception as e:
        return fallback # Fallback if quota exhausted
