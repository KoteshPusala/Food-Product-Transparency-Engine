import os
import json
from groq import Groq
from app.models.product import AIAnalysis

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


async def analyze_product(product, score, pubchem_data, papers):
    try:
        content = f"""
You are a food safety expert.

Analyze the product "{product.name}".

Ingredients:
{product.ingredients_list}

Health Score:
{score}

Scientific data (PubChem):
{pubchem_data}

Research papers (PubMed):
{papers}

---

Return STRICTLY valid JSON. Do not include any text outside JSON. Do not miss commas.
Return STRICT JSON. Every array item MUST be separated by commas.

Format:
{{
  "overall_verdict": "Safe | Moderate | Risky",
  "overall_summary": "Detailed 4-5 sentence explanation covering main health risks, key concerning ingredients, whether any ingredients are banned or restricted in any countries, who should avoid this product, and recommended consumption frequency. Minimum 60 words.",

  "ingredient_analyses": [
    {{
      "name": "ingredient name",
      "status": "safe | moderate | harmful",
      "explanation": "short scientific explanation including if this ingredient is banned or restricted in any country (if applicable, mention country name)"
    }}
  ],

  "recommendations": [
    "Clear actionable health advice",
    "Mention moderation or avoidance if needed",
    "Include safer consumption tips"
  ],

  "safer_alternatives": "Suggest safer or healthier alternatives if applicable"
}}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": content}]
        )

        text = response.choices[0].message.content.strip()

        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) > 1:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
            text = text.strip()

        parsed = json.loads(text)

        raw_recommendations = parsed.get("recommendations", [])
        recommendations = []
        for item in raw_recommendations:
            if isinstance(item, str):
                recommendations.append(item)
            elif isinstance(item, dict):
                recommendations.append(
                    item.get("text") or item.get("description") or str(item)
                )

        raw_ingredients = parsed.get("ingredient_analyses", [])
        ingredient_analyses = []
        for item in raw_ingredients:
            if isinstance(item, dict):
                ingredient_analyses.append({
                    "name": item.get("name", ""),
                    "status": item.get("status", "safe"),
                    "explanation": item.get("explanation", "")
                })

        return AIAnalysis(
            overall_verdict=parsed.get("overall_verdict", "Unknown"),
            overall_summary=parsed.get("overall_summary", ""),
            ingredient_analyses=ingredient_analyses,
            recommendations=recommendations,
            safer_alternatives=parsed.get("safer_alternatives"),
        )

    except Exception as e:
        print("❌ GROQ ERROR:", str(e))
        return AIAnalysis(
            overall_verdict="Error",
            overall_summary=f"AI analysis failed: {str(e)}",
            ingredient_analyses=[],
            recommendations=["Try again later"],
            safer_alternatives=None
        )