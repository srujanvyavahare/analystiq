import os
import tempfile
import subprocess
import pandas as pd
from core.exporter import generate_python_script, generate_notebook, generate_html_report

def test_python_export_runs():
    messages = [
        {"role": "user", "content": "What is the total sum?"},
        {"role": "assistant", "code": "result_df = df['val'].sum()", "insights": ["Sum is 15"]}
    ]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "data.csv")
        pd.DataFrame({"val": [5, 10]}).to_csv(csv_path, index=False)
        
        script_code = generate_python_script(messages, filename=csv_path)
        script_path = os.path.join(tmpdir, "analysis.py")
        
        # Add a print statement to verify output
        script_code += "\nprint(result_df)\n"
        
        with open(script_path, "w") as f:
            f.write(script_code)
            
        # Run it in a subprocess without GEMINI_API_KEY
        env = os.environ.copy()
        if "GEMINI_API_KEY" in env:
            del env["GEMINI_API_KEY"]
            
        result = subprocess.run(
            ["python", script_path], 
            capture_output=True, 
            text=True, 
            env=env
        )
        
        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "15" in result.stdout

def test_notebook_export_format():
    messages = [{"role": "user", "content": "test"}, {"role": "assistant", "code": "print(1)"}]
    nb_json = generate_notebook(messages)
    assert '"cell_type": "code"' in nb_json
    assert 'print(1)' in nb_json

def test_html_export_format():
    messages = [{"role": "user", "content": "test"}, {"role": "assistant", "code": "print(1)"}]
    html = generate_html_report(messages)
    assert 'Q: test' in html
    assert 'print(1)' in html
