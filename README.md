## LuxeStore — Ecommerce backend (Django)

This repository contains the **backend** for an ecommerce platform built with **Django 5.2**, focused on real production flows: authentication + OTP, catalog + search, cart → order → payment, shipping integrations, background jobs, and a heavily customized admin.

The documentation below is organized **by app**, in this order:
`authenticate` → `store` → `cart` → `coupon` → `order` → `payment` → admin → translation.

## `authenticate` app (auth, OTP, social login)

**Technologies used**
- Django auth + sessions
- Redis (direct client) for OTP storage/rate limit (`ecommerce/redis_client.py`)
- Celery for async email sending
- `social-auth-app-django` for Google OAuth2

**Implemented flows**
- **Custom email authentication backend**: `authenticate.authentication.EmailAuthBackend`
- **OTP (email verification / password reset)**
  - Secure 6-digit OTP generation
  - OTP is **hashed (SHA-256)** and stored in Redis under `otp:<email>:<purpose>`
  - **TTL**: ~5 minutes
  - **Rate limiting**: blocks repeated OTP requests (~2 minutes)
  - **Brute-force protection**: max attempts (3), stored in Redis
  - OTP email send is async: `send_email.delay(...)` (with retry policy)
- **Google OAuth2 login**
  - Pipeline includes `associate_by_email` so existing users can be linked by email

## `store` app (catalog, variants, search, filtering, recommendations)

**Technologies used**
- PostgreSQL (`django.contrib.postgres`)
- Postgres trigram search + indexes
- `django-filter` for filtering
- `django-taggit` for tagging
- Redis for “bought together” recommendations (sorted sets)
- `modeltranslation` for bilingual (EN/AR) model fields
- Media handling: Pillow + easy-thumbnails

**Implemented flows**
- **Products, categories, tags**
- **Variants**
  - `ProductVariantGroup` to group variants and compute specs/sales
  - `Product.variant_specifications` stored as JSON
- **Search**
  - Fuzzy search using **trigram similarity** ranking (`store/search.py`)
  - Trigram extension migration + **GIN trigram indexes** for name/description in EN/AR
- **Pagination**
  - Classic Django `Paginator` + custom **cursor pagination** helper
- **Filtering**
  - Price/category/tags/in-stock using `django-filter` (`store/filters.py`)
- **Recommendations**
  - Redis sorted-set based “bought together” tracking + retrieval (`store/recommendation.py`)

## `cart` app (session cart)

**Technologies used**
- Django sessions (stored in Redis cache)
- Redis-backed session engine (`django.contrib.sessions.backends.cache`)

**Implemented flows**
- Session-backed cart with session key `CART_SESSION_ID = 'cart'`

## `coupon` app (discount codes + usage tracking)

**Technologies used**
- Django models + validators
- i18n translations in model fields/messages

**Implemented flows**
- Coupons with:
  - Percentage discount validation
  - Active window (`valid_from` → `valid_to`)
  - `usage_limit` per user enforced via `CouponUsage`
- Coupon validation raises localized errors for invalid cases

## `order` app (orders, addresses, invoices, shipping)

**Technologies used**
- PostgreSQL models + query optimization patterns (`select_related`, `prefetch_related`)
- Celery background tasks
- WeasyPrint for PDF generation
- Django cache (Redis) for shipping lookups
- `django-phonenumber-field` for Egyptian phone validation
- Bosta shipping API integration using `requests`

**Implemented flows**
- **Order lifecycle**
  - Status flow: pending → paid → shipped/delivered or cancelled
  - Background flow to **release stock / cancel abandoned payments** (`order/tasks.py`)
- **Order address**
  - Structured address fields including Bosta IDs (city/zone/district)
- **Invoices**
  - Single invoice PDF generation (WeasyPrint)
  - Bulk invoices generation as a tracked file (`PdfFile`) via Celery
- **Shipping (Bosta)**
  - Cached lookups: cities/zones/districts (cache backed by Redis)
  - Pricing calculator endpoint
  - Delivery creation flow (`order/shipping.py`)

## `payment` app (Stripe + Paymob, webhooks, post-payment automation)

**Technologies used**
- Stripe Python SDK (`stripe`)
- Paymob integration using `requests`
- Django cache (Redis) used for currency conversion caching
- Celery for post-payment automation + invoice emailing

**Implemented flows**
- **Stripe**
  - Checkout session creation
  - Coupon and shipping represented in the Stripe checkout data
  - Webhook endpoint wired in project URLs
- **Paymob**
  - Intention / unified checkout flow
  - Webhook endpoint wired in project URLs
- **Post-payment automation**
  - Marks order paid, stores payment ID, triggers invoice sending, and updates recommendations (`payment/tasks.py`)

## Admin (Unfold + custom back-office tooling)

**Technologies used**
- `django-unfold` for modern admin UI
- Custom admin classes/actions/filters
- Chart.js (dashboard charts)
- RTL adjustments via custom CSS

**What’s customized**
- **Custom analytics dashboard** mounted at `/admin/` (`order/dashboard.py` + `templates/admin/index.html`)
  - KPI cards + multiple charts (Chart.js)
  - Quick links to filtered admin changelists
  - RTL-aware rendering for Arabic
- **Store admin productivity**
  - Translation tabs (TabbedTranslationAdmin)
  - Inline images
  - Variant group management with “Add Variant” shortcut (clone flow via `copy_from_id`)
  - Low-stock filter + bulk discount action with custom form/template
- **Orders admin productivity**
  - Inline order items + shipping address
  - Payment link rendering, invoice actions
  - CSV export + async bulk invoice generation tracked via `PdfFile`
- **Users admin**
  - Default `UserAdmin` re-registered using Unfold

## Translation / i18n (project-wide)

**Technologies used**
- Django i18n: `LocaleMiddleware`, `i18n_patterns`, `gettext_lazy`
- `django-modeltranslation` for bilingual model fields (EN/AR)

**What’s implemented**
- English + Arabic language support (including RTL in admin dashboard)

## Core infrastructure (used across apps)

- **Database**: PostgreSQL
- **Cache + sessions**: Redis (`django-redis`) + cache-backed sessions
- **Background jobs**: Celery (broker via env, commonly RabbitMQ `amqp://...` using `CELERY_BROKER_URL`)

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

