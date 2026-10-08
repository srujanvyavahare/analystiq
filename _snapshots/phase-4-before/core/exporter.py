import json
import pandas as pd
import base64
import io

def generate_python_script(messages, filename="data.csv"):
    safe_filename = filename.replace('\\', '/')
    script = [
        "import pandas as pd",
        "import matplotlib.pyplot as plt",
        "import plotly.express as px",
        "import plotly.graph_objects as go",
        "import numpy as np",
        "",
        f"df = pd.read_csv('{safe_filename}')",
        "result_df = df.copy()",
        "fig = None",
        ""
    ]
    
    for msg in messages:
        if msg["role"] == "user":
            script.append(f"\n# QUESTION: {msg['content']}")
        elif msg["role"] == "assistant" and msg.get("code"):
            script.append(msg["code"])
            
    return "\n".join(script)

def generate_notebook(messages, filename="data.csv"):
    safe_filename = filename.replace('\\', '/')
    cells = [
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "import plotly.express as px\n",
                "import numpy as np\n",
                f"df = pd.read_csv('{safe_filename}')\n",
                "result_df = df.copy()\n",
                "fig = None"
            ]
        }
    ]
    
    current_q = ""
    for msg in messages:
        if msg["role"] == "user":
            current_q = msg['content']
            cells.append({
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"### Question: {current_q}"]
            })
        elif msg["role"] == "assistant":
            if msg.get("assumptions"):
                assumptions_text = f"**Interpretation:** {msg['assumptions'].get('interpretation', '')}\n\n**Filters:** {msg['assumptions'].get('filters_applied', '')}"
                cells.append({
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [assumptions_text]
                })
            
            if msg.get("code"):
                cells.append({
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": [line + "\n" for line in msg["code"].split("\n")]
                })
                
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    return json.dumps(notebook, indent=2)

def generate_html_report(messages, filename="data.csv"):
    html = [
        "<html><head>",
        "<title>AnalystIQ Report</title>",
        "<style>",
        "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; color: #333; }",
        ".card { border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }",
        ".question { font-weight: bold; font-size: 1.2em; color: #1E40AF; border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 15px; }",
        ".insights { background: #f8f9fa; padding: 15px; border-left: 4px solid #3B82F6; margin: 10px 0; }",
        ".code { background: #2d2d2d; color: #f8f8f2; padding: 15px; border-radius: 5px; overflow-x: auto; font-family: monospace; }",
        "</style>",
        "</head><body>",
        f"<h1>Data Analysis Report</h1><p>Dataset: <code>{filename}</code></p>"
    ]
    
    for msg in messages:
        if msg["role"] == "user":
            html.append(f"<div class='card'><div class='question'>Q: {msg['content']}</div>")
        elif msg["role"] == "assistant":
            if msg.get("insights"):
                html.append("<div class='insights'><ul>")
                for insight in msg["insights"]:
                    html.append(f"<li>{insight}</li>")
                html.append("</ul></div>")
                
            if msg.get("code"):
                html.append("<div><strong>Code Executed:</strong></div>")
                html.append(f"<pre class='code'><code>{msg['code']}</code></pre>")
                
            html.append("</div>") # close card
            
    html.append("</body></html>")
    return "\n".join(html)
