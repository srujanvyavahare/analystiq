import os
import json

REGISTRY_FILE = "registry/metrics.json"

def load_metrics() -> dict:
    if not os.path.exists(REGISTRY_FILE):
        return {}
    with open(REGISTRY_FILE, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def save_metric(name: str, definition: str):
    metrics = load_metrics()
    metrics[name] = definition
    os.makedirs(os.path.dirname(REGISTRY_FILE), exist_ok=True)
    with open(REGISTRY_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

def delete_metric(name: str):
    metrics = load_metrics()
    if name in metrics:
        del metrics[name]
        with open(REGISTRY_FILE, "w") as f:
            json.dump(metrics, f, indent=2)

def get_metrics_prompt() -> str:
    metrics = load_metrics()
    if not metrics:
        return ""
        
    prompt = "\nBUSINESS METRIC DEFINITIONS (YOU MUST USE THESE EXACT DEFINITIONS):\n"
    for name, definition in metrics.items():
        prompt += f"- {name}: {definition}\n"
    return prompt
