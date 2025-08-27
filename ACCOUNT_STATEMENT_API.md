# Account Statement & Summary API Documentation

## Overview
This document provides the API endpoints for account statement and summary functionality in the DreamBox backend.

## API Endpoints

### 1. Comprehensive Account Summary
**Endpoint:** `GET /account/summary`

**Description:** Provides a complete overview of the user's financial status including balances, goals, recent transactions, and monthly statistics.

**Authentication:** Required (Bearer Token)

**Response Structure:**
```json
{
  "account_balances": {
    "total_balance": 5000.00,
    "safelock_balance": 3000.00,
    "mygoal_balance": 1500.00,
    "emergency_balance": 400.00,
    "flexi_balance": 100.00
  },
  "goals": {
    "safelock_goals": [
      {
        "id": "uuid",
        "name": "Vacation Fund",
        "target_amount": 5000.00,
        "current_amount": 3000.00,
        "progress_percentage": 60.0,
        "days_remaining": 45,
        "target_date": "2024-06-15",
        "has_emergency_fund": true,
        "emergency_fund_percentage": 10
      }
    ],
    "mygoal_goals": [...],
    "total_goals": 3
  },
  "recent_transactions": [
    {
      "id": "uuid",
      "transaction_type": "deposit",
      "account_type": "safelock",
      "amount": 500.00,
      "status": "successful",
      "description": "Monthly savings",
      "goal_name": "Vacation Fund",
      "created_at": "2024-01-15T10:30:00Z",
      "reference": "TXN123456"
    }
  ],
  "monthly_statistics": {
    "total_deposits": 1500.00,
    "transaction_count": 8
  },
  "account_status": {
    "has_emergency_fund": true,
    "has_flexi_account": true,
    "active_goals": 2
  }
}
```

### 2. Detailed Account Statement
**Endpoint:** `GET /account/statement`

**Description:** Get detailed account statement with opening/closing balances, transactions, and period statistics.

**Authentication:** Required (Bearer Token)

**Query Parameters:**
- `start_date` (optional): Start date for statement period (ISO format)
- `end_date` (optional): End date for statement period (ISO format)
- `account_type` (optional): Filter by account type (safelock, mygoal, emergency, flexi)
- `goal_id` (optional): Filter by specific goal UUID
- `limit` (optional): Number of transactions to return (max 500, default 100)
- `offset` (optional): Offset for pagination (default 0)

**Response Structure:**
```json
{
  "statement_period": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z",
    "opening_balance": 3000.00,
    "closing_balance": 5000.00
  },
  "period_statistics": {
    "total_deposits": 2000.00,
    "total_transactions": 15,
    "average_transaction_amount": 133.33
  },
  "current_balances": {
    "total_balance": 5000.00,
    "safelock_balance": 3000.00,
    "mygoal_balance": 1500.00,
    "emergency_balance": 400.00,
    "flexi_balance": 100.00
  },
  "transactions": {
    "total_count": 15,
    "by_account_type": {
      "safelock": [...],
      "mygoal": [...],
      "emergency": [...],
      "flexi": [...]
    },
    "all_transactions": [...]
  },
  "pagination": {
    "limit": 100,
    "offset": 0,
    "has_more": false
  }
}
```

### 3. Goals Progress Summary
**Endpoint:** `GET /account/goals-progress`

**Description:** Provides detailed analysis of goal progress including required daily savings and status tracking.

**Authentication:** Required (Bearer Token)

**Response Structure:**
```json
{
  "goals": [
    {
      "id": "uuid",
      "name": "Vacation Fund",
      "type": "safelock",
      "target_amount": 5000.00,
      "current_amount": 3000.00,
      "progress_percentage": 60.0,
      "days_remaining": 45,
      "target_date": "2024-06-15",
      "remaining_amount": 2000.00,
      "required_daily_savings": 44.44,
      "has_emergency_fund": true,
      "emergency_fund_percentage": 10,
      "status": "on_track"
    }
  ],
  "summary": {
    "total_goals": 3,
    "average_progress": 65.5,
    "goals_on_track": 2,
    "goals_needing_attention": 1,
    "completed_goals": 0
  }
}
```

## Transaction Endpoints

### 4. Get All Transactions
**Endpoint:** `GET /transactions/`

**Description:** Get user transactions with optional filters.

**Authentication:** Required (Bearer Token)

**Query Parameters:**
- `account_type` (optional): Filter by account type
- `transaction_type` (optional): Filter by transaction type (deposit/withdrawal)
- `goal_id` (optional): Filter by specific goal
- `start_date` (optional): Filter by start date
- `end_date` (optional): Filter by end date
- `limit` (optional): Number of transactions (max 100, default 50)
- `offset` (optional): Offset for pagination (default 0)

### 5. Get Recent Transactions
**Endpoint:** `GET /transactions/recent`

**Description:** Get recent transactions for home screen.

**Authentication:** Required (Bearer Token)

**Query Parameters:**
- `limit` (optional): Number of transactions (max 10, default 5)

### 6. Get Transaction Summary
**Endpoint:** `GET /transactions/summary`

**Description:** Get transaction summary for specified period.

**Authentication:** Required (Bearer Token)

**Query Parameters:**
- `days` (optional): Number of days to look back (1-365, default 30)

## Debug Endpoints

### 7. Transaction Information
**Endpoint:** `GET /debug/transactions-info`

**Description:** Debug endpoint to check transaction data and statistics.

**Authentication:** Required (Bearer Token)

### 8. Create Test Transactions
**Endpoint:** `POST /debug/create-test-transactions`

**Description:** Create test transaction data for debugging.

**Authentication:** Required (Bearer Token)

### 9. Check Transaction Endpoints
**Endpoint:** `GET /debug/check-transaction-endpoints`

**Description:** Check if transaction endpoints are working properly.

**Authentication:** Required (Bearer Token)

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message description"
}
```

## Authentication

All endpoints require authentication using Bearer token:

```
Authorization: Bearer <your_jwt_token>
```

## Testing the Endpoints

You can test these endpoints using tools like Postman, curl, or your frontend application:

```bash
# Get account summary
curl -X GET "http://localhost:8000/account/summary" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get account statement with filters
curl -X GET "http://localhost:8000/account/statement?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get goals progress
curl -X GET "http://localhost:8000/account/goals-progress" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Data Models

### AccountType Enum
- `safelock`: SafeLock goal account
- `mygoal`: MyGoal account
- `emergency`: Emergency fund account
- `flexi`: Flexi account

### TransactionType Enum
- `deposit`: Money deposited into account
- `withdrawal`: Money withdrawn from account

### TransactionStatus Enum
- `pending`: Transaction is pending
- `successful`: Transaction completed successfully
- `failed`: Transaction failed

## Notes

- All monetary amounts are returned as floats
- Dates are returned in ISO 8601 format
- UUIDs are returned as strings
- Pagination is zero-based (offset starts at 0)
- All endpoints are protected and require valid JWT authentication
