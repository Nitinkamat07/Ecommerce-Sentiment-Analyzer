# System Architecture

## Component diagram

```mermaid
flowchart TD
    A[Customer / Admin Browser] --> B[Flask Routes and Jinja Templates]
    B --> C[Authentication and Role Checks]
    B --> D[Product Catalogue and Search]
    B --> E[Session Cart and Simulated Checkout]
    B --> F[Review Submit / Edit]
    C --> G[(SQLite Database via SQLAlchemy)]
    D --> G
    E --> G
    F --> H[Sentiment Service]
    H --> I[VADER if installed]
    H --> J[Lexicon fallback if VADER unavailable]
    I --> K[Sentiment label and score]
    J --> K
    F --> L[Keyword-based Aspect Matcher]
    K --> G
    L --> G
    G --> M[Admin Analytics and Review Filters]
    M --> N[Chart.js Visualizations]
```

## Review submission and edit flow

```mermaid
flowchart TD
    A[Customer submits review form] --> B{Authenticated customer?}
    B -- No --> C[Redirect to login]
    B -- Yes --> D[Validate review text and rating]
    D --> E{Input valid?}
    E -- No --> F[Show validation message]
    E -- Yes --> G[Find review for this user and product]
    G --> H[Run sentiment analysis and aspect matching]
    H --> I{Existing review found?}
    I -- Yes --> J[Update existing review row]
    I -- No --> K[Insert new review row]
    J --> L[Commit database changes]
    K --> L
    L --> M[Show result and refresh product page]
```

## Main components

- `app.py`: Flask routes, SQLAlchemy models, authentication, product/cart/order logic, review create-or-update flow, admin authorization, analytics, and seed data.
- `sentiment_service.py`: VADER sentiment classification with a local lexicon fallback, plus keyword-based aspect hints.
- `templates/`: Jinja-based pages for the catalogue, product details, authentication, cart, orders, errors, and admin analytics.
- `static/css/style.css`: application styling.
- `tests/test_sentiment.py`: basic unit tests for positive, negative, and neutral labels and aspect matching.
- `shop.db`: SQLite database created by the application at runtime.

## Data integrity and security notes

- Passwords are stored using Werkzeug password hashing.
- Admin routes use a role-checking decorator.
- A unique database constraint on `(product_id, user_id)` enforces one review per user per product.
- Review submission validates body length and rating values.
- The current project is for local demonstration. Before public deployment, configure a strong secret key, review CSRF protections and form security, and run behind a production WSGI server.
