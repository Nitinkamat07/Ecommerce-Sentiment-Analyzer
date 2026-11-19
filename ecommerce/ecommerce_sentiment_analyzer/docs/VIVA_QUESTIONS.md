# Viva Preparation: AI-Powered E-Commerce Website with Customer Review Sentiment Analysis

## Core project questions

**1. What is the objective of your project?**  
The project demonstrates an e-commerce website that classifies customer review text as Positive, Neutral, or Negative and summarizes the results in an admin dashboard.

**2. What problem does it address?**  
Manually reading many customer reviews is time-consuming. Sentiment labels and summary charts help an administrator inspect the general tone of feedback more quickly.

**3. What technologies did you use?**  
Python, Flask, Jinja templates, HTML/CSS/JavaScript, Flask-SQLAlchemy, SQLite, Flask-Login, Werkzeug password hashing, VADER with a local fallback, Chart.js, and pytest.

**4. What is NLP?**  
Natural Language Processing (NLP) is a field of AI concerned with processing and analyzing human language.

**5. What are the three sentiment classes?**  
Positive indicates favorable wording, Negative indicates unfavorable wording, and Neutral indicates wording that is neither clearly positive nor negative according to the analyzer.

## AI and analysis

**6. Is this a custom-trained AI model?**  
No. The current implementation uses VADER when installed and otherwise uses a small lexicon-based fallback. It is a sentiment-analysis baseline, not a custom model trained on this project's review dataset.

**7. How does VADER classify a review?**  
VADER returns sentiment scores, including a compound score between -1 and +1. This project labels scores greater than or equal to 0.05 as Positive, scores less than or equal to -0.05 as Negative, and values between those thresholds as Neutral.

**8. What happens if VADER is unavailable?**  
The service falls back to a small local positive/negative word lexicon with basic handling of a preceding negation word. The fallback is intentionally simple and less capable than a robust trained model.

**9. What does the sentiment score mean?**  
It is the score returned by the active sentiment method. With VADER it is the compound score. It is not a probability that the label is correct.

**10. What are the limitations of sentiment analysis here?**  
Sarcasm, mixed opinions, domain-specific language, context, and complex negation may be misclassified. A short lexicon fallback can miss many expressions.

**11. What is aspect analysis in this project?**  
It matches keywords to predefined topics such as quality, price/value, delivery, battery, performance, design, and comfort. It only identifies topic mentions; it does not independently classify sentiment for each topic.

**12. How would you evaluate the model properly?**  
Use a labeled review dataset, keep a held-out test set, compare predictions with the human-provided labels, and report accuracy, precision, recall, F1-score, and a confusion matrix. The current four unit tests are not a formal accuracy evaluation.

## Web application and database

**13. Why did you use Flask?**  
Flask is a lightweight Python web framework that provides routes and integrates well with Python libraries.

**14. Why SQLite?**  
SQLite is a relational database stored in a local file, making it easy to set up for a student project without running a separate database server.

**15. How are passwords stored?**  
The application stores password hashes using Werkzeug's password-hashing functions, rather than storing the original passwords.

**16. How is admin access restricted?**  
The admin route uses a decorator that requires the user to be logged in and checks the account's admin flag. Non-admin users receive a 403 response.

**17. How do you prevent duplicate reviews?**  
The database has a unique constraint on the combination of `product_id` and `user_id`. The route also searches for an existing review before saving.

**18. Can a user change a review after submitting it?**  
Yes. The product page loads the user's existing review into the form. On submission, the route updates the same row, recalculates sentiment and aspect hints, and saves the new rating and body.

**19. Why is editing better than inserting another review?**  
It prevents the same account from adding repeated entries for one product while still allowing the customer to correct or update their feedback. It also avoids inflating the review count.

**20. What happens to analytics after a review is edited?**  
The dashboard reads the stored review records. Since editing updates the existing record rather than inserting another one, the total review count stays the same while the sentiment category or rating can change.

**21. Does checkout accept real payments?**  
No. It creates a simulated order and updates the demonstration stock count. No payment gateway is integrated.

**22. How are sentiment percentages calculated?**  
Percentage for a label = (number of reviews with that label / total number of reviews) × 100. If there are no reviews, the displayed percentage is zero.

**23. What are the four automated tests?**  
The included tests check a clearly positive review, a clearly negative review, a neutral factual review, and keyword detection for battery and delivery. They test basic sentiment-service behaviour, not every web route.

**24. What would you improve next?**  
I would add route-level integration tests, evaluate the sentiment approach on a labeled dataset, compare it with a trained TF-IDF plus Logistic Regression model, improve aspect-level analysis, and strengthen security before deployment.

## Demo flow for presentation

1. Open the home page and browse/search the products.
2. Register a customer account and sign in.
3. Open a product and submit a review with a rating.
4. Show the predicted sentiment label and aspect hints.
5. Edit the same review and show that the label is recalculated without adding a duplicate review.
6. Sign in as the demo administrator and open the analytics dashboard.
7. Show the sentiment chart, product comparison, review filters, and re-analysis action.
8. Explain the limitations and clarify that checkout is simulated and the current sentiment service is not a custom-trained model.

## Honest claims to make in the viva

- Say “automatic sentiment classification using VADER with a fallback,” not “a custom deep-learning model.”
- Say “keyword-based aspect hints,” not “trained aspect-based sentiment analysis.”
- Do not quote an accuracy percentage unless you have evaluated a labeled dataset.
- Describe the project as an educational prototype rather than a production-ready online store.
