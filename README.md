# Serverless Event-Driven Order Processing System

## Overview
A scalable e-commerce backend built with Flask, PostgreSQL, DynamoDB, and AWS Lambda.

## Tech Stack
* Python 3.10+
* Flask & Flask-SQLAlchemy
* PostgreSQL (Relational Data)
* DynamoDB Local (Event Logging)
* AWS Lambda / Boto3

## Setup Instructions
1. Clone the repository.
2. Run `docker-compose up -d` to start PostgreSQL and DynamoDB.
3. Create a virtual environment: `python -m venv venv` and activate it.
4. Install dependencies: `pip install -r requirements.txt`.
5. Copy `.env.example` to `.env`.
6. Apply database migrations: `flask db upgrade`.
7. Run the application: `python run.py`.

## Core API Endpoints
* `POST /api/auth/register` - Register a user
* `POST /api/auth/login` - Login and receive JWT
* `GET /api/health` - Check system and DB status
* `POST /api/orders` - Place a new order