import pandas as pd
from typing import Dict, Any
from utils.llm import get_insights_and_code
from utils.sandbox import execute_code

def run_analysis_pipeline(
    prompt_text: str, 
    df: pd.DataFrame, 
    df_info: str, 
    model_name: str = "gemini-3.6-flash", 
    temperature: float = 0.2, 
    max_retries: int = 2,
    user_overrides: str = None
) -> Dict[str, Any]:
    """
    Executes the full LLM analysis and code execution loop.
    """
    result = get_insights_and_code(prompt_text, df_info, model_name=model_name, temperature=temperature, user_overrides=user_overrides)
    
    if "error" in result:
        return {"success": False, "error": result['error'], "code": ""}
        
    code = result.get('python_code', '')
    insights = result.get('insights', [])
    assumptions = result.get('assumptions', {})
    
    fig = None
    res_df = None
    final_code = code
    execution_facts = {}
    confidence_reason = []
    confidence = "Green"
    
    if code:
        success = False
        exec_res = None
        rows_in = len(df)
        nulls_in = df.isnull().sum().to_dict()
        
        for attempt in range(max_retries + 1):
            exec_res = execute_code(code, df)
            if exec_res['success']:
                success = True
                final_code = code
                if attempt > 0:
                    confidence = "Red"
                    confidence_reason.append("Code required automatic retry to execute.")
                break
            else:
                if attempt < max_retries:
                    retry_result = get_insights_and_code(
                        prompt_text, 
                        df_info, 
                        previous_code=code, 
                        error_msg=exec_res['error'],
                        model_name=model_name,
                        temperature=temperature,
                        user_overrides=user_overrides
                    )
                    code = retry_result.get('python_code', '')
        
        if success:
            locals_dict = exec_res['locals']
            fig = locals_dict.get('fig')
            res_df = locals_dict.get('result_df')
            
            # Calculate execution facts deterministically
            if res_df is not None and isinstance(res_df, (pd.DataFrame, pd.Series)):
                rows_out = len(res_df) if isinstance(res_df, pd.DataFrame) else len(res_df.dropna())
                execution_facts['rows_in'] = rows_in
                execution_facts['rows_out'] = rows_out
                
                rows_dropped = rows_in - rows_out
                if rows_dropped > 0:
                    pct_dropped = (rows_dropped / rows_in) * 100
                    execution_facts['dropped_pct'] = pct_dropped
                    
                    if pct_dropped > 50:
                        confidence = "Red"
                        confidence_reason.append(f"Filtered out >50% of source rows ({pct_dropped:.1f}% dropped).")
                    elif pct_dropped > 10:
                        if confidence != "Red": confidence = "Amber"
                        confidence_reason.append(f"Excluded {pct_dropped:.1f}% of source rows.")
                        
                if rows_out < 30:
                    confidence = "Red"
                    confidence_reason.append(f"Result based on small sample (<30 rows: {rows_out}).")
                    
                # Phase 5: Statistical Guardrails
                from core.guardrails import run_statistical_guardrails
                guardrail_warnings = run_statistical_guardrails(df, res_df)
                
                for w in guardrail_warnings:
                    if w["level"] == "Red":
                        confidence = "Red"
                    elif w["level"] == "Amber" and confidence != "Red":
                        confidence = "Amber"
                    confidence_reason.append(f"GUARDRAIL ({w['level']}): {w['message']}")
                    
        else:
            return {
                "success": False, 
                "error": f"Failed to execute code after retries. Last Error: {exec_res['error']}",
                "code": final_code
            }
            
    # Amber triggers
    if assumptions.get("inferred_mapping"):
        if confidence != "Red": confidence = "Amber"
        confidence_reason.append(f"Inferred column mappings: {assumptions.get('inferred_mapping')}")
        
    return {
        "success": True,
        "code": final_code,
        "insights": insights,
        "assumptions": assumptions,
        "execution_facts": execution_facts,
        "confidence": confidence,
        "confidence_reason": confidence_reason,
        "fig": fig,
        "result_df": res_df
    }
