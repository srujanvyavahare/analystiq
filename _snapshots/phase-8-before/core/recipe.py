import os
import json
import pandas as pd
from utils.sandbox import execute_code

RECIPES_DIR = "recipes"
os.makedirs(RECIPES_DIR, exist_ok=True)

def save_recipe(name: str, messages: list):
    steps = []
    required_cols = set()
    
    current_prompt = ""
    for msg in messages:
        if msg["role"] == "user":
            current_prompt = msg["content"]
        elif msg["role"] == "assistant" and msg.get("code"):
            steps.append({
                "prompt": current_prompt,
                "code": msg["code"]
            })
            if msg.get("assumptions") and msg["assumptions"].get("columns_used"):
                for col in msg["assumptions"]["columns_used"]:
                    required_cols.add(col)
                    
    recipe = {
        "name": name,
        "required_columns": list(required_cols),
        "steps": steps
    }
    
    safe_name = "".join([c if c.isalnum() else "_" for c in name]).lower()
    path = os.path.join(RECIPES_DIR, f"{safe_name}.json")
    with open(path, "w") as f:
        json.dump(recipe, f, indent=2)
        
    return path

def list_recipes():
    recipes = []
    for fname in os.listdir(RECIPES_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(RECIPES_DIR, fname), "r") as f:
                try:
                    recipes.append(json.load(f))
                except Exception:
                    pass
    return recipes

def apply_recipe(recipe: dict, df: pd.DataFrame) -> dict:
    # Schema check
    missing = [col for col in recipe.get("required_columns", []) if col not in df.columns]
    if missing:
        return {"success": False, "error": f"Schema drift detected. Missing required columns: {', '.join(missing)}"}
        
    results = []
    current_df = df
    
    for step in recipe.get("steps", []):
        exec_res = execute_code(step["code"], current_df)
        if exec_res["success"]:
            # Capture outputs
            fig = exec_res["locals"].get("fig")
            res_df = exec_res["locals"].get("result_df")
            results.append({
                "prompt": step["prompt"],
                "code": step["code"],
                "fig": fig,
                "result_df": res_df
            })
        else:
            return {"success": False, "error": f"Error running '{step['prompt']}': {exec_res['error']}"}
            
    return {"success": True, "results": results}
