"""
Step 2: Health Score Calculator
- Takes normalized product data
- Outputs weighted score (0-100) with grade and breakdown
- Works even when Nutriscore/NOVA are missing by calculating from raw nutrients
"""

from app.models.product import NormalizedProduct, ScoreBreakdown

NOVA_SCORES = {1: 25, 2: 18, 3: 10, 4: 0}
NUTRISCORE_SCORES = {"A": 40, "B": 32, "C": 20, "D": 10, "E": 0}

HARMFUL_ADDITIVES = {
    "en:e102", "en:e104", "en:e110", "en:e120", "en:e122",
    "en:e123", "en:e124", "en:e129", "en:e131", "en:e132",
    "en:e210", "en:e211", "en:e212", "en:e213", "en:e214",
    "en:e215", "en:e216", "en:e217", "en:e218", "en:e219",
    "en:e249", "en:e250", "en:e251", "en:e252",
    "en:e951", "en:e950", "en:e952", "en:e954", "en:e955",
    "en:e621",
    "en:e319", "en:e320", "en:e321",
    "en:e150d",
}

CAUTION_ADDITIVES = {
    "en:e407", "en:e412", "en:e415", "en:e466",
    "en:e471", "en:e472",
    "en:e500", "en:e501", "en:e503",
}

# Nutrient thresholds per 100g
NUTRIENT_THRESHOLDS = {
    "sugars_100g":        {"low": 5,   "high": 22.5, "bad": True},
    "fat_100g":           {"low": 3,   "high": 17.5, "bad": True},
    "saturated-fat_100g": {"low": 1.5, "high": 5,    "bad": True},
    "salt_100g":          {"low": 0.3, "high": 1.5,  "bad": True},
    "sodium_100g":        {"low": 0.1, "high": 0.6,  "bad": True},
    "energy-kcal_100g":   {"low": 100, "high": 400,  "bad": True},
    "fiber_100g":         {"low": 1.5, "high": 4.5,  "bad": False},
    "proteins_100g":      {"low": 3,   "high": 10,   "bad": False},
}


def _nutriscore_score(product: NormalizedProduct) -> float:
    """
    Max 40 points.
    If Nutriscore grade is available, use it directly.
    Otherwise calculate from raw nutrients.
    """
    grade = product.nutriscore
    if grade and grade.upper() in NUTRISCORE_SCORES:
        return float(NUTRISCORE_SCORES[grade.upper()])

    # --- Calculate from raw nutrients when grade is missing ---
    nutrients = product.nutrients
    if not nutrients:
        return 20.0  # truly unknown

    score = 40.0

    # Penalty for bad nutrients being high
    bad = [
        ("sugars_100g", 12),
        ("saturated-fat_100g", 10),
        ("salt_100g", 8),
        ("energy-kcal_100g", 6),
    ]
    for key, max_penalty in bad:
        n = nutrients.get(key)
        if n and n.value is not None:
            t = NUTRIENT_THRESHOLDS[key]
            if n.value >= t["high"]:
                score -= max_penalty
            elif n.value >= (t["low"] + t["high"]) / 2:
                score -= max_penalty * 0.5

    # Bonus for good nutrients
    for key, bonus in [("fiber_100g", 5), ("proteins_100g", 5)]:
        n = nutrients.get(key)
        if n and n.value is not None:
            t = NUTRIENT_THRESHOLDS[key]
            if n.value >= t["high"]:
                score += bonus
            elif n.value >= t["low"]:
                score += bonus * 0.5

    return round(max(0.0, min(40.0, score)), 1)


def _nova_score(product: NormalizedProduct) -> float:
    """
    Max 25 points.
    If NOVA group is available, use it.
    Otherwise estimate from number of additives.
    """
    group = product.nova_group
    if group and group in NOVA_SCORES:
        return float(NOVA_SCORES[group])

    # --- Estimate from additives count ---
    additive_count = len(product.additives)
    if additive_count == 0:
        # Could be NOVA 1 or 2 — check ingredients count
        ing_count = len(product.ingredients_list)
        if ing_count <= 3:
            return 22.0   # likely minimally processed
        elif ing_count <= 8:
            return 16.0
        else:
            return 10.0
    elif additive_count <= 2:
        return 10.0   # some additives → likely NOVA 3
    elif additive_count <= 5:
        return 5.0    # many additives → likely NOVA 4
    else:
        return 0.0    # ultra-processed


def _additives_score(product: NormalizedProduct) -> float:
    """Max 20 points. Penalise harmful/caution additives."""
    score = 20.0
    for additive in product.additives:
        code = additive.code.lower()
        if code in HARMFUL_ADDITIVES:
            score -= 5
        elif code in CAUTION_ADDITIVES:
            score -= 2
    return round(max(0.0, score), 1)


def _nutrient_score(product: NormalizedProduct) -> float:
    """Max 15 points based on nutrient risk levels."""
    nutrients = product.nutrients
    if not nutrients:
        return 7.5  # unknown → half

    score = 15.0

    # Penalties for bad nutrients
    bad_deductions = {
        "sugars_100g": 3.5,
        "fat_100g": 2.0,
        "saturated-fat_100g": 3.0,
        "salt_100g": 2.5,
        "sodium_100g": 2.0,
        "energy-kcal_100g": 1.5,
    }
    for key, max_deduct in bad_deductions.items():
        n = nutrients.get(key)
        if n and n.value is not None:
            t = NUTRIENT_THRESHOLDS[key]
            if n.value >= t["high"]:
                score -= max_deduct
            elif n.value >= (t["low"] + t["high"]) / 2:
                score -= max_deduct * 0.4

    # Bonuses for good nutrients
    for key, bonus in [("fiber_100g", 2.0), ("proteins_100g", 2.0)]:
        n = nutrients.get(key)
        if n and n.value is not None:
            t = NUTRIENT_THRESHOLDS[key]
            if n.value >= t["high"]:
                score += bonus
            elif n.value >= t["low"]:
                score += bonus * 0.5

    return round(max(0.0, min(15.0, score)), 1)


def _grade(score: float) -> str:
    if score >= 85:
        return "A+"
    elif score >= 70:
        return "A"
    elif score >= 55:
        return "B"
    elif score >= 40:
        return "C"
    elif score >= 25:
        return "D"
    else:
        return "F"


def _summary(grade: str) -> str:
    summaries = {
        "A+": "Excellent choice! Outstanding nutritional quality with minimal processing and no harmful additives.",
        "A":  "Good choice. Scores well on nutrition, processing level, and additive safety.",
        "B":  "Decent product. A few areas of moderate concern but generally acceptable.",
        "C":  "Average product. Consider moderating consumption — notable nutritional or additive concerns.",
        "D":  "Poor health profile. Highly processed, harmful additives, or poor nutritional value.",
        "F":  "Not recommended. Serious health concerns across multiple categories.",
    }
    return summaries.get(grade, "Health score calculated.")


def calculate_health_score(product: NormalizedProduct) -> ScoreBreakdown:
    ns  = _nutriscore_score(product)
    nv  = _nova_score(product)
    ads = _additives_score(product)
    nut = _nutrient_score(product)
    total = round(ns + nv + ads + nut, 1)
    grade = _grade(total)

    return ScoreBreakdown(
        nutriscore_score=ns,
        nova_score=nv,
        additives_score=ads,
        nutrient_score=nut,
        total=total,
        grade=grade,
        summary=_summary(grade)
    )


def get_flagged_additives(product: NormalizedProduct) -> list[str]:
    flagged = []
    for a in product.additives:
        code = a.code.lower()
        if code in HARMFUL_ADDITIVES or code in CAUTION_ADDITIVES:
            flagged.append(a.name)
    return flagged


def get_harmful_ingredients(product: NormalizedProduct) -> list[str]:
    harmful = get_flagged_additives(product)
    for key in ["sugars_100g", "saturated-fat_100g", "salt_100g"]:
        n = product.nutrients.get(key)
        if n and n.level == "high":
            readable = key.replace("_100g", "").replace("-", " ").title()
            harmful.append(f"High {readable}")
    return harmful