import os
import json
import time
from datetime import datetime
import requests

# רשימת מודלים פופולריים ומרכזיים שעליהם נריץ בדיקת Latency ומהירות פעילה
PRIORITY_MODELS_TO_BENCHMARK = [
    "openai/gpt-4o-mini",
    "anthropic/claude-3.5-haiku",
    "meta-llama/llama-3.3-70b-instruct",
    "google/gemini-flash-1.5"
]

def fetch_openrouter_models():
    """
    שליפת רשימת המודלים והמחירים העדכניים ישירות מ-OpenRouter API.
    """
    url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json().get("data", [])
        
        models = []
        for item in data:
            model_id = item.get("id")
            pricing = item.get("pricing", {})
            
            prompt_price_per_token = float(pricing.get("prompt", 0))
            completion_price_per_token = float(pricing.get("completion", 0))
            
            input_price_per_mtok = prompt_price_per_token * 1_000_000
            output_price_per_mtok = completion_price_per_token * 1_000_000
            
            provider = model_id.split("/")[0].capitalize() if "/" in model_id else "Other"
            
            models.append({
                "provider": provider,
                "model_id": model_id,
                "input_price_per_mtok": round(input_price_per_mtok, 4),
                "output_price_per_mtok": round(output_price_per_mtok, 4),
                "context_length": item.get("context_length", 0),
                "tokens_per_sec": 0,  # ערך ברירת מחדל
                "latency_ms": 0       # ערך ברירת מחדל
            })
            
        return models
    except Exception as e:
        print(f"Error fetching from OpenRouter: {e}")
        return []

def run_live_probe(model_id, api_key):
    """
    מריץ קריאת בדיקה קצרה (Probe) למדידת Latency אמיתי ומהירות (Tokens/sec)
    """
    if not api_key:
        return 0, 0
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/ai-arbitrage-matrix",
        "X-Title": "AI Arbitrage Matrix"
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Reply with the exact word: OK"}],
        "max_tokens": 5
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        end_time = time.time()
        
        latency_ms = int((end_time - start_time) * 1000)
        
        if response.status_code == 200:
            res_data = response.json()
            usage = res_data.get("usage", {})
            completion_tokens = usage.get("completion_tokens", 1)
            
            duration = end_time - start_time
            tokens_per_sec = round(completion_tokens / max(duration, 0.01), 2)
            
            return tokens_per_sec, latency_ms
    except Exception as e:
        print(f"Probe failed for {model_id}: {e}")
        
    return 0, 0

def calculate_task_costs(model):
    """
    חישוב עלות אמיתית ל-1,000 משימות טיפוסיות
    """
    in_price = model["input_price_per_mtok"]
    out_price = model["output_price_per_mtok"]
    
    tech_summary = (8000 / 1e6 * in_price) + (500 / 1e6 * out_price)
    code_review = (3000 / 1e6 * in_price) + (1500 / 1e6 * out_price)
    structured_extraction = (1500 / 1e6 * in_price) + (300 / 1e6 * out_price)
    
    return {
        "tech_summary_cost_per_1k": round(tech_summary * 1000, 4),
        "code_review_cost_per_1k": round(code_review * 1000, 4),
        "structured_extraction_cost_per_1k": round(structured_extraction * 1000, 4)
    }

def main():
    print("Fetching live model prices from OpenRouter...")
    raw_models = fetch_openrouter_models()
    
    if not raw_models:
        print("No models fetched. Exiting.")
        return

    # שליפת מפתח ה-API מתוך משתני הסביבה של השרת
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if api_key:
        print("API Key found. Running live latency & speed probes on priority models...")
    else:
        print("No OPENROUTER_API_KEY found. Skipping live probes.")

    matrix = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_models": len(raw_models),
        "models": []
    }
    
    for m in raw_models:
        model_id = m["model_id"]
        
        # אם זה מודל עדיפות ויש מפתח API, נריץ בדיקה חיה
        if api_key and model_id in PRIORITY_MODELS_TO_BENCHMARK:
            print(f"Probing {model_id}...")
            tps, lat = run_live_probe(model_id, api_key)
            m["tokens_per_sec"] = tps
            m["latency_ms"] = lat
            time.sleep(1) # השהייה קטנה בין קריאות
            
        m["tasks"] = calculate_task_costs(m)
        matrix["models"].append(m)
        
    filename = "ai_arbitrage_matrix.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully updated {filename} with live benchmark data!")

if __name__ == "__main__":
    main()
