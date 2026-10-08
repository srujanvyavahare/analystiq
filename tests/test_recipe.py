import os
import tempfile
import pandas as pd
from core.recipe import save_recipe, list_recipes, apply_recipe

def test_recipe_lifecycle():
    import core.recipe
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch RECIPES_DIR
        original_dir = core.recipe.RECIPES_DIR
        core.recipe.RECIPES_DIR = tmpdir
        
        messages = [
            {"role": "user", "content": "test"},
            {
                "role": "assistant", 
                "code": "result_df = df.copy()\nresult_df['new_col'] = 1",
                "assumptions": {"columns_used": ["existing_col"]}
            }
        ]
        
        # Save
        path = save_recipe("Test Recipe", messages)
        assert os.path.exists(path)
        
        # List
        recipes = list_recipes()
        assert len(recipes) == 1
        assert recipes[0]["name"] == "Test Recipe"
        assert "existing_col" in recipes[0]["required_columns"]
        
        # Apply success
        df = pd.DataFrame({"existing_col": [1]})
        res = apply_recipe(recipes[0], df)
        assert res["success"] == True
        assert "new_col" in res["results"][0]["result_df"].columns
        
        # Apply failure (schema drift)
        df_bad = pd.DataFrame({"wrong_col": [1]})
        res_bad = apply_recipe(recipes[0], df_bad)
        assert res_bad["success"] == False
        assert "Schema drift detected" in res_bad["error"]
        
        core.recipe.RECIPES_DIR = original_dir
