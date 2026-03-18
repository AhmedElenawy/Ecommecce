# LuxeStore — Ecommerce Backend (Django)

This repository contains the backend infrastructure for a high-performance e-commerce platform built with **Django 5.2**. It is designed for real-world production flows, featuring robust custom authentication, advanced search and filtering, session-based cart management, robust third-party shipping/payment integrations, and a highly customized admin panel.

## System Architecture & Core Infrastructure

* **Framework**: Built on Django 5.2.
* **Database**: Uses PostgreSQL, utilizing `django.contrib.postgres` for advanced features like GIN trigram indexes.
* **Caching & Sessions**: Relies on Redis via `django-redis` and `django.contrib.sessions.backends.cache` for caching and session management.
* **Asynchronous Tasks**: Implements Celery (typically backed by RabbitMQ) for background jobs like handling emails, stock releases, and PDF generation.
* **Localization**: Provides bilingual support for English and Arabic using `django-modeltranslation` and Django's built-in i18n features.
* **Admin Dashboard**: Features a modern, RTL-aware UI powered by the `django-unfold` library.

---

## Application Modules

### `authenticate` (Custom Auth, OTP & Social Login)
* Handles secure user access using a custom `EmailAuthBackend` that replaces standard username login with email.
* Generates secure 6-digit OTPs that are hashed via SHA-256 and stored in Redis with a 5-minute time-to-live (TTL).
* Enforces brute-force protection by tracking and limiting attempts (maximum 3) and applying rate-limiting (2-minute cooldowns) to prevent spam.
* Integrates Google OAuth2 via `social-auth-app-django`, automatically linking social logins to existing email accounts using a custom `associate_by_email` pipeline step.

### `store` (Catalog, Search & Recommendations)
* Implements fuzzy search using PostgreSQL trigram similarity ranking for both English and Arabic content.
* Utilizes a custom base64-encoded cursor pagination system (`cursor_pagination.py`) for highly efficient, scalable data fetching based on created dates or rank.
* Tracks "bought together" items using Redis sorted sets (`zincrby` and `zunionstore` commands) for fast, real-time product recommendations.

### `cart` & `coupon` (Session-Based Shopping & Discounts)
* Binds shopping carts directly to the Django session, which is backed entirely by Redis for low-latency access.
* Validates available stock upon cart iteration, automatically adjusting quantities and alerting users if items sell out while in the cart.
* Enforces granular coupon rules, validating active time windows, general active status, and specific usage limits per user.

### `order` (Checkout & Lifecycle Management)
* Protects the checkout flow using `transaction.atomic()` to lock database rows and prevent race conditions when reducing stock inventory.
* Utilizes a Celery background task (`release_stock`) to automatically cancel pending, abandoned orders after 15 minutes and restore the product stock.
* Dynamically generates individual PDF order invoices using WeasyPrint.

### `shipping` (Logistics & Bosta Integration)
* Provides full integration with the Bosta shipping API for managing Egyptian logistics.
* Caches Bosta cities, zones, and districts in Redis to heavily minimize latency and external API calls.
* Exposes asynchronous API endpoints for the frontend to calculate dynamic shipping rates based on the user's drop-off city.
* Automatically generates Bosta delivery orders with fully structured addresses, including building number, floor, and apartment.

### `payment` (Gateways & Webhooks)
* Integrates both Stripe for Checkout Sessions and Paymob for Unified Checkout flows.
* Automatically converts EGP to USD for Stripe transactions using an external Exchange Rate API, safely caching the rate in Redis for 24 hours.
* Handles asynchronous payment confirmations by validating Paymob webhooks using SHA-512 HMAC signatures.
* Verifies Stripe webhooks securely using Stripe's native signature verification mechanism (`stripe.Webhook.construct_event`).

### Back-Office Admin (`dashboard` & `admin`)
* Features a comprehensive custom dashboard that calculates real-time metrics such as Total Revenue, Average Order Value, Pending Orders, and Active Stock.
* Integrates Chart.js to visually display 7-day revenue trends, order status distributions, and top-selling products.
* Includes custom admin actions to export orders to CSV and trigger asynchronous bulk PDF invoice generation via Celery, tracked via a `PdfFile` model.
* Renders the entire dashboard with RTL awareness to support Arabic localization natively.

---

## Local setup

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment

Copy `.env.example` → `.env` and fill values (never commit `.env`):

```bash
cp .env.example .env
```

### Run

```bash
python manage.py migrate
python manage.py runserver
```

