# FastAPI Secure Microservice

A production-ready, highly scalable demo of a RESTful microservice built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, 
**PostgreSQL 15**, and **Redis 7**. Designed with enterprise security standards, non-blocking asynchronous I/O, 
automated database migrations, and one-command Docker deployment.

Although production-ready, this project is intended as a portfolio piece. Demonstrating Python backend development 
with a modern tech stack, security best practices, and containerized microservice architecture. 

Please keep in mind that this is my first 'big' project and so there will most likely be areas for improvement. 
As I keep learning and improving my skills, I may update this project to reflect that. By the point you are reading 
this, I hope to have more recent projects that better reflect my current skill level. Thanks for taking the time to 
check out my work and I hope you enjoy it!

---

# Architecture Overview

```
                               ┌───────────────────────────┐
                               │   Client / Frontend App   │
                               └─────────────┬─────────────┘
                                             │ HTTP Requests
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Service                                      │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         Security Headers Middleware                            │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            ▼                                           │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        Global Exception Handler (500/422)                      │   │
│   └────────────────────────────────────────┬───────────────────────────────────────┘   │
│                                            ▼                                           │
│   ┌──────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐   │
│   │   Auth Router (JWT)  │      │ Sliding Rate Limiter│      │  Response Cache     │   │
│   └──────────┬───────────┘      └──────────┬──────────┘      └──────────┬──────────┘   │
└──────────────┼─────────────────────────────┼────────────────────────────┼──────────────┘
               │                             │                            │
               ▼ Async Queries               ▼ Cache / Limit              ▼ Store Data
┌───────────────────────────┐  ┌─────────────────────────────────────────────────────────┐
│   PostgreSQL 15 Container │  │                   Redis 7 Container                 │
│    (SQLAlchemy + asyncpg) │  │               (Connection Pool via redis-py)            │
└───────────────────────────┘  └─────────────────────────────────────────────────────────┘
```


# Key Features:

- Asynchronous Core Engine: Fully non-blocking database queries and cache interactions using asyncpg and redis.asyncio.

- Enterprise Security Standards:

    - Argon2 Password Hashing: Modern, memory-hard password hashing via pwdlib[argon2].

    - OAuth2 + JWT Authentication: Stateless token-based access control with configurable expiration.

    - OWASP Security Headers: Built-in middleware configuring HSTS, X-Frame-Options, X-Content-Type-Options, and 
      Permissions-Policy.

- Distributed Rate Limiting: Sliding-window rate-limiting decorator backed by Redis to prevent brute-force attacks.

- Response Caching: High-performance Redis caching middleware for expensive API endpoints.

- Unified Error Handling: Global exception handlers outputting standardized error payloads for operational consistency.

- Database Migrations: Automated schema versioning via Alembic.

- Containerized Deployment: Multi-container orchestrations powered by Docker Compose.

- CI/CD Integration: Pre-configured GitHub Actions workflow (tests.yml) running isolated unit and integration test 
  suites against live Postgres/Redis services.


# Tech Stack:

- Framework: FastAPI 0.141+

- Database: PostgreSQL 15 (ORM: SQLAlchemy 2.0 Async + asyncpg)

- In-Memory Store: Redis 7 (Client: redis.asyncio)

- Security & Auth: Argon2id, PyJWT (python-jose), Pydantic v2

- Migrations: Alembic

- Testing: Pytest, HTTPX, Pytest-Asyncio

- DevOps: Docker, Docker Compose, GitHub Actions


# Quickstart Guide

Prerequisites:

- Docker Desktop installed on your machine
- git installed

1. Clone Repository

- git clone https://github.com/harryrix6/fastapi-secure-service.git
- cd fastapi-secure-service

2. Configure Environment Variables

Copy the `.env.example` file to `.env` and modify the values as needed.
- cd .env.example .env

3. Spin up Services

- docker compose up --build / docker compose up -d --build (for detached mode)

The service will be live at 'http://localhost:8000'


# Environment Variables Reference

PROJECT_NAME: Display name for OpenAPI docs and logs.
SECRET_KEY: HMAC secret key for JWT signing and encryption.
ALGORITHM: JWT signing algorithm (e.g., HS256).
ACCESS_TOKEN_EXPIRE_MINUTES: Token expiration time in minutes.
POSTGRES_USER: PostgreSQL username.
POSTGRES_PASSWORD: PostgreSQL password.
POSTGRES_DB: PostgreSQL database name.
POSTGRES_HOST: PostgreSQL host (default: db).
POSTGRES_PORT: PostgreSQL port (default: 5432).
REDIS_HOST: Redis host (default: redis).
REDIS_PORT: Redis port (default: 6379).
DATABASE_URL: SQLAlchemy database URL (e.g., postgresql+asyncpg://user:password@host:port/dbname).


# API Documentation

Once the container stack is running, you can access the interactive API documentation in browser at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Core Endpoints:

POST /api/auth/register: Register a new user (requires username, email, password).
POST /api/auth/login: Authenticate user and return JWT access token.
GET /api/users/me: Retrieve the authenticated user's profile (requires valid JWT).
GET /: Health check endpoint returning service status.
GET /test-cache: Test endpoint demonstrating Redis caching functionality.
GET /test-rate-limit: Throttling demo (3 requests/10s).


# Running Tests

Execute automated test suite inside the running web container:

- docker compose exec web pytest

To run tests with full logging and coverage output:

- docker compose exec web pytest -v -s

