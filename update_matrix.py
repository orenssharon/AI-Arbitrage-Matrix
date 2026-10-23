import json
from datetime import datetime
import requests

def fetch_openrouter_models():
    """
    שליפת רשימת המודלים והמחירים העדכניים ישירות מ-OpenRouter API.
    המחירון ב-OpenRouter מוחזר כעלות לטוקן בודד, ולכן נמיר אותו לעלות למיליון טוקנים (MToK).
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
            
            # OpenRouter מחזיר מחיר לכל טוקן (מחרוזת או מספר)
            prompt_price_per_token = float(pricing.get("prompt", 0))
            completion_price_per_token = float(pricing.get("completion", 0))
            
            # המרה לעלות למיליון טוקנים (MToK)
            input_price_per_mtok = prompt_price_per_token * 1_000_000
            output_price_per_mtok = completion_price_per_token * 1_000_000
            
            # חילוץ שם הספק מתוך ה-ID (לדוגמה: "openai/gpt-4o" יהפוך ל-"Openai")
            provider = model_id.split("/")[0].capitalize() if "/" in model_id else "Other"
            
            models.append({
                "provider": provider,
                "model_id": model_id,
                "input_price_per_mtok": round(input_price_per_mtok, 4),
                "output_price_per_mtok": round(output_price_per_mtok, 4),
                "context_length": item.get("context_length", 0),
                "tokens_per_sec": 0,  # ערך ברירת מחדל, יתעדכן במודל ה-Benchmarks הבא
                "latency_ms": 0       # ערך ברירת מחדל
            })
            
        return models
    except Exception as e:
        print(f"Error fetching from OpenRouter: {e}")
        return []

def calculate_task_costs(model):
    """
    חישוב עלות אמיתית ל-1,000 משימות טיפוסיות על בסיס מחירי ה-Input וה-Output
    """
    in_price = model["input_price_per_mtok"]
    out_price = model["output_price_per_mtok"]
    
    # 1. סיכום מאמר טכני: 8,000 טוקן קלט, 500 טוקן פלט
    tech_summary = (8000 / 1e6 * in_price) + (500 / 1e6 * out_price)
    
    # 2. ניתוח ותיקון קוד Python: 3,000 טוקן קלט, 1,500 טוקן פלט
    code_review = (3000 / 1e6 * in_price) + (1500 / 1e6 * out_price)
    
    # 3. יצירת פרומפט מובנה / חילוץ נתונים: 1,500 טוקן קלט, 300 טוקן פלט
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

    matrix = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_models": len(raw_models),
        "models": []
    }
    
    for m in raw_models:
        m["tasks"] = calculate_task_costs(m)
        matrix["models"].append(m)
        
    # שמירה לקובץ JSON המרכזי
    filename = "ai_arbitrage_matrix.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully updated {filename} with {len(raw_models)} models!")

if __name__ == "__main__":
    main()
