# occasion_nlp.py — v3 — Groq + keyword fallback
# Fixes:
#   1. Unicode arrow crash (uses ASCII -> instead of ->)
#   2. Keyword-based pre-classification so common phrases never miss
#   3. Groq confirms/refines — no longer sole classifier
#   4. Confidence boost when keyword + Groq agree
# ─────────────────────────────────────────────────────────────────────

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

OCCASION_LABELS = {
    "job_interview": "Job Interview",
    "sports":        "Sports & Gym",
    "wedding_guest": "Wedding / Function",
    "casual_outing": "Casual Outing",
    "date_night":    "Date Night",
    "office":        "Office & Work",
    "festival":      "Festival & Traditional",
    "beach":         "Beach & Vacation",
}

OCCASION_ICONS = {
    "job_interview": "💼",
    "sports":        "🏃",
    "wedding_guest": "🎊",
    "casual_outing": "☀️",
    "date_night":    "🌙",
    "office":        "🏢",
    "festival":      "🪔",
    "beach":         "🏖️",
}

VALID_OCCASIONS = list(OCCASION_LABELS.keys())

# ── Keyword maps — catches the most common phrases instantly ──────────
KEYWORD_MAP = {
    "job_interview": [
        "interview", "job interview", "placement", "campus placement",
        "hiring", "hr round", "technical round", "corporate", "formal meeting",
        "boardroom", "client meeting", "presentation", "induction",
    ],
    "sports": [
        "gym", "workout", "running", "jogging", "cricket", "football",
        "basketball", "badminton", "tennis", "yoga", "pilates", "cycling",
        "hiking", "trekking", "marathon", "sport", "training", "exercise",
        "fitness", "crossfit", "zumba", "swimming",
    ],
    "wedding_guest": [
        "wedding", "shaadi", "shadi", "baraat", "sangeet", "mehndi",
        "reception", "engagement", "nikah", "function", "ceremony",
        "marriage", "vivah", "mandap", "mehendi",
    ],
    "casual_outing": [
        "hangout", "mall", "shopping", "movie", "cinema", "coffee",
        "cafe", "brunch", "lunch", "college", "friends", "outing",
        "chill", "casual", "weekend", "day out", "picnic", "market",
    ],
    "date_night": [
        "date", "date night", "dinner date", "anniversary", "romantic",
        "valentine", "special evening", "candlelight", "girlfriend",
        "boyfriend", "partner", "impress",
    ],
    "office": [
        "office", "work", "9 to 5", "9-5", "daily wear", "business casual",
        "wfh", "work from home", "workplace", "corporate office", "job",
        "professional", "monday", "weekday",
    ],
    "festival": [
        "diwali", "holi", "eid", "navratri", "garba", "dandiya",
        "puja", "pooja", "durga", "ganesh", "onam", "ugadi", "pongal",
        "baisakhi", "lohri", "makar sankranti", "karva chauth",
        "festival", "celebration", "traditional", "cultural", "ethnic",
    ],
    "beach": [
        "beach", "goa", "vacation", "holiday", "trip", "travel", "resort",
        "pool", "swimming pool", "sea", "ocean", "sunbathe", "sunset",
        "hill station", "trekking trip", "backpacking", "tourist",
    ],
}


def _keyword_classify(message: str) -> tuple[str | None, float]:
    """Fast keyword pre-classifier. Returns (occasion_key, confidence)."""
    text = message.lower().strip()
    scores: dict[str, int] = {}

    for occasion, keywords in KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text:
                scores[occasion] = scores.get(occasion, 0) + (2 if len(kw.split()) > 1 else 1)

    if not scores:
        return None, 0.0

    best = max(scores, key=lambda k: scores[k])
    raw_score = scores[best]

    # scale: 1 match -> 0.6, 2 matches -> 0.75, 3+ -> 0.88
    confidence = min(0.6 + (raw_score - 1) * 0.14, 0.90)
    return best, round(confidence, 2)


_SYSTEM_PROMPT = """You are an occasion classifier for an Indian e-commerce fashion app.

Given a user message, identify which occasion they are dressing for.

Valid occasions (use ONLY these exact keys):
- job_interview  : interview, placement, corporate meeting, office presentation
- sports         : gym, workout, running, cricket, football, yoga, hiking
- wedding_guest  : wedding, shaadi, reception, sangeet, engagement, ethnic function
- casual_outing  : hangout, mall, movie, coffee, friends, weekend outing, college
- date_night     : date, dinner, romantic evening, anniversary
- office         : daily office, work, 9-to-5, business casual, WFH
- festival       : diwali, holi, eid, puja, navratri, garba, cultural celebration
- beach          : beach, vacation, trip, goa, resort, travel, hill station

Respond ONLY with valid JSON — no explanation, no markdown fences:
{
  "occasion":     "<key or null>",
  "confidence":   <0.0 to 1.0>,
  "alternatives": [
    {"occasion": "<key>", "confidence": <float>},
    {"occasion": "<key>", "confidence": <float>}
  ]
}

Rules:
- confidence 0.9-1.0 : very clear (e.g. "job interview tomorrow")
- confidence 0.6-0.89 : good match (e.g. "going to the gym")
- confidence 0.3-0.59 : possible (e.g. "something nice to wear out")
- confidence 0.0-0.29 : weak / ambiguous
- occasion = null : message is a product search only (e.g. "blue jeans under 2000", "Nike shoes")
- alternatives : next 2 most likely (empty list [] if none)
"""


def classify_occasion(user_message: str) -> dict:
    """
    Two-stage classifier:
      Stage 1 — fast keyword match (instant, zero cost)
      Stage 2 — Groq LLM confirmation/refinement
    If Groq fails, keyword result is returned as fallback.
    """
    kw_occasion, kw_confidence = _keyword_classify(user_message)

    try:
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_message.strip()},
            ],
            temperature=0.0,
            max_tokens=200,
        )

        raw  = resp.choices[0].message.content.strip()
        raw  = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)

        groq_occasion    = data.get("occasion")
        groq_confidence  = float(data.get("confidence", 0.0))
        raw_alts         = data.get("alternatives", [])

        if groq_occasion not in VALID_OCCASIONS:
            groq_occasion   = None
            groq_confidence = 0.0

        # ── Fusion logic ──────────────────────────────────────────────
        # If both agree, boost confidence
        if groq_occasion and groq_occasion == kw_occasion:
            final_occasion    = groq_occasion
            final_confidence  = min(max(groq_confidence, kw_confidence) + 0.08, 0.97)
        elif groq_occasion and groq_confidence >= 0.55:
            # Groq is confident — trust it
            final_occasion   = groq_occasion
            final_confidence = groq_confidence
        elif kw_occasion and kw_confidence >= 0.60:
            # Keyword is confident, Groq was unsure — trust keyword
            final_occasion   = kw_occasion
            final_confidence = kw_confidence
        elif groq_occasion:
            # Use Groq result at whatever confidence it gave
            final_occasion   = groq_occasion
            final_confidence = groq_confidence
        else:
            final_occasion   = kw_occasion
            final_confidence = kw_confidence

        alternatives = []
        for alt in raw_alts[:2]:
            key = alt.get("occasion")
            if key in VALID_OCCASIONS and key != final_occasion:
                alternatives.append({
                    "occasion": key,
                    "label":    OCCASION_LABELS[key],
                    "icon":     OCCASION_ICONS[key],
                    "score":    round(float(alt.get("confidence", 0)), 2),
                })

        method = "groq+keyword" if kw_occasion else "groq"

    except Exception as e:
        # Use ASCII for print to avoid cp1252 crash on Windows
        print(f"[occasion_nlp] Groq error: {e} -> falling back to keyword")
        final_occasion   = kw_occasion
        final_confidence = kw_confidence
        alternatives     = []
        method           = "keyword_fallback"

    return {
        "occasion":     final_occasion,
        "label":        OCCASION_LABELS.get(final_occasion, "") if final_occasion else "",
        "icon":         OCCASION_ICONS.get(final_occasion, "🛍️") if final_occasion else "🛍️",
        "confidence":   round(final_confidence or 0.0, 2),
        "method":       method,
        "alternatives": alternatives,
    }


if __name__ == "__main__":
    tests = [
        "I have a job interview tomorrow",
        "going to the gym tonight",
        "my cousin's shaadi next week",
        "casual hangout with friends",
        "date night dinner",
        "diwali celebration",
        "goa trip next month",
        "office daily wear",
        "what should I wear",
        "blue jeans under 2000",
        "Nike sports shoes",
        "baraat outfit",
        "garba night",
        "campus placement",
    ]
    for t in tests:
        r = classify_occasion(t)
        icon  = r["icon"] if r["icon"] else "?"
        label = r["label"] or "General (product search)"
        print(f"  [{icon} {label}] conf={r['confidence']} method={r['method']} | {t}")