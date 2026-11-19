from sentiment_service import analyze_sentiment, analyze_aspects

def test_positive_review():
    label, score = analyze_sentiment("Excellent product, great quality and works perfectly.")
    assert label == "Positive"

def test_negative_review():
    label, score = analyze_sentiment("Terrible quality, broken and disappointing.")
    assert label == "Negative"

def test_neutral_review():
    label, score = analyze_sentiment("The item arrived yesterday.")
    assert label == "Neutral"

def test_aspects():
    found = analyze_aspects("The battery drains quickly and delivery was late.")
    assert "battery" in found
    assert "delivery" in found
