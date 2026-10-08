import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re
import traceback
import io
import contextlib

# Dangerous keywords and patterns
FORBIDDEN_KEYWORDS = [
    r'\bos\b', r'\bsys\b', r'\bsubprocess\b', r'\bshutil\b', r'\bpathlib\b',
    r'\b__import__\b', r'\beval\b', r'\bexec\b', r'\bopen\b', r'\bbuiltins\b',
    r'\bglobals\b', r'\blocals\b', r'\bgetattr\b', r'\bsetattr\b', r'\bdelattr\b',
    r'\b__class__\b', r'\b__bases__\b', r'\b__subclasses__\b', r'\b__dict__\b',
    r'\b__dir__\b', r'\b__file__\b', r'\b__name__\b', r'\b__package__\b',
    r'\brequests\b', r'\burllib\b', r'\bhttp\b', r'\bftp\b', r'\bsocket\b'
]

class SecurityError(Exception):
    pass

def check_security(code: str) -> bool:
    """Check code against regex patterns for security."""
    for pattern in FORBIDDEN_KEYWORDS:
        if re.search(pattern, code):
            raise SecurityError(f"Security violation: Forbidden keyword or pattern detected matching '{pattern}'.")
    return True

def execute_code(code: str, df: pd.DataFrame):
    """
    Execute generated pandas code in a sandboxed environment.
    """
    try:
        check_security(code)
    except SecurityError as e:
        return {"success": False, "error": str(e), "traceback": ""}
    
    # Restrict execution namespace
    safe_globals = {
        'pd': pd,
        'plt': plt,
        'px': px,
        'go': go,
        'np': np,
        '__builtins__': {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'range': range,
            'set': set,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
            'print': print,
            'Exception': Exception,
            'ValueError': ValueError,
            'TypeError': TypeError,
            'KeyError': KeyError,
            'IndexError': IndexError,
            'round': round
        }
    }
    
    # Inject the dataframe into locals so the code can access it directly as `df`
    safe_locals = {'df': df}
    
    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        try:
            # We want to execute the code and extract the result.
            exec(code, safe_globals, safe_locals)
        except Exception as e:
            error_trace = traceback.format_exc()
            return {"success": False, "error": str(e), "traceback": error_trace}
            
    return {
        "success": True,
        "locals": safe_locals,
        "stdout": stdout_capture.getvalue()
    }
