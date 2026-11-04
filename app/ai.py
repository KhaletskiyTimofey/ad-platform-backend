def evaluate(creative: dict) -> dict:
    headline = (creative.get("headline") or "").lower()
    description = (creative.get("description") or "").lower()
    banned = ["казино", "ставк", "наркотик", "18+"]
    score = 96
    notes = ["Креатив прочитан автоматически"]
    for word in banned:
        if word in headline or word in description:
            return {
                "verdict": "reject",
                "score": 12,
                "notes": [f"Обнаружено запрещённое слово: {word}"],
            }
    if len(description) < 20:
        score = 78
        notes.append("Короткое описание — стоит расширить")
    link = creative.get("link") or ""
    if not link.startswith("https://"):
        score -= 5
        notes.append("Ссылка без HTTPS")
    if score >= 90:
        return {"verdict": "approve", "score": score, "notes": notes}
    return {"verdict": "review", "score": score, "notes": notes}
