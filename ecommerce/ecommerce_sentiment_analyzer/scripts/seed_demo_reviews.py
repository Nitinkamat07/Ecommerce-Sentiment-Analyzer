
import os
import sys
import random
import uuid

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from app import app, db, Product, User, Review
from sentiment_service import analyze_aspects

TARGET = 50

POSITIVE = [
    "Really happy with the quality and finish.",
    "Worth the money and performs better than expected.",
    "The product feels premium for this price.",
    "Good purchase for everyday use.",
    "Impressed with the overall build quality.",
    "Works as described and looks great.",
    "A useful product with good value for money.",
    "The design is attractive and practical.",
    "Very satisfied with the performance so far.",
    "Quality is better than I expected.",
    "Packaging was neat and the product arrived safely.",
    "Good experience overall. No major complaints.",
    "Easy to use and feels well made.",
    "A solid choice at this price point.",
    "The product matches the description nicely.",
    "Happy with the features and overall finish.",
    "Good performance for regular daily use.",
    "Looks stylish and feels durable.",
    "Quite pleased with this purchase.",
    "A practical product that does its job well.",
    "The quality and price are well balanced.",
    "Everything works properly so far.",
    "I would consider buying this brand again.",
    "Simple to use and delivers what it promises.",
    "The product exceeded my initial expectations.",
    "Nice finish and a satisfying overall experience.",
    "Good packaging and a product worth considering.",
    "It has been convenient to use regularly.",
    "The features are useful and easy to understand.",
    "A good purchase for the price paid.",
]

NEUTRAL = [
    "The product is as described in the listing.",
    "Quality is average for this price range.",
    "It performs the basic functions adequately.",
    "The design is simple and fairly standard.",
    "Received the expected product and accessories.",
    "The appearance matches the listing photographs.",
    "It is usable for ordinary everyday requirements.",
    "The packaging was standard.",
    "Features are similar to other products in this category.",
    "The size and finish are as expected.",
    "It does the basic job without anything unusual.",
    "The product information is mostly accurate.",
    "Performance seems reasonable so far.",
    "The design is functional rather than distinctive.",
    "Overall, it is an average product.",
    "The product arrived in acceptable condition.",
    "Setup was straightforward.",
    "It meets my basic requirements.",
    "The materials and finish seem standard.",
    "Nothing particularly special about the product.",
    "The features are adequate for normal use.",
    "It looks similar to other products I have seen.",
    "The product works, but my experience is limited.",
    "The quality seems consistent with the price.",
    "It has the expected features and appearance.",
    "The product is neither exceptional nor disappointing.",
    "The overall experience has been ordinary.",
    "It serves its intended purpose.",
    "I need more time to judge long-term durability.",
    "A fairly standard option in this category.",
]

NEGATIVE = [
    "Disappointed with the quality at this price.",
    "The product feels cheaper than expected.",
    "Not worth the amount I paid.",
    "The finish could have been much better.",
    "Performance has been inconsistent.",
    "Expected better quality from this product.",
    "The overall experience was disappointing.",
    "Some features are not as convenient as expected.",
    "Build quality does not feel very durable.",
    "I am not satisfied with this purchase.",
    "The product did not meet my expectations.",
    "The quality does not justify the price.",
    "Not a great experience for everyday use.",
    "The design looks better in the pictures.",
    "I expected a more premium finish.",
    "The product feels overpriced.",
    "There is plenty of room for improvement.",
    "The performance has been underwhelming.",
    "I would compare other options before buying again.",
    "The product is less impressive than advertised.",
    "Not particularly happy with the quality.",
    "The materials feel rather basic.",
    "The experience has not been as smooth as expected.",
    "The product could be more reliable.",
    "The value for money is not very convincing.",
    "I expected better attention to detail.",
    "The product has been frustrating to use.",
    "The finish and performance need improvement.",
    "I am unsure I would purchase this again.",
    "Overall, this was a disappointing purchase.",
]

OPENINGS = [
    "Honestly,",
    "In my experience,",
    "For the price,",
    "After using it for a few days,",
    "From my initial impression,",
    "Compared with my expectations,",
    "One thing I noticed is that",
    "Looking at the overall experience,",
    "Having tried this product,",
    "For everyday use,",
    "After trying it at home,",
    "My overall impression is that",
]

ENDINGS = [
    "This is my honest opinion.",
    "That is my experience so far.",
    "Hope this helps other shoppers.",
    "These are my observations after trying it.",
    "This is based on my personal experience.",
    "I considered both quality and price.",
    "That is how I feel about this purchase.",
    "Other buyers may have a different experience.",
    "This is my overall impression.",
    "Sharing my feedback for other buyers.",
]

RATING_POOLS = {
    "Positive": [4, 4, 4, 5, 5, 5, 5, 3],
    "Neutral": [2, 3, 3, 3, 3, 4, 4],
    "Negative": [1, 1, 1, 2, 2, 2, 3],
}

BANKS = {
    "Positive": POSITIVE,
    "Neutral": NEUTRAL,
    "Negative": NEGATIVE,
}


def make_review(product_name, sentiment, index):
    phrases = BANKS[sentiment]
    phrase = phrases[index % len(phrases)]

    # Vary sentence structure and wording.
    opening = OPENINGS[(index * 7) % len(OPENINGS)]
    ending = ENDINGS[(index * 3 + len(product_name)) % len(ENDINGS)]

    return f"{opening} {product_name}: {phrase} {ending}"


with app.app_context():
    products = Product.query.order_by(Product.id).all()

    if not products:
        print("No products found. Add products before running this script.")
        sys.exit(1)

    # Remove previous demo reviews only.
    old_demo_users = User.query.filter(
        User.username.like("demo_p%")
    ).all()

    old_demo_ids = [user.id for user in old_demo_users]

    if old_demo_ids:
        Review.query.filter(
            Review.user_id.in_(old_demo_ids)
        ).delete(synchronize_session=False)

        for user in old_demo_users:
            db.session.delete(user)

        db.session.commit()
        print("Removed previous demo reviews.")

    total_added = 0

    for item in products:
        product_id = item.id
        product_name = item.name

        print(f"\nGenerating reviews for: {product_name}")

        # Prepare reviews for every sentiment before inserting.
        review_jobs = []

        for sentiment in ("Positive", "Neutral", "Negative"):
            for i in range(TARGET):
                review_jobs.append({
                    "sentiment": sentiment,
                    "body": make_review(product_name, sentiment, i),
                })

        # Shuffle all sentiments together.
        random.shuffle(review_jobs)

        for job in review_jobs:
            sentiment = job["sentiment"]
            body = job["body"]

            token = uuid.uuid4().hex[:12]
            username = f"demo_p{product_id}_{token}"

            user = User(
                username=username,
                email=f"{username}@example.test",
            )
            user.set_password(uuid.uuid4().hex)

            db.session.add(user)
            db.session.flush()

            rating = random.choice(RATING_POOLS[sentiment])

            review = Review(
                product_id=product_id,
                user_id=user.id,
                rating=rating,
                body=body,
                sentiment=sentiment,
                sentiment_score={
                    "Positive": 0.8,
                    "Neutral": 0.0,
                    "Negative": -0.8,
                }[sentiment],
                aspects=", ".join(analyze_aspects(body)),
            )

            db.session.add(review)
            total_added += 1

        db.session.commit()

        print(f"Inserted {len(review_jobs)} shuffled reviews.")

    print("\n========== REVIEW COUNTS ==========")

    for item in Product.query.order_by(Product.id).all():
        print(f"\n{item.name}")

        for sentiment in ("Positive", "Neutral", "Negative"):
            count = Review.query.filter_by(
                product_id=item.id,
                sentiment=sentiment,
            ).count()

            print(f"  {sentiment}: {count}")

    print(f"\nTotal new reviews: {total_added}")
    print("Finished successfully!")
    print("Refresh your browser using Ctrl + F5.")
