# Serverless Event-Driven Order Processing System

## Overview

A scalable e-commerce backend built with **Flask, PostgreSQL, DynamoDB, and AWS Lambda**.
This system manages product inventory, order processing, and immutable event logging using an **event-driven serverless architecture**.

---

## Architecture Diagram

```
[ Client ] ---> [ Flask REST API ] ---> [ PostgreSQL ] (State: Orders, Products)
                        |
                        v
               (Lambda Invoker)
                        |
            +-----------+-----------+
            |                       |
     [ process_order ]      [ update_inventory ]
            |             (Row-Level Locking)
            +-----------+-----------+
                        |
                        v
               [ DynamoDB Local ] (Immutable Event Logs)
```

---

## Tech Stack

**Backend Framework**

* Flask
* Flask-RESTful

**Relational Database**

* PostgreSQL
* SQLAlchemy

**NoSQL Database**

* DynamoDB Local (Event logging)

**Serverless**

* AWS Lambda (Local Python invocation & Boto3 AWS mode)

**Authentication**

* Flask-JWT-Extended (JWT Bearer Tokens)

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repo-url>
cd order-processing-system
```

### 2. Start services

Run PostgreSQL and DynamoDB Local using Docker:

```bash
docker-compose up -d
```

### 3. Create virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / Mac**

```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Fill in the required secrets.

### 6. Run database migrations

```bash
flask db upgrade
```

### 7. Run the application

```bash
python run.py
```

---

# Lambda Functions

### process_order

Responsibilities:

* Validates the order
* Simulates payment processing (80% success rate)
* Updates order status to **confirmed** or **cancelled**
* Logs all state transitions to **DynamoDB**

---

### update_inventory

Responsibilities:

* Uses PostgreSQL **row-level locking**

```
SELECT ... FOR UPDATE
```

* Safely decrements or restores product stock
* Prevents race conditions during concurrent orders

---

# API Documentation

## Auth Endpoints

### Register User

```
POST /api/auth/register
```

Request body:

```
username
email
password
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

# Product Endpoints

### Get Products

```
GET /api/products
```

Supports query params:

```
page
per_page
search
```

---

### Get Single Product

```
GET /api/products/<id>
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

### Delete Product (Admin)

```
DELETE /api/products/<id>
```

Uses **soft delete**.

---

# Order Endpoints (JWT Required)

### Place Order

```
POST /api/orders
```

Triggers the **Lambda processing pipeline**.

---

### List Orders

```
GET /api/orders
```

Returns orders for the authenticated user.

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

Restores product stock.

---

### Manually Trigger Order Processing (Admin)

```
POST /api/orders/<id>/process
```

Triggers **process_order Lambda**.

---

### Get Order Event Logs

```
GET /api/orders/<id>/events
```

Returns DynamoDB event logs for the order.

---

# Event Endpoints (Admin Only)

### Get All Events

```
GET /api/events
```

Returns paginated system events.

---

### Query Events by Type

```
GET /api/events/types/<type>
```

Uses DynamoDB **Global Secondary Index (GSI)**.

---

# System Endpoints

### Health Check

```
GET /api/health
```

Checks connectivity for:

* API
* PostgreSQL
* DynamoDB

---

# Key Features

* Event-driven order processing
* Serverless Lambda architecture
* Row-level locking for safe inventory updates
* Immutable event logging with DynamoDB
* JWT authentication
* Clean service-layer architecture
