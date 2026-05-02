# occasion_nlp.py  — Groq-powered occasion classifier
# ─────────────────────────────────────────────────────────────────────
#  Replaces spaCy + TF-IDF with a single Groq llama3-8b call.
#  Return shape is IDENTICAL to the old version so nothing else changes.
#
#  classify_occasion(message) → {
#      occasion, label, icon, confidence, method, alternatives
#  }
# ─────────────────────────────────────────────────────────────────────

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Occasion metadata (used everywhere else — do not remove) ──────────
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

# ── System prompt for Groq ────────────────────────────────────────────
_SYSTEM_PROMPT = """You are an occasion classifier for an Indian e-commerce fashion app.

Given a user message, identify which occasion they are dressing for.

Valid occasions (use ONLY these keys):
- job_interview  : interview, placement, corporate meeting, office presentation
- sports         : gym, workout, running, cricket, football, yoga, hiking
- wedding_guest  : wedding, shaadi, reception, sangeet, engagement, ethnic function
- casual_outing  : hangout, mall, movie, coffee, friends, weekend outing, college
- date_night     : date, dinner, romantic evening, anniversary
- office         : daily office, work, 9-to-5, business casual, WFH
- festival       : diwali, holi, eid, puja, navratri, garba, cultural celebration
- beach          : beach, vacation, trip, goa, resort, travel, hill station

Respond with ONLY valid JSON — no explanation, no markdown, no extra text:
{
  "occasion":     "<key or null>",
  "confidence":   <0.0 to 1.0>,
  "alternatives": [
    {"occasion": "<key>", "confidence": <float>},
    {"occasion": "<key>", "confidence": <float>}
  ]
}

Rules:
- confidence 0.9-1.0 : very clear match (e.g. "job interview tomorrow")
- confidence 0.6-0.89 : good match (e.g. "going to the gym")
- confidence 0.3-0.59 : possible match (e.g. "something nice to wear out")
- confidence 0.1-0.29 : weak / ambiguous
- confidence 0.0      : purely a product search, no occasion (e.g. "blue jeans under 2000")
- occasion = null     : when message is a product search, not an occasion
- alternatives        : next 2 most likely occasions (empty list if none)
"""


def classify_occasion(user_message: str) -> dict:
    """
    Classify the occasion in user_message using Groq llama3-8b.

    Returns dict with keys:
        occasion, label, icon, confidence, method, alternatives
    Same shape as old spaCy version — nothing else needs to change.
    """
    try:
        resp = groq_client.chat.completions.create(
            model='llama-3.1-8b-instant',       # fast + cheap — perfect for classification
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": user_message.strip()},
            ],
            temperature=0.0,              # deterministic classification
            max_tokens=200,
        )

        raw = resp.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)

        occasion    = data.get("occasion")
        confidence  = float(data.get("confidence", 0.0))
        raw_alts    = data.get("alternatives", [])

        # validate occasion key
        if occasion not in VALID_OCCASIONS:
            occasion   = None
            confidence = 0.0

        # build alternatives list in same shape as old version
        alternatives = []
        for alt in raw_alts[:2]:
            key = alt.get("occasion")
            if key in VALID_OCCASIONS and key != occasion:
                alternatives.append({
                    "occasion": key,
                    "label":    OCCASION_LABELS[key],
                    "icon":     OCCASION_ICONS[key],
                    "score":    round(float(alt.get("confidence", 0)), 2),
                })

        return {
            "occasion":     occasion,
            "label":        OCCASION_LABELS.get(occasion, "") if occasion else "",
            "icon":         OCCASION_ICONS.get(occasion, "🛍️") if occasion else "🛍️",
            "confidence":   round(confidence, 2),
            "method":       "groq",
            "alternatives": alternatives,
        }

    except Exception as e:
        print(f"[occasion_nlp] Groq classify error: {e}")
        # fallback — return null occasion so unified route uses general path
        return {
            "occasion":     None,
            "label":        "",
            "icon":         "🛍️",
            "confidence":   0.0,
            "method":       "groq_error",
            "alternatives": [],
        }


# ── Quick test ────────────────────────────────────────────────────────
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
        "blue jeans under 2000",        # should return null occasion
        "Nike sports shoes",            # should return null occasion
    ]
    for t in tests:
        r = classify_occasion(t)
        print(
            f"  [{r['icon']} {r['label'] or 'General'}] "
            f"conf={r['confidence']} | {t}"
        )