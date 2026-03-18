## LuxeStore — Ecommerce backend (Django)

This repository contains the **backend** for an ecommerce platform built with **Django 5.2** + PostgreSQL + Redis, with payments, shipping integrations, async background jobs, and a heavily customized admin dashboard.

## 1) Auth + OTP (email verification & password reset)

- **Authentication**
  - Django sessions auth
  - Custom email authentication backend: `authenticate.authentication.EmailAuthBackend`
  - Google OAuth2 login using `social-auth-app-django` (includes `associate_by_email` pipeline step)
- **OTP (Redis-backed)**
  - OTPs are **securely generated**, then **hashed (SHA-256)** and stored in Redis (`otp:<email>:<purpose>`)
  - **TTL**: ~5 minutes
  - **Rate limiting**: blocks repeated requests for ~2 minutes
  - **Max attempts**: 3 attempts stored and enforced in Redis
  - Sending OTP email is done asynchronously via Celery (`send_email.delay(...)`)
- **i18n**
  - English/Arabic support via `LocaleMiddleware` + `i18n_patterns`
  - OTP pages/messages are localized

## 2) Database (PostgreSQL)

- PostgreSQL as primary DB (`django.db.backends.postgresql`)
- Postgres features used:
  - `django.contrib.postgres`
  - Trigram extension migrations for fuzzy search (`TrigramExtension`)
  - GIN indexes for Arabic/English name/description fields (trigram ops)

## 3) Cache + sessions + Redis

- **Django cache on Redis** via `django-redis`
- **Redis-backed sessions** (Django sessions stored in cache)
- **Direct Redis usage** via `ecommerce/redis_client.py`:
  - OTP storage + rate limiting
  - “Bought together” recommendations (sorted sets) in `store/recommendation.py`

## 4) Pagination + search

- **Pagination**
  - Page-based pagination with Django `Paginator` (`store/search.py`)
  - Custom **cursor pagination** helper (`store/cursor_pagination.py`)
- **Search**
  - Postgres trigram similarity ranking for better fuzzy search (`store/search.py`)
  - Filtering with `django-filter` (`store/filters.py`) for price/category/tags/stock and more

## 5) Background jobs: Celery + broker (RabbitMQ/Redis)

- Celery app config: `ecommerce/celery.py`
- Implemented tasks:
  - OTP email sending with retries (`authenticate/tasks.py`)
  - Invoice PDF generation and email sending (`payment/tasks.py`)
  - Bulk invoices generation + background stock release for abandoned payments (`order/tasks.py`)
- The broker URL is expected via environment (common: RabbitMQ `amqp://...` using `CELERY_BROKER_URL`).

## 6) Cart + orders

- Session-backed cart (`CART_SESSION_ID = 'cart'`)
- Order lifecycle with background cancellation/stock release
- Invoices as PDFs (WeasyPrint), both immediate and async

## 7) Payments + shipping

- **Stripe**
  - Checkout session creation
  - Webhook endpoint wired in project URLs
  - After-payment flow updates order + triggers invoice + recommendations
- **Paymob**
  - Intention / unified checkout flow
  - Webhook endpoint wired in project URLs
- **Bosta shipping integration**
  - Cached lookups: cities/zones/districts
  - Pricing calculator
  - Delivery creation flow (`order/shipping.py`)

## Admin & back-office (Unfold + custom tooling)

- Unfold-powered admin theme + customizations
- **Custom analytics dashboard** mounted at `/admin/`:
  - KPI cards + multiple charts (Chart.js)
  - Deep links into filtered admin changelists
  - RTL-aware rendering for Arabic
- Store admin productivity:
  - Variant group management + “Add Variant” shortcut (clone flow)
  - Bulk discount admin action with a custom form/template
  - Low-stock filter
- Orders admin productivity:
  - Inline order items + shipping address
  - CSV export
  - Bulk invoice generation (async) tracked via `PdfFile`

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

