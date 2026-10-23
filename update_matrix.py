import json
from datetime import datetime

def fetch_provider_prices():
    # כאן נשלף את המחירונים מה-APIs או דפי התיעוד הרשמיים
    models_data = [
        {
            "provider": "OpenAI",
            "model_id": "gpt-4o-mini",
            "input_price": 0.15,
            "output_price": 0.60,
            "tokens_per_sec": 110,
            "latency_ms": 320
        },
        {
            "provider": "Anthropic",
            "model_id": "claude-3-5-haiku",
            "input_price": 0.80,
            "output_price": 4.00,
            "tokens_per_sec": 140,
            "latency_ms": 290
        }
    ]
    return models_data

def calculate_task_costs(model):
    # משימת סיכום מאמר: 8k input, 500 output
    tech_summary = (8000 / 1e6 * model["input_price"]) + (500 / 1e6 * model["output_price"])
    # משימת קוד: 3k input, 1500 output
    code_review = (3000 / 1e6 * model["input_price"]) + (1500 / 1e6 * model["output_price"])
    
    return {
        "tech_summary_cost_per_1k": round(tech_summary * 1000, 4),
        "code_review_cost_per_1k": round(code_review * 1000, 4)
    }

def main():
    raw_models = fetch_provider_prices()
    matrix = {
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "models": []
    }
    
    for m in raw_models:
        costs = calculate_task_costs(m)
        m["tasks"] = costs
        matrix["models"].append(m)
        
    with open("ai_arbitrage_matrix.json", "w", encoding="utf-8") as f:
        json.dump(matrix, f, indent=2, ensure_ascii=False)
    print("Matrix updated successfully!")

if __name__ == "__main__":
    main()
