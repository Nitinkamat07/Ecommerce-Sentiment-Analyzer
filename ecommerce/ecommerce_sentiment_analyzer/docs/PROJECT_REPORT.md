# Project Report: AI-Powered E-Commerce Website with Customer Review Sentiment Analysis

## 1. Abstract

This project is a web-based e-commerce demonstration that integrates automatic sentiment analysis into the customer product-review workflow. Customers can browse a product catalogue, search and filter products, manage a session-based shopping cart, place simulated orders, and submit product reviews. Each review is classified as **Positive**, **Neutral**, or **Negative**. Customers can edit their existing review for a product, and the sentiment and aspect hints are recalculated after an edit. An administrator can inspect review statistics, filter reviews, view product-level summaries, and re-analyse stored reviews.

The application is implemented with Python and Flask. SQLAlchemy manages relational data stored in SQLite. The sentiment service uses VADER when the dependency is available and otherwise uses a small rule/lexicon-based fallback. The system is intended as an educational prototype, not a production commerce platform.

## 2. Problem Statement

E-commerce websites can accumulate many free-text reviews. Reading every review manually is time-consuming, while star ratings alone may not reveal the tone of the written feedback. A lightweight system that assigns sentiment labels and summarizes reviews can help a user quickly inspect the general tone of customer feedback.

## 3. Objectives

1. Build a functional e-commerce demonstration with product browsing and product detail pages.
2. Provide customer registration, login, and password hashing.
3. Store products, users, reviews, orders, and order items in a relational database.
4. Classify review text into positive, neutral, or negative sentiment.
5. Enforce one review per user per product while allowing the user to edit that review.
6. Recalculate sentiment and keyword-based aspect hints when a review is submitted or edited.
7. Provide an admin dashboard with sentiment totals, percentages, product comparisons, filters, and re-analysis.
8. Test the baseline sentiment service and document its limitations honestly.

## 4. Technology Stack

- **Language:** Python
- **Web framework:** Flask
- **Templates/UI:** Jinja templates, HTML, CSS, Bootstrap-based styling, JavaScript
- **Database:** SQLite
- **ORM:** Flask-SQLAlchemy / SQLAlchemy
- **Authentication:** Flask-Login
- **Password security:** Werkzeug password hashing
- **Sentiment analysis:** VADER when installed; local lexicon fallback otherwise
- **Charts:** Chart.js loaded in the admin dashboard
- **Testing:** pytest

## 5. System Modules

### 5.1 Product catalogue
The home page displays seeded demonstration products. Users can search by product name, filter by category, sort the catalogue, and open product detail pages.

### 5.2 Authentication
Customers can register and log in using a username or email. Passwords are stored as hashes rather than plain text. Administrative routes are protected by a role check.

### 5.3 Cart and simulated checkout
The shopping cart is stored in the Flask session. Users can adjust quantities within the displayed stock limit and place a demonstration order. No payment gateway or real payment processing is implemented.

### 5.4 Review management
A signed-in customer can submit a review with a star rating and review text. Review text must be between 5 and 1,200 characters, and the rating must be from 1 to 5. A database unique constraint on `(product_id, user_id)` enforces one review per account per product. If that review already exists, the product page loads it into the form and a new submission updates the existing row rather than creating a duplicate.

### 5.5 Sentiment analysis
The review text is sent to `sentiment_service.py`. If VADER is installed, the service uses its compound score and thresholds:
- Positive: compound score greater than or equal to 0.05
- Negative: compound score less than or equal to -0.05
- Neutral: otherwise

If VADER cannot be imported, a small local word lexicon counts positive and negative terms and applies simple negation handling. This fallback is transparent and suitable only for demonstration. It is not a trained, domain-specific machine-learning model.

### 5.6 Aspect hints
The aspect analyser checks for keywords associated with topics such as quality, price/value, delivery, battery, performance, design, and comfort. This is keyword matching, not a trained aspect-based sentiment model, and a mention does not necessarily mean the sentiment toward that aspect is positive or negative.

### 5.7 Admin analytics
The admin dashboard displays user, product, and review totals; sentiment counts and percentages; a chart of sentiment distribution; product-level sentiment counts; products with a high share of negative reviews; aspect keyword mentions; and a review explorer with sentiment/product filters. An administrator can re-run the sentiment and aspect analysis on stored reviews.

## 6. Architecture and Data Flow

1. The customer or administrator interacts with the browser UI.
2. Flask routes validate requests and apply authentication/authorization checks.
3. SQLAlchemy reads and writes the SQLite database.
4. When a review is submitted or edited, the route calls the sentiment and aspect functions.
5. The predicted label, score, and keyword-based aspect list are saved with the review.
6. The admin dashboard aggregates stored review records and renders charts and tables.

See `ARCHITECTURE.md` for a Mermaid flow diagram.

## 7. Database Design

- **User:** username, email, password hash, admin flag, creation time.
- **Product:** name, category, description, price, image URL, stock.
- **Review:** product, user, rating, review body, sentiment label, sentiment score, aspect hints, creation/update timestamp.
- **Order:** customer, total, creation time.
- **OrderItem:** order, product, saved product name, quantity, and unit price.

The review table uses a unique constraint on the combination of product and user IDs so that a user cannot create multiple review rows for the same product.

## 8. Testing and Evaluation

The included pytest suite checks four baseline behaviours:
1. A clearly positive review receives the Positive label.
2. A clearly negative review receives the Negative label.
3. A neutral factual review receives the Neutral label.
4. Text mentioning battery and delivery produces the corresponding aspect hints.

These tests check expected behaviour for a few examples. They do **not** establish general model accuracy, and they do not cover every route or database workflow. A formal evaluation should use a labeled product-review dataset with a held-out test set and report accuracy, precision, recall, F1-score, and a confusion matrix. Do not claim an accuracy figure unless that evaluation has been carried out.

## 9. Limitations

- VADER is a general-purpose rule-based sentiment tool, not a model trained specifically on this project's product reviews.
- The local fallback uses a small lexicon and simple negation handling.
- Sarcasm, mixed opinions, context, domain-specific expressions, and complex negation can cause incorrect predictions.
- Aspect hints are based on keyword matching and do not assign independent sentiment to each aspect.
- Checkout is simulated; no real payment is processed.
- The application uses Flask's development server and a demonstration secret-key fallback. It is not configured for public production deployment.
- Product images and Chart.js are loaded from remote URLs and may require internet access.

## 10. Future Enhancements

1. Train and evaluate a domain-specific classifier using a labeled product-review dataset.
2. Compare a TF-IDF plus Logistic Regression baseline with VADER and, if feasible, a pretrained transformer.
3. Implement aspect-level sentiment analysis rather than keyword-only aspect hints.
4. Add pagination, moderation, and helpfulness voting for reviews.
5. Add automated integration tests for registration, authorization, duplicate-review handling, editing, and dashboard aggregation.
6. Use environment-based secrets, CSRF protection on all forms, a production WSGI server, and secure deployment configuration before any public deployment.

## 11. Conclusion

The project demonstrates how a web application can combine basic e-commerce workflows with automatic review sentiment labeling and an administrative summary dashboard. The one-review-per-user-per-product rule and edit workflow prevent duplicate review rows while allowing feedback to be updated and re-analysed. The current sentiment and aspect components are intentionally lightweight baselines. Their limitations should be included in the presentation, and the project should not be described as a custom-trained AI model unless a separate training and evaluation stage is completed.
