# Revenue Engine API Documentation

## Overview

The Revenue Engine API is a Flask-based REST API that handles webhook processing, order fulfillment, lead management, and analytics for the autonomous revenue generation system.

**Base URL**: `https://api.copykit.io` (production) or `http://localhost:5000` (development)

## Authentication

Most endpoints require authentication via API key:

```bash
curl -H "X-API-Key: your-api-key" https://api.copykit.io/health
```

## Rate Limiting

- **General endpoints**: 1000 requests per hour, 100 per minute
- **Webhook endpoints**: 10 requests per minute
- **Lead creation**: 20 requests per minute

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

## Endpoints

### Health Check

#### GET /health

Check the health status of the API and its dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-27T10:30:00Z",
  "service": "omni-revenue-agent-api",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "database": "healthy",
    "stripe": "healthy"
  },
  "uptime": 3600
}
```

**Status Codes:**
- `200`: All systems healthy
- `503`: Service degraded or unhealthy

---

### Webhooks

#### POST /webhooks/stripe

Handle Stripe webhook events for payment processing.

**Headers:**
- `Content-Type: application/json`
- `Stripe-Signature: webhook_signature`

**Supported Events:**
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `charge.refunded`
- `charge.dispute.created`

**Response:**
```json
{
  "received": true
}
```

**Status Codes:**
- `200`: Webhook processed successfully
- `400`: Invalid content type or payload
- `401`: Invalid signature

#### POST /webhooks/paypal

Handle PayPal webhook events for payment processing.

**Headers:**
- `Content-Type: application/json`

**Supported Events:**
- `PAYMENT.CAPTURE.COMPLETED`
- `BILLING.SUBSCRIPTION.CREATED`
- `BILLING.SUBSCRIPTION.CANCELLED`
- `PAYMENT.CAPTURE.REFUNDED`

**Response:**
```json
{
  "received": true
}
```

---

### Lead Management

#### POST /api/leads

Create a new lead in the system.

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "source": "Manual",
  "tags": ["enterprise", "demo"],
  "utm_source": "google",
  "utm_campaign": "copykit_enterprise",
  "utm_medium": "cpc",
  "utm_term": "ai copywriting",
  "utm_content": "banner_ad"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "source": "Manual",
  "tags": ["enterprise", "demo"],
  "utmSource": "google",
  "utmCampaign": "copykit_enterprise",
  "utmMedium": "cpc",
  "utmTerm": "ai copywriting",
  "utmContent": "banner_ad",
  "createdAt": "2025-01-27T10:30:00Z",
  "updatedAt": "2025-01-27T10:30:00Z"
}
```

**Status Codes:**
- `200`: Lead already exists
- `201`: Lead created successfully
- `400`: Invalid request data
- `500`: Server error

---

### CopyKit Data

#### GET /api/copykit/data

Fetch data from the CopyKit URL and return structured information.

**Response:**
```json
{
  "status": "success",
  "data": {
    "global_env": {
      "api_key": "value",
      "environment": "production"
    },
    "title": "CopyKit - AI-Powered Copywriting That Converts",
    "meta_description": "Transform your marketing with AI-powered copy...",
    "last_updated": "2025-01-27T10:30:00Z"
  }
}
```

#### GET /api/copykit/products

Get CopyKit product data with real-time pricing and availability.

**Response:**
```json
{
  "status": "success",
  "products": [
    {
      "id": "monthly",
      "name": "CopyKit Monthly",
      "price": "£49",
      "period": "/month",
      "sku": "COPYKIT-MONTHLY",
      "description": "Perfect for growing businesses",
      "features": [
        "Weekly ad creative packs (10+ variants)",
        "Monthly landing page copy",
        "Email swipe files"
      ],
      "popular": true,
      "available": true
    }
  ]
}
```

#### GET /api/copykit/analytics

Get CopyKit analytics and performance data.

**Response:**
```json
{
  "status": "success",
  "analytics": {
    "totals": {
      "visitors": 1500,
      "leads": 75,
      "orders": 12,
      "revenue": 588.00
    },
    "recent_orders": [
      {
        "id": "uuid",
        "gateway": "stripe",
        "status": "paid",
        "amountGbp": 49.00,
        "buyerEmail": "customer@example.com",
        "sku": "COPYKIT-MONTHLY",
        "createdAt": "2025-01-27T10:30:00Z"
      }
    ],
    "kpi_trend": [
      {
        "date": "2025-01-27",
        "visitors": 50,
        "leads": 3,
        "orders": 1,
        "grossGbp": 49.00
      }
    ]
  }
}
```

---

### Fulfillment

#### POST /api/fulfilment/copykit

Manually trigger CopyKit fulfillment for an order.

**Request Body:**
```json
{
  "order_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "uuid"
}
```

#### POST /api/fulfilment/briefing

Manually trigger Daily Briefing fulfillment for an order.

**Request Body:**
```json
{
  "order_id": "uuid"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "uuid"
}
```

---

### KPI Management

#### GET /api/kpi/daily

Get daily KPI records.

**Query Parameters:**
- `days` (optional): Number of days to retrieve (default: 30)

**Response:**
```json
[
  {
    "date": "2025-01-27",
    "visitors": 50,
    "leads": 3,
    "orders": 1,
    "grossGbp": 49.00,
    "netGbp": 49.00,
    "refunds": 0,
    "crPct": 2.00,
    "stripeOrders": 1,
    "paypalOrders": 0,
    "stripeGrossGbp": 49.00,
    "paypalGrossGbp": 0.00
  }
]
```

#### POST /api/kpi/update

Update or create daily KPI record.

**Request Body:**
```json
{
  "date": "2025-01-27",
  "visitors": 50,
  "leads": 3,
  "orders": 1,
  "gross_gbp": 49.00,
  "net_gbp": 49.00,
  "refunds": 0,
  "cr_pct": 2.00
}
```

**Response:**
```json
{
  "date": "2025-01-27",
  "visitors": 50,
  "leads": 3,
  "orders": 1,
  "grossGbp": 49.00,
  "netGbp": 49.00,
  "refunds": 0,
  "crPct": 2.00,
  "createdAt": "2025-01-27T10:30:00Z",
  "updatedAt": "2025-01-27T10:30:00Z"
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

### Common Error Codes

- `400 Bad Request`: Invalid request data or missing required fields
- `401 Unauthorized`: Invalid or missing API key
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Unexpected server error

### Validation Errors

When request validation fails, the API returns detailed error information:

```json
{
  "error": "Validation Error",
  "message": "Invalid request data",
  "details": {
    "email": "Invalid email format",
    "name": "Name too long (max 255 characters)"
  },
  "timestamp": "2025-01-27T10:30:00Z"
}
```

---

## Webhook Security

### Stripe Webhooks

Stripe webhooks are verified using the `Stripe-Signature` header. The signature is validated against the webhook secret configured in the `STRIPE_WEBHOOK_SECRET` environment variable.

### PayPal Webhooks

PayPal webhook verification is implemented but may be disabled in development mode. In production, proper PayPal webhook signature verification should be implemented.

---

## Rate Limiting

The API implements rate limiting using Flask-Limiter with Redis as the storage backend. Rate limits are applied per IP address and can be customized per endpoint.

### Rate Limit Headers

All responses include rate limiting information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1643284800
```

---

## Monitoring and Logging

### Health Checks

The `/health` endpoint provides comprehensive health information including:
- Database connectivity
- External service status (Stripe, PayPal)
- System uptime
- Version information

### Logging

All API requests and errors are logged with structured logging including:
- Request method and path
- Response status code
- Processing time
- Error details
- User agent and IP address

### Metrics

The API exposes Prometheus-compatible metrics at `/metrics` (if enabled):
- Request count and duration
- Error rates
- Database connection pool status
- External API call metrics

---

## SDK Examples

### Python

```python
import requests

# Health check
response = requests.get('https://api.copykit.io/health')
print(response.json())

# Create lead
lead_data = {
    "email": "user@example.com",
    "name": "John Doe",
    "source": "Manual"
}
response = requests.post(
    'https://api.copykit.io/api/leads',
    json=lead_data,
    headers={'X-API-Key': 'your-api-key'}
)
print(response.json())
```

### JavaScript

```javascript
// Health check
const healthResponse = await fetch('https://api.copykit.io/health');
const health = await healthResponse.json();

// Create lead
const leadData = {
  email: 'user@example.com',
  name: 'John Doe',
  source: 'Manual'
};

const leadResponse = await fetch('https://api.copykit.io/api/leads', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify(leadData)
});
const lead = await leadResponse.json();
```

### cURL

```bash
# Health check
curl -X GET https://api.copykit.io/health

# Create lead
curl -X POST https://api.copykit.io/api/leads \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe",
    "source": "Manual"
  }'
```

---

## Changelog

### Version 1.0.0 (2025-01-27)
- Initial API release
- Webhook handling for Stripe and PayPal
- Lead management endpoints
- CopyKit data integration
- KPI tracking and analytics
- Comprehensive error handling and logging
- Rate limiting and security features