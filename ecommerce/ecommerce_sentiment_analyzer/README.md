# AI-Powered E-Commerce Website with Customer Review Sentiment Analysis

A student mini-project combining a Flask e-commerce demo with automatic positive/neutral/negative customer review classification and an admin analytics dashboard.

## Features
- Product catalogue, search, category filter, sorting and product detail pages
- Account registration/login with hashed passwords
- Session shopping cart and simulated checkout (no real payment processing)
- One review per user per product; review sentiment is calculated on submission
- Admin dashboard with sentiment totals, charts, negative-review highlights and re-analysis
- Lightweight aspect keyword insights
- SQLite database and seeded demo products

## Requirements
- Python 3.10+ (Python 3.12 recommended)
- Internet access is only needed to load remote product images; the core app runs locally.
- VADER is used when installed. A small transparent lexicon fallback is included. The fallback is for demonstration, not a production-grade trained model.

## Windows setup (VS Code terminal)
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate again.

## Demo administrator
The first run creates an administrator:
- Email: `admin@shopdemo.local`
- Username: `admin`
- Password: `Admin123!`

Change these values before sharing or deploying the project. You can set `ADMIN_EMAIL`, `ADMIN_PASSWORD`, and `SECRET_KEY` environment variables. These defaults are only for local demonstration.

## How to use
1. Register a normal customer account.
2. Browse a product and add it to the cart.
3. Sign in and submit a review with a rating.
4. The app classifies the review and stores the label.
5. Sign in as the demo admin and open **Analytics**.
6. Inspect sentiment counts and use the re-analyze action.

## Important limitations
- This is a learning/demo project, not a production store.
- Checkout is simulated and does not accept payments.
- The built-in fallback uses a small word lexicon and cannot reliably understand sarcasm, negation scope, mixed opinions or context. VADER is used when installed, but it is still a general-purpose sentiment tool.
- Aspect detection is keyword-based, not a trained aspect-based sentiment model.
- The app uses Flask's development server; do not deploy it as-is to the public internet.
- Remote image URLs may need to be replaced if the image provider changes URLs.

## Project layout
- `app.py` — Flask routes, database models and seed data
- `sentiment_service.py` — sentiment and aspect analysis
- `templates/` — Jinja pages
- `static/css/style.css` — styling
- `static/js/dashboard.js` — charts
- `tests/` — basic automated tests
