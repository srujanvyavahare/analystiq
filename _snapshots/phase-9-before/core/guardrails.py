import pandas as pd
import numpy as np

def run_statistical_guardrails(df: pd.DataFrame, result_df) -> list:
    warnings = []
    
    if result_df is None:
        return warnings
        
    if isinstance(result_df, pd.Series):
        result_df = result_df.to_frame()
        
    if not isinstance(result_df, pd.DataFrame):
        return warnings

    # 1. Sample Size Check
    if len(result_df) > 0 and len(result_df) < 30:
        warnings.append({
            "level": "Red",
            "message": f"Small sample size ({len(result_df)} rows). Results may not be statistically significant."
        })

    # 2. Outlier / Skew Check (Mean vs Median)
    num_cols = result_df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        col_data = result_df[col].dropna()
        if len(col_data) > 2:
            mean_val = col_data.mean()
            median_val = col_data.median()
            if median_val != 0:
                diff = abs((mean_val - median_val) / median_val)
                if diff > 0.2:
                    warnings.append({
                        "level": "Amber",
                        "message": f"Column '{col}' is highly skewed (Mean: {mean_val:.2f}, Median: {median_val:.2f}). Outliers may be distorting this result."
                    })
                    
    # 3. Missing Data Check in results
    if len(result_df) > 0:
        nulls = result_df.isnull().sum() / len(result_df)
        for col, pct in nulls.items():
            if pct > 0.2:
                warnings.append({
                    "level": "Amber",
                    "message": f"Column '{col}' in the result has {pct*100:.0f}% missing values."
                })
                
    # 4. Simpson's Paradox / Correlation Reversal (Basic heuristic)
    if len(result_df) < len(df) and len(result_df) > 5 and set(num_cols).issubset(set(df.columns)):
        for i in range(len(num_cols)):
            for j in range(i+1, len(num_cols)):
                col1, col2 = num_cols[i], num_cols[j]
                
                if df[col1].std() > 0 and df[col2].std() > 0 and result_df[col1].std() > 0 and result_df[col2].std() > 0:
                    orig_corr = df[col1].corr(df[col2])
                    new_corr = result_df[col1].corr(result_df[col2])
                    
                    if (orig_corr > 0.3 and new_corr < -0.3) or (orig_corr < -0.3 and new_corr > 0.3):
                        warnings.append({
                            "level": "Amber",
                            "message": f"Correlation between '{col1}' and '{col2}' reversed in this subset (Potential Simpson's Paradox)."
                        })

    return warnings
