# CodeWarden API Reference

REST API documentation for the CodeWarden backend services.

## Base URL

```
Production: https://api.codewarden.io
Local:      http://localhost:8000
```

## Authentication

All API requests require authentication using an API key.

### API Key Authentication

Include your API key in the `X-API-Key` header:

```bash
curl -X POST https://api.codewarden.io/api/v1/events/ingest \
  -H "X-API-Key: cw_live_xxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{"events": [...]}'
```

### Dashboard Authentication

Dashboard endpoints use Supabase JWT tokens:

```bash
curl -X GET https://api.codewarden.io/api/dashboard/apps \
  -H "Authorization: Bearer <supabase-jwt-token>"
```

---

## SDK Endpoints

These endpoints are used by the SDKs to send telemetry data.

### Ingest Events (Batch)

**POST** `/api/v1/events/ingest`

Send multiple events in a single request.

**Headers:**
```
X-API-Key: cw_live_xxxxxxxxxxxx
Content-Type: application/json
```

**Request Body:**
```json
{
  "events": [
    {
      "event_type": "exception",
      "timestamp": "2024-01-15T10:30:00Z",
      "level": "error",
      "message": "Database connection failed",
      "exception": {
        "type": "ConnectionError",
        "value": "Connection refused to localhost:5432",
        "module": "psycopg2",
        "stacktrace": [
          {
            "filename": "/app/db.py",
            "lineno": 45,
            "function": "connect",
            "context_line": "conn = psycopg2.connect(dsn)"
          }
        ]
      },
      "context": {
        "request_id": "req-123",
        "user_id": "user-456"
      },
      "breadcrumbs": [
        {
          "timestamp": "2024-01-15T10:29:55Z",
          "category": "http",
          "message": "GET /api/users",
          "level": "info"
        }
      ]
    }
  ]
}
```

**Response:**
```json
{
  "status": "ok",
  "event_ids": ["evt-abc123", "evt-def456"]
}
```

### Ingest Single Event

**POST** `/api/v1/events/single`

Send a single event.

**Request Body:**
```json
{
  "event_type": "message",
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "info",
  "message": "User signup completed",
  "context": {
    "user_id": "user-789"
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "event_id": "evt-xyz789"
}
```

---

## Dashboard Endpoints

These endpoints power the CodeWarden dashboard.

### Get Dashboard Stats

**GET** `/api/dashboard/stats`

Get aggregated statistics for the dashboard overview.

**Response:**
```json
{
  "total_apps": 5,
  "total_events_24h": 1523,
  "total_errors_24h": 47,
  "critical_count": 3,
  "warning_count": 12,
  "apps_healthy": 3,
  "apps_warning": 1,
  "apps_critical": 1
}
```

### Apps

#### List Apps

**GET** `/api/dashboard/apps`

Get all apps for the authenticated user's organization.

**Response:**
```json
[
  {
    "id": "app-123",
    "name": "My API",
    "slug": "my-api",
    "description": "Production API server",
    "environment": "production",
    "framework": "fastapi",
    "status": "healthy",
    "created_at": "2024-01-01T00:00:00Z",
    "last_event_at": "2024-01-15T10:30:00Z",
    "event_count_24h": 450,
    "error_count_24h": 12
  }
]
```

#### Get App

**GET** `/api/dashboard/apps/{app_id}`

Get a single app by ID.

#### Create App

**POST** `/api/dashboard/apps`

Create a new app.

**Request Body:**
```json
{
  "name": "New API",
  "description": "My new API service",
  "environment": "production",
  "framework": "fastapi"
}
```

**Response:**
```json
{
  "id": "app-456",
  "name": "New API",
  "slug": "new-api",
  ...
}
```

### API Keys

#### List API Keys

**GET** `/api/dashboard/apps/{app_id}/keys`

Get all API keys for an app.

**Response:**
```json
[
  {
    "id": "key-123",
    "name": "Production Key",
    "key_prefix": "cw_live_abc",
    "key_type": "live",
    "permissions": ["events:write"],
    "created_at": "2024-01-01T00:00:00Z",
    "last_used_at": "2024-01-15T10:30:00Z"
  }
]
```

#### Create API Key

**POST** `/api/dashboard/apps/{app_id}/keys?name={name}&key_type={type}`

Create a new API key.

**Query Parameters:**
- `name` (string): Key name (default: "Default Key")
- `key_type` (string): Key type - `live` or `test` (default: "live")

**Response:**
```json
{
  "id": "key-456",
  "name": "Production Key",
  "key_prefix": "cw_live_xyz",
  "key_type": "live",
  "full_key": "cw_live_xyzabc123...",  // Only returned on creation!
  "permissions": ["events:write"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

> **Important:** The `full_key` is only returned once during creation. Store it securely.

#### Revoke API Key

**DELETE** `/api/dashboard/keys/{key_id}`

Revoke an API key.

**Response:** `204 No Content`

### Events

#### List Events

**GET** `/api/dashboard/events`

Get recent events across all apps.

**Query Parameters:**
- `limit` (int): Max events to return (default: 50)
- `severity` (string): Filter by severity (critical, warning, info)

**Response:**
```json
[
  {
    "id": "evt-123",
    "event_type": "exception",
    "severity": "critical",
    "error_type": "DatabaseError",
    "error_message": "Connection timeout",
    "file_path": "/app/db.py",
    "line_number": 45,
    "status": "new",
    "occurred_at": "2024-01-15T10:30:00Z",
    "analysis_status": "completed",
    "analysis_summary": "Database connection pool exhausted..."
  }
]
```

#### Get App Events

**GET** `/api/dashboard/apps/{app_id}/events`

Get events for a specific app.

**Query Parameters:**
- `limit` (int): Max events (default: 50)
- `offset` (int): Pagination offset
- `severity` (string): Filter by severity
- `status_filter` (string): Filter by status (new, investigating, resolved)

### Settings

#### Get Settings

**GET** `/api/dashboard/settings`

Get organization settings.

**Response:**
```json
{
  "name": "Acme Corp",
  "notification_email": "alerts@acme.com",
  "telegram_chat_id": "-123456789",
  "slack_webhook": null,
  "notify_on_critical": true,
  "notify_on_warning": true,
  "weekly_digest": true
}
```

#### Update Settings

**PATCH** `/api/dashboard/settings`

Update organization settings.

**Request Body:**
```json
{
  "notification_email": "newalerts@acme.com",
  "notify_on_warning": false
}
```

### Architecture Map

#### Get Architecture Map

**GET** `/api/dashboard/apps/{app_id}/architecture`

Get the service architecture map for an app.

**Response:**
```json
{
  "nodes": [
    {
      "id": "node-1",
      "type": "api",
      "name": "API Server",
      "status": "healthy",
      "latency": 45,
      "error_rate": 0.001
    },
    {
      "id": "node-2",
      "type": "database",
      "name": "PostgreSQL",
      "status": "healthy",
      "latency": 12
    },
    {
      "id": "node-3",
      "type": "cache",
      "name": "Redis",
      "status": "warning",
      "latency": 3,
      "error_rate": 0.05
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "source": "node-1",
      "target": "node-2",
      "label": "queries"
    },
    {
      "id": "edge-2",
      "source": "node-1",
      "target": "node-3",
      "label": "cache"
    }
  ]
}
```

**Node Types:**
- `frontend` - Frontend application
- `api` - API server
- `database` - Database service
- `cache` - Cache service (Redis, Memcached)
- `external` - External API/service
- `storage` - Object storage (S3, R2)

**Status Values:**
- `healthy` - Operating normally
- `warning` - Degraded performance
- `critical` - Service issues

### AI Analysis

#### Get AI Status

**GET** `/api/dashboard/ai/status`

Check AI analysis availability.

**Response:**
```json
{
  "available": true,
  "models": ["gemini-1.5-flash", "claude-3-haiku", "gpt-4o-mini"],
  "message": "AI analysis is available"
}
```

#### Analyze Event

**POST** `/api/dashboard/events/{event_id}/analyze`

Trigger AI analysis for an event.

**Response:**
```json
{
  "event_id": "evt-123",
  "analysis": {
    "summary": "Database connection pool exhausted due to connection leak",
    "severity": "critical",
    "root_cause": "Connections not being properly released after transactions",
    "recommendations": [
      "Implement connection pooling with proper timeout",
      "Add connection cleanup in finally blocks",
      "Monitor active connection count"
    ],
    "similar_issues": ["evt-100", "evt-105"]
  }
}
```

### Notifications

#### Get Notification Status

**GET** `/api/dashboard/notifications/status`

Check notification channel availability.

**Response:**
```json
{
  "available": true,
  "channels": ["email", "telegram"],
  "message": "Notifications are configured"
}
```

#### Send Notification

**POST** `/api/dashboard/events/{event_id}/notify`

Send a notification for an event.

**Request Body:**
```json
{
  "channels": ["email", "telegram"]
}
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message here"
}
```

**HTTP Status Codes:**

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Validation Error - Invalid data format |
| 500 | Internal Server Error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/v1/events/ingest` | 1000 req/min |
| `/api/v1/events/single` | 100 req/min |
| `/api/dashboard/*` | 100 req/min |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1705312800
```
