# Serverless Event-Driven Order Processing System

## Overview

An **enterprise-grade, event-driven e-commerce backend** built with **Flask, PostgreSQL, DynamoDB, and simulated AWS Lambda functions**.

This system provides:

* Secure **JWT authentication**
* **Product inventory management** with PostgreSQL row-level locking
* **Immutable event logging** in DynamoDB
* **Enterprise-grade webhook delivery system** with **HMAC-SHA256 signing**
* **Exponential backoff retries** and delivery observability

---

# Architecture Diagram

```text
[ Client ] ---> [ Flask REST API ] ---> [ PostgreSQL ] (State: Users, Orders, Products, Webhooks)
                        |
                        v
               (Lambda Invoker)
                        |
            +-----------+-----------+
            |                       |
    [ process_order ]      [ update_inventory ] (Row-Level Locking)
            |                       |
            +-----------+-----------+
                        |
                        v
               [ DynamoDB Local ] (OrderEvents Table)
                        |
                 (DynamoDB Stream Simulation)
                        |
                        v
                [ send_webhook ] (HMAC-SHA256 Signing & Retries)
                        |
            +-----------+-----------+
            |                       |
            v                       v
    [ External URLs ]      [ DynamoDB Local ] (WebhookDeliveries Table)
```

---

# Tech Stack

### Web Framework

* Flask
* Flask-RESTful

### Relational Database

* PostgreSQL
* SQLAlchemy

Used for:

* Users
* Products
* Orders
* Webhook subscriptions

### NoSQL Database

* DynamoDB Local

Used for:

* Event logging
* Webhook delivery logs

### Serverless

* AWS Lambda (Local simulation using `importlib`)
* AWS `boto3` integration for real AWS mode

### Authentication

* Flask-JWT-Extended (JWT Bearer Tokens)

### Validation

* Marshmallow

---

# Key Features

## Phase 1 — Core Backend

* JWT Authentication
* Secure password hashing
* RESTful CRUD APIs
* Entity relationships:

  * Users
  * Products
  * Orders

---

## Phase 2 — Event-Driven Architecture

* Asynchronous order processing
* Lambda-style event execution
* Race-condition prevention using:

```sql
SELECT ... FOR UPDATE
```

* Immutable event tracking in **DynamoDB**
* Global Secondary Indexes (GSI) for event queries

---

## Phase 3 — Enterprise Webhooks

Secure webhook delivery system featuring:

* HTTP POST delivery to subscriber URLs
* **HMAC-SHA256 payload signing**
* **5-second request timeout**
* **3 retry attempts**
* **Exponential backoff strategy**
* Delivery logging for observability

Webhook delivery logs stored in:

```
WebhookDeliveries DynamoDB table
```

---

# Local Setup Instructions

## 1. Clone Repository

```bash
git clone <repo-url>
cd order-processing-system
```

---

## 2. Start Docker Services

```bash
docker-compose up -d
```

This starts:

* PostgreSQL → **port 5432**
* DynamoDB Local → **port 8000**

---

## 3. Setup Python Environment

```bash
python -m venv venv
```

Activate environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / Mac**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# Configure Environment Variables

Copy example file:

```bash
cp .env.example .env
```

Update the values:

```ini
FLASK_APP=run.py
FLASK_ENV=dev

DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/order_processing_db

JWT_SECRET_KEY=your-super-secret-key

LAMBDA_MODE=local

DYNAMODB_URL=http://localhost:8000
AWS_REGION=us-east-1
```

---

# Initialize Database

Run migrations:

```bash
flask db upgrade
```

---

# Run Application

```bash
python run.py
```

---

# Lambda Functions Overview

## process_order

Responsibilities:

* Validates order
* Simulates payment processing (**80% success rate**)
* Updates order status in PostgreSQL

---

## update_inventory

Uses **PostgreSQL row-level locking**:

```sql
SELECT ... FOR UPDATE
```

This ensures:

* Safe stock updates
* No race conditions during concurrent orders

---

## send_webhook

Triggered automatically when a **DynamoDB event is created**.

Responsibilities:

1. Find active webhook subscribers
2. Sign payload using **HMAC-SHA256**
3. Send HTTP POST request
4. Retry failed requests (max **3 attempts**)
5. Use **exponential backoff**
6. Log:

* HTTP status code
* latency
* attempt count

All delivery logs are stored in **DynamoDB**.

---

# API Documentation

# Auth & System Endpoints

### Register User

```
POST /api/auth/register
```

---

### Login

```
POST /api/auth/login
```

Returns:

```
JWT Access Token
```

---

### Health Check

```
GET /api/health
```

Checks connectivity for:

* API
* PostgreSQL
* DynamoDB

---

# Product Endpoints

### List Products

```
GET /api/products
```

Supports:

```
page
per_page
search
```

---

### Create Product (Admin)

```
POST /api/products
```

---

### Update Product (Admin)

```
PUT /api/products/<id>
```

---

# Order Endpoints (JWT Required)

### Place Order

```
POST /api/orders
```

Triggers:

* `process_order`
* `update_inventory`

---

### List Orders

```
GET /api/orders
```

---

### Get Order Details

```
GET /api/orders/<id>
```

---

### Cancel Order

```
PUT /api/orders/<id>/cancel
```

Restores stock.

---

### View Order Events

```
GET /api/orders/<id>/events
```

Returns the DynamoDB **event timeline**.

---

# Webhook Management Endpoints (JWT Required)

### Create Webhook Subscription

```
POST /api/webhooks
```

Returns a `secret_key` used for **HMAC verification**.

---

### List Webhooks

```
GET /api/webhooks
```

---

### Update Webhook

```
PUT /api/webhooks/<id>
```

---

### Pause / Resume Webhook

```
PATCH /api/webhooks/<id>/toggle
```

---

### Delete Webhook

```
DELETE /api/webhooks/<id>
```

---

# Webhook Delivery Dashboard

### View All Deliveries

```
GET /api/webhooks/deliveries
```

---

### Deliveries for Specific Webhook

```
GET /api/webhooks/<webhook_id>/deliveries
```

---

### Failed Deliveries

```
GET /api/webhooks/deliveries/failed
```

---

# Testing Endpoint

Mock merchant receiver for webhook testing.

```
POST /api/webhook-receiver/listen
```

Requirements:

* `X-Webhook-Signature` header
* `?secret=` query parameter

Used to verify **HMAC-SHA256 signature validation**.
