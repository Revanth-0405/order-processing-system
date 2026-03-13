# Serverless Event-Driven Order Processing System

An **enterprise-grade, event-driven order processing API** built with **Flask, PostgreSQL, DynamoDB, and AWS Lambda**. This system handles asynchronous order processing, inventory management, and includes a robust, secure **webhook dispatch system** for notifying external merchants.

---

# 🏗 Architecture Diagram

```text
+-------------------+        +--------------------+      +-----------------------+
|    Flask API      | -----> |    PostgreSQL      |      |      DynamoDB         |
|    (Gateway)      |        |   (Orders, Users,  |      |   (Event Logs,        |
|  (Auth, Routes)   |        |     Products)      |      |   Webhook Delivery)   |
+-------------------+        +--------------------+      +-----------------------+
         |                                                           ^
         | (Invokes asynchronously)                                  | (Logs delivery)
         v                                                           |
+-------------------+    Trigger   +--------------------+            |
|   AWS Lambda      | -----------> |   AWS Lambda       | -----------+
| (process_order)   |              | (send_webhook)     |
+-------------------+              +--------------------+
         |
         | Trigger
         v
+-------------------+
|   AWS Lambda      |
| (update_inventory)|
+-------------------+
```

---

# 🚀 Tech Stack

**Framework**

* Python 3.12
* Flask (App Factory Pattern, Blueprints)

**Databases**

* PostgreSQL (Relational Data)
* DynamoDB Local (NoSQL Event & Delivery Logs)

**Serverless**

* AWS Lambda (Local Python invocation / SAM compatible)

**Security**

* JWT Authentication
* HMAC-SHA256 Webhook Signatures

**Testing**

* Pytest
* pytest-mock
* pytest-flask
* In-memory SQLite used during tests

---

# ✨ Elite / Bonus Features Implemented

* **Idempotency Keys**
  Prevents duplicate order placement.

* **Webhook Circuit Breaker**
  Automatically disables webhook subscriptions after **5 consecutive failures**.

* **Dead Letter Queue (DLQ)**
  Failed webhook deliveries stored in **PostgreSQL** for manual retry.

* **Webhook Rate Limiting**
  Custom DynamoDB GSI implementation limiting deliveries to **100/hour**.

* **API Versioning**
  All routes are versioned under `/api/v1/`.

* **Request Tracing & JSON Logging**
  End-to-end `request_id` tracking from Flask → Lambda → DynamoDB.

---

# 🛠 Local Setup Instructions

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/order-processing-system.git
cd order-processing-system
```

---

## 2. Setup Virtual Environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**Mac/Linux**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 3. Start Infrastructure (Docker)

Ensure Docker is running.

```bash
docker-compose up -d
```

This starts:

* PostgreSQL
* DynamoDB Local

---

# 🔑 Environment Variables (.env.example)

Create a `.env` file in the root directory.

```env
FLASK_APP=run.py
FLASK_ENV=development

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/orders_db

JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-prod

LAMBDA_MODE=local

AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_ENDPOINT_URL=http://localhost:8000
```

---

# Initialize Databases

Run migrations:

```bash
flask db upgrade
```

---

# Run the Application

```bash
flask run
```

---

# 🧪 Testing Instructions

The system includes a **comprehensive Pytest suite (24 tests)** covering:

* Unit tests
* Integration tests
* Lambda handler logic

Run the test suite:

```bash
python -m pytest -v
```

---

# End-to-End Testing Flow (Manual / Postman)

### 1. Register & Login

```
POST /api/v1/auth/register
POST /api/v1/auth/login
```

Retrieve JWT token.

---

### 2. Create Product

Create a product with stock using admin endpoint.

---

### 3. Register Webhook

```
POST /api/v1/webhooks
```

Example body:

```json
{
 "target_url": "http://127.0.0.1:5000/api/v1/webhook-receiver/listen",
 "event_type": "all"
}
```

---

### 4. Place Order

```
POST /api/v1/orders
```

Include header:

```
Idempotency-Key: unique-key
```

---

### 5. Trigger Processing

Flask automatically invokes the **process_order Lambda**.

---

### 6. Verify Order Status

```
GET /api/v1/orders/<id>
```

Status should become **confirmed**.

---

### 7. Verify Inventory

Ensure stock was decremented via **row-level locking**.

---

### 8. Verify Event Log

```
GET /api/v1/events
```

Event stored in **DynamoDB with request_id**.

---

### 9. Verify Webhook Delivery

```
GET /api/v1/webhooks/deliveries
```

Shows webhook POST log in DynamoDB.

---

### 10. Verify Receiver

The Flask terminal logs webhook receipt confirming **HMAC-SHA256 verification**.

---

# 📚 Lambda Function Documentation

### process_order

* Validates order
* Simulates payment logic
* Updates order status
* Logs event to DynamoDB
* Triggers other lambdas

---

### update_inventory

Handles:

* `reduce_stock`
* `restore_stock`

Uses PostgreSQL row-level locking:

```sql
SELECT ... FOR UPDATE
```

Prevents race conditions.

---

### send_webhook

Responsibilities:

* Query active subscriptions
* Sign payload with **HMAC-SHA256**
* Enforce **100/hour rate limit**
* Send HTTP POST request
* Retry with exponential backoff **(2s / 4s / 8s)**
* Log delivery to DynamoDB
* Send failures to DLQ
* Trigger circuit breaker when needed

---

# 📦 Webhook Payload Format

Every webhook delivery uses this JSON structure:

```json
{
 "event": "order_confirmed",
 "delivery_id": "550e8400-e29b-41d4-a716-446655440000",
 "timestamp": "2026-03-13T12:00:00Z",
 "data": {
   "order_id": "123e4567-e89b-12d3-a456-426614174000",
   "order_number": "ORD-20260313-ABCD",
   "status": "confirmed",
   "total_amount": 149.99,
   "items": []
 }
}
```

---

# 🌐 API Endpoints Reference

## Auth

```
POST /api/v1/auth/register
POST /api/v1/auth/login
```

---

## Products

```
GET /api/v1/products
GET /api/v1/products/<id>
POST /api/v1/products
PUT /api/v1/products/<id>
DELETE /api/v1/products/<id>
```

---

## Orders

```
POST /api/v1/orders
GET /api/v1/orders
GET /api/v1/orders/<id>
PUT /api/v1/orders/<id>/cancel
```

---

## Webhooks

```
POST /api/v1/webhooks
GET /api/v1/webhooks
GET /api/v1/webhooks/<id>
PATCH /api/v1/webhooks/<id>/toggle
DELETE /api/v1/webhooks/<id>
POST /api/v1/webhooks/<id>/test
```

---

## Webhook Delivery Logs

```
GET /api/v1/webhooks/deliveries
GET /api/v1/webhooks/stats
GET /api/v1/webhooks/dlq
POST /api/v1/webhooks/dlq/<id>/resolve
```

---

## Receiver Endpoint

```
POST /api/v1/webhook-receiver/listen
```

Used to verify webhook delivery.

---

## System & Events

```
GET /api/v1/events
GET /api/v1/health
```

Checks connectivity with:

* Flask
* PostgreSQL
* DynamoDB
* Lambdas

---

# API cURL Examples

Replace `YOUR_JWT_TOKEN` with the token from login.

---

## Register

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/register \
-H "Content-Type: application/json" \
-d '{"username":"merchant","email":"merchant@test.com","password":"password123"}'
```

---

## Login

```bash
curl -X POST http://127.0.0.1:5000/api/v1/auth/login \
-H "Content-Type: application/json" \
-d '{"username":"merchant","password":"password123"}'
```

---

## Create Product

```bash
curl -X POST http://127.0.0.1:5000/api/v1/products \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json" \
-d '{"name":"Mechanical Keyboard","sku":"KB-001","price":120.00,"stock_quantity":50}'
```

---

## Register Webhook

```bash
curl -X POST http://127.0.0.1:5000/api/v1/webhooks \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Content-Type: application/json" \
-d '{"target_url":"http://127.0.0.1:5000/api/v1/webhook-receiver/listen","event_type":"all"}'
```

---

## Place Order

```bash
curl -X POST http://127.0.0.1:5000/api/v1/orders \
-H "Authorization: Bearer YOUR_JWT_TOKEN" \
-H "Idempotency-Key: postman-test-key-001" \
-H "Content-Type: application/json" \
-d '{"shipping_address":"123 Main St","items":[{"product_id":"REPLACE_WITH_PRODUCT_UUID","quantity":1}]}'
```

---

## Health Check

```bash
curl -X GET http://127.0.0.1:5000/api/v1/health
```

