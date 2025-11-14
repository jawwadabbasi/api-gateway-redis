# Batman API Gateway (Python + Redis)

## Overview
This repository implements a high-performance API Gateway built in Python using Flask.  
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
.
├── README.md
├── dev
│   ├── Dockerfile
│   ├── kubeconfig.yaml
│   └── settings.py
├── prod
│   ├── Dockerfile
│   ├── kubeconfig.yaml
│   └── settings.py
└── src
    ├── configure.py
    ├── cron.py
    ├── includes
    │   ├── common.py
    │   ├── db.py
    │   └── schema.py
    ├── main.py
    ├── requirements.txt
    ├── services
    │   ├── crons.py
    │   ├── logger.py
    │   └── users.py
    ├── settings.py
    ├── v1
    │   ├── api.py
    │   ├── cache.py
    │   ├── helper.py
    │   └── library.py
    └── v2
        └── controller.py

8 directories, 23 files
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

# 2. **Api.Handler()** - The Heart of the Gateway

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
Parse Request -> Load Session -> Apply Rules -> Check Cache
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
- Auto-merged into request body

If a route requires authentication but session missing -> returns **403 Unauthorized**

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
- GET -> `endpoint?params`
- POST -> JSON body

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

---

# v1/library.py - Route Definitions

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

# v1/helper.py - Utilities

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

# v1/cache.py - Redis Functions

### Connect
Initializes global Redis client.

### Get / Set / Delete
Handles JSON serialization and key namespacing.

---

# v1/api.py - Core Response Wrapper

Every request ends with:

```
Api.Response(...)
```

This handles:
- request tracking
- merging all relevant metadata
- returning final JSON

---

# Running Redis - Locally and in Production

### Development (Local Redis)

In development, Redis can run locally using Docker:

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

This launches a local Redis instance for quick testing.

---

## Production: AWS ElastiCache Redis OSS

### Why Use AWS ElastiCache Redis OSS?

- Fully managed Redis (no patching or maintenance)
- Automatic failover
- Multi-AZ replication
- High availability & low latency
- Works exactly like local Redis — same protocol, same Python client

The API Gateway code **does not need any rewrite**.  
Only the connection settings change.

---

## Connecting the API Gateway to ElastiCache

Update your `settings.py`:

```python
REDIS_HOST = "batman-cache.xxxxxx.ng.0001.use1.cache.amazonaws.com"
REDIS_PORT = 6379
REDIS_SSL = True
REDIS_DB = 0
REDIS_KEY_PREFIX = "gateway"
```

Your Redis client automatically connects:

```python
import redis

settings.REDIS_CLIENT = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    ssl=settings.REDIS_SSL,
    decode_responses=True
)
```

---

## Security Notes for ElastiCache

AWS enforces:

- VPC-only access
- Optional authentication tokens
- TLS encryption

If your cluster uses an auth token:

```python
settings.REDIS_CLIENT = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    ssl=True,
    password=settings.REDIS_AUTH_TOKEN,
    decode_responses=True
)
```

---

## Recommended Deployment Pattern

Environment | Redis Setup
----------- | -----------
Local Dev | Docker Redis
Production | Multi-AZ ElastiCache Redis OSS cluster

---

## How the API Gateway Uses Redis

Redis is used for:

- User session caching
- Cached GET responses
- Cached user profiles
- Cache invalidation after POST requests

---

## Testing Redis Connectivity

Run:

```bash
redis-cli -h <endpoint> -p 6379 --tls ping
```

Expected output:

```
PONG
```

---

## Author
**Jawwad Ahmed Abbasi**  
Senior Software Developer  
[GitHub](https://github.com/jawwadabbasi) | [YouTube](https://www.youtube.com/@jawwad_abbasi)