"""Local review sentiment service.

Uses VADER when installed. A transparent lexicon fallback keeps the demo usable
without a model download. The fallback is educational and should not be treated
as production-grade sentiment analysis.
"""
import re

POSITIVE = {
    "amazing", "awesome", "excellent", "great", "good", "love", "loved", "perfect",
    "best", "fast", "comfortable", "useful", "worth", "recommend", "beautiful",
    "reliable", "smooth", "fantastic", "happy", "impressed", "durable", "easy",
    "clear", "bright", "efficient", "nice", "superb", "works", "wonderful", "value"
}
NEGATIVE = {
    "bad", "terrible", "awful", "poor", "worst", "hate", "hated", "broken", "slow",
    "disappointed", "disappointing", "waste", "cheap", "defective", "damaged",
    "overpriced", "uncomfortable", "issue", "issues", "problem", "problems", "fail",
    "failed", "failure", "noisy", "weak", "drains", "drain", "late", "useless",
    "return", "refund", "fragile", "annoying", "cracked"
}
NEGATIONS = {"not", "never", "no", "isn't", "wasn't", "doesn't", "don't", "didn't", "hardly"}
ASPECTS = {
    "quality": {"quality", "build", "durable", "material", "broken", "fragile"},
    "price/value": {"price", "cost", "expensive", "cheap", "overpriced", "value", "worth"},
    "delivery": {"delivery", "shipping", "arrived", "late", "packaging"},
    "battery": {"battery", "charge", "charging", "drains", "backup"},
    "performance": {"performance", "speed", "fast", "slow", "lag", "works", "responsive"},
    "design": {"design", "look", "looks", "beautiful", "color", "colour", "size"},
    "comfort": {"comfort", "comfortable", "fit", "uncomfortable", "weight", "light"}
}

def analyze_sentiment(text):
    """Return (label, compound_score). Attempts VADER, then uses a local fallback."""
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        scores = SentimentIntensityAnalyzer().polarity_scores(text)
        compound = float(scores["compound"])
        if compound >= 0.05:
            label = "Positive"
        elif compound <= -0.05:
            label = "Negative"
        else:
            label = "Neutral"
        return label, compound
    except ImportError:
        pass

    tokens = re.findall(r"[a-z']+", text.lower())
    pos = neg = 0
    for i, token in enumerate(tokens):
        prev = tokens[i - 1] if i else ""
        if token in POSITIVE:
            if prev in NEGATIONS:
                neg += 1
            else:
                pos += 1
        elif token in NEGATIVE:
            if prev in NEGATIONS:
                pos += 1
            else:
                neg += 1
    total = pos + neg
    score = (pos - neg) / max(total, 1)
    if total == 0 or abs(score) < 0.20:
        return "Neutral", round(score, 3)
    return ("Positive" if score > 0 else "Negative"), round(score, 3)

def analyze_aspects(text):
    tokens = set(re.findall(r"[a-z']+", text.lower()))
    found = [aspect for aspect, keywords in ASPECTS.items() if tokens & keywords]
    return found
