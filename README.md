# Batman API Gateway (Python + Redis)

## Overview
This repository implements a high‑performance API Gateway built in Python using Flask.  
It provides routing, caching via Redis, authentication handling, request tracking, and forwarding logic.

The gateway sits between clients and backend microservices, managing session validation, caching, forwarding, and consistent API responses.

---

# Architecture Overview

## Components
### 1. **Flask Web Server**
Handles all inbound requests under `/v1/...`.

### 2. **Redis Caching Layer**
Used for:
- caching GET responses
- session data caching
- reducing load on backend services

### 3. **Request Forwarder**
Forwards requests to internal microservices and merges responses.

### 4. **Request Tracker**
Stores every tracked request in MySQL (`requests` table).

### 5. **Library**
Defines all API routes, required rules, caching settings, and exception handlers.

---

# Project Structure

```
/v1
  api.py
  cache.py
  helper.py
  library.py
includes/
  db.py
services/
  logger.py
  users.py
settings.py
main.py
```

---

# Request Flow (Step By Step)

## 1. **main.py**
Initializes:
- Flask app
- Redis connection
- Sentry (optional)

Every request hits:
```
/<path>
```
which sends the request into `Api.Handler`.

---

# 2. **Api.Handler()** – The Heart of the Gateway

This method:
1. Parses headers, body, IP
2. Loads session from Redis or DB
3. Merges session metadata into request body
4. Determines endpoint rules from `Library.Standard`
5. Checks:
   - requires_auth?
   - requires_tracking?
   - requires_caching?
6. Pulls cached data if available
7. Forwards request to backend service if needed
8. Caches response
9. Returns response

---

# Request Lifecycle Diagram

```
Client
  ↓
Flask (/v1/*)
  ↓
Api.Handler()
  ↓
Parse Request → Load Session → Apply Rules → Check Cache
  ↓
Forward to service (internal API)
  ↓
Receive Response
  ↓
Store cache (optional)
  ↓
Track request in MySQL (async)
  ↓
Return final response to client
```

---

# Authentication

Session cookies:
- Cached in Redis as `cookie:<uuid>`
- Loaded via `Users.VerifySession()`
- Auto‑merged into request body

If a route requires authentication but session missing → returns **403 Unauthorized**

---

# Caching (Redis)

### Cache keys use prefix:
```
<REDIS_KEY_PREFIX>:<key>
```

### Supported caching operations:
- `Cache.Set(key, value, ttl)`
- `Cache.Get(key)`
- `Cache.Delete(keys)`
- `Cache.Clear()`

### Automatic cache deletion
Some routes define:
```
cache_delete: [
  "cookie:<value>",
  "user_id:{123}:*"
]
```

---

# Forwarding Logic

`Helper.Forwarder()` determines:
- GET → `endpoint?params`
- POST → JSON body

Uses Python `requests`:

```
requests.get(...)
requests.post(...)
```

Returns:
```
(result.headers, result.json())
```

---

# Request Tracking (MySQL)

Stored on **every** tracked request using:
```
Api.Track(...)
```

The following is stored:
- headers
- body
- response
- tracking metadata
- IP address
- timestamp

Insert query:

```
INSERT INTO requests (...)
```

Tracking runs **async** using:
```
ThreadPoolExecutor
```

---

# v1/library.py – Route Definitions

Each endpoint includes:

```
'method': 'GET/POST',
'endpoint': <backend service URL>,
'requires_auth': True/False,
'requires_tracking': True/False,
'requires_caching': True/False,
'cache_ttl': <seconds>,
'cache_key': <key>,
'cache_delete': [...]
```

This is the rule engine that powers the gateway.

---

# v1/helper.py – Utilities

### Parsing
- Headers
- Body
- IP address

### Forwarding
Handles:
```
GET /service?params
POST /service with JSON body
```

Logs failure via `Logger.CreateExceptionLog`.

---

# v1/cache.py – Redis Functions

### Connect
Initializes global Redis client.

### Get / Set / Delete
Handles JSON serialization and key namespacing.

---

# v1/api.py – Core Response Wrapper

Every request ends with:

```
Api.Response(...)
```

This handles:
- request tracking
- merging all relevant metadata
- returning final JSON

---

# Running Locally

## Install Requirements
```
pip install flask redis requests sentry-sdk
```

## Start Redis
```
docker run -p 6379:6379 redis
```

## Run API
```
python main.py
```

Gateway will run on:
```
http://0.0.0.0:<settings.FLASK_PORT>
```

---

# Security Notes

- Redis should be internal‑only
- All backend service URLs should stay private to gateway
- No direct client‑to‑service communication
- All tokens/sensitive data stored in environment variables

---

## Author
**Jawwad Ahmed Abbasi**  
Senior Software Developer  
[GitHub](https://github.com/jawwadabbasi) | [YouTube](https://www.youtube.com/@jawwad_abbasi)