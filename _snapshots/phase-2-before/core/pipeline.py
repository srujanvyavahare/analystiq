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
    max_retries: int = 2
) -> Dict[str, Any]:
    """
    Executes the full LLM analysis and code execution loop, isolated from Streamlit UI.
    """
    result = get_insights_and_code(prompt_text, df_info, model_name=model_name, temperature=temperature)
    
    if "error" in result:
        return {"success": False, "error": result['error'], "code": ""}
        
    code = result.get('python_code', '')
    insights = result.get('insights', [])
    
    fig = None
    res_df = None
    final_code = code
    
    if code:
        success = False
        exec_res = None
        
        for attempt in range(max_retries + 1):
            exec_res = execute_code(code, df)
            if exec_res['success']:
                success = True
                final_code = code
                break
            else:
                if attempt < max_retries:
                    # Retry generating code
                    retry_result = get_insights_and_code(
                        prompt_text, 
                        df_info, 
                        previous_code=code, 
                        error_msg=exec_res['error'],
                        model_name=model_name,
                        temperature=temperature
                    )
                    code = retry_result.get('python_code', '')
        
        if success:
            locals_dict = exec_res['locals']
            fig = locals_dict.get('fig')
            res_df = locals_dict.get('result_df')
        else:
            return {
                "success": False, 
                "error": f"Failed to execute code after retries. Last Error: {exec_res['error']}",
                "code": final_code
            }
            
    return {
        "success": True,
        "code": final_code,
        "insights": insights,
        "fig": fig,
        "result_df": res_df
    }
