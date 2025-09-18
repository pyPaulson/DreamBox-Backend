# Auto-Save Feature API Documentation

## Overview
The auto-save feature allows users to automatically deposit money to their savings goals at scheduled intervals using mobile money wallets.

## Base URL
```
http://localhost:8000
```

## Authentication
All endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Wallet Management

### 1. Get User Wallets
**GET** `/wallets/`

Returns all wallets for the authenticated user.

**Response:**
```json
{
  "wallets": [
    {
      "id": "uuid",
      "provider": "MTN",
      "phone_number": "0241234567",
      "account_name": "John Doe",
      "is_default": true,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### 2. Create Wallet
**POST** `/wallets/`

Creates a new wallet for the authenticated user.

**Request Body:**
```json
{
  "provider": "MTN",
  "phone_number": "0241234567",
  "account_name": "John Doe",
  "is_default": false
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "provider": "MTN",
  "phone_number": "0241234567",
  "account_name": "John Doe",
  "is_default": false,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Validation Rules:**
- Phone number must be in Ghanaian format (e.g., 0241234567)
- Valid prefixes: 024, 020, 027, 055, 059, 054, 056, 057
- Account name must be at least 2 characters
- Provider must be one of: MTN, Telecel, AirtelTigo

### 3. Update Wallet
**PUT** `/wallets/{wallet_id}`

Updates an existing wallet.

**Request Body:** (Same as create, all fields optional)

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "provider": "MTN",
  "phone_number": "0241234567",
  "account_name": "John Doe Updated",
  "is_default": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### 4. Delete Wallet
**DELETE** `/wallets/{wallet_id}`

Deletes a wallet. Cannot delete if used in active auto-save settings.

**Response:** `200 OK`
```json
{
  "message": "Wallet deleted successfully"
}
```

### 5. Set Default Wallet
**PUT** `/wallets/{wallet_id}/set-default`

Sets a wallet as the default wallet for the user.

**Response:** `200 OK`
```json
{
  "message": "Default wallet updated successfully"
}
```

---

## Auto-Save Management

### 1. Create Auto-Save Setting
**POST** `/auto-save/goals/{goal_id}/auto-save`

Creates an auto-save setting for a specific goal.

**Request Body:**
```json
{
  "wallet_id": "uuid",
  "frequency": "weekly",
  "time": "09:00",
  "amount": 50.00
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "wallet_id": "uuid",
  "frequency": "weekly",
  "time": "09:00",
  "amount": 50.00,
  "is_active": true,
  "next_execution": "2024-01-22T09:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Validation Rules:**
- Amount: 1.00 - 10,000.00
- Frequency: daily, weekly, monthly
- Time: HH:MM format (00:00 to 23:59)
- Maximum 10 auto-save settings per user
- One auto-save setting per goal

### 2. Update Auto-Save Setting
**PUT** `/auto-save/goals/{goal_id}/auto-save`

Updates an existing auto-save setting.

**Request Body:** (Same as create, all fields optional)

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "wallet_id": "uuid",
  "frequency": "monthly",
  "time": "10:00",
  "amount": 100.00,
  "is_active": true,
  "next_execution": "2024-02-15T10:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### 3. Delete Auto-Save Setting
**DELETE** `/auto-save/goals/{goal_id}/auto-save`

Disables auto-save for a goal.

**Response:** `200 OK`
```json
{
  "message": "Auto-save disabled successfully"
}
```

### 4. Get Auto-Save Setting
**GET** `/auto-save/goals/{goal_id}/auto-save`

Gets the auto-save setting for a specific goal.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "wallet_id": "uuid",
  "frequency": "weekly",
  "time": "09:00",
  "amount": 50.00,
  "is_active": true,
  "next_execution": "2024-01-22T09:00:00Z",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 5. Get Auto-Save Transaction History
**GET** `/auto-save/transactions`

Gets the auto-save transaction history for the authenticated user.

**Query Parameters:**
- `goal_id` (optional): Filter by specific goal ID
- `limit` (optional): Number of transactions to return (1-100, default: 20)
- `offset` (optional): Number of transactions to skip (default: 0)

**Response:** `200 OK`
```json
{
  "transactions": [
    {
      "id": "uuid",
      "amount": 50.00,
      "status": "success",
      "payment_reference": "MTN123456789",
      "error_message": null,
      "executed_at": "2024-01-15T09:00:00Z"
    }
  ],
  "total": 25,
  "limit": 20,
  "offset": 0
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Error message describing the validation error"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Auto-Save Execution Logic

### Next Execution Calculation
- **Daily**: Next day at the same time
- **Weekly**: Next week on the same day and time
- **Monthly**: Next month on the same day and time

### Payment Processing
1. Validate goal is still active and not completed
2. Process payment through mobile money API
3. Update goal balance if successful
4. Log transaction result
5. Calculate and set next execution timestamp
6. Send notification to user

### Retry Logic
- Failed payments are retried in 24 hours
- Maximum 3 retry attempts
- Auto-save is paused if goal is completed
- Auto-save is disabled if user disables it

---

## Mobile Money Integration

### Supported Providers
- **MTN Mobile Money**
- **Telecel Cash**
- **AirtelTigo Money**

### Payment Flow
1. Validate wallet and amount
2. Initiate payment request to mobile money provider
3. Handle payment response (success/failure)
4. Update goal balance if successful
5. Send push notification to user
6. Log transaction details

### Error Handling
- Insufficient funds in wallet
- Network issues with mobile money API
- Invalid/expired wallet
- Goal completed or deleted
- User disabled auto-save
- Mobile money service unavailable

---

## Background Job Processing

### Scheduler
- Runs every hour to check for due auto-save executions
- Processes all active auto-save settings where `next_execution <= NOW()`
- Handles payment processing and goal updates
- Manages retry logic for failed payments

### Running the Scheduler
```bash
python app/background_jobs.py
```

### Logging
- All auto-save executions are logged
- Payment results are tracked
- Error messages are recorded for debugging

---

## Database Schema

### Wallets Table
```sql
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('MTN', 'Telecel', 'AirtelTigo')),
    phone_number VARCHAR(15) NOT NULL,
    account_name VARCHAR(100) NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, phone_number, provider)
);
```

### Auto-Save Settings Table
```sql
CREATE TABLE auto_save_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES "safeLock_account"(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    wallet_id UUID NOT NULL REFERENCES wallets(id) ON DELETE CASCADE,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('daily', 'weekly', 'monthly')),
    time TIME NOT NULL,
    amount DECIMAL(10,2) NOT NULL CHECK (amount > 0),
    is_active BOOLEAN DEFAULT TRUE,
    next_execution TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(goal_id)
);
```

### Auto-Save Transactions Table
```sql
CREATE TABLE auto_save_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auto_save_id UUID NOT NULL REFERENCES auto_save_settings(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES "safeLock_account"(id) ON DELETE CASCADE,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'success', 'failed', 'cancelled')),
    payment_reference VARCHAR(100),
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Testing

### Test Cases
1. **Wallet Management**
   - Create/update/delete wallets
   - Set default wallet
   - Phone number validation
   - Provider validation

2. **Auto-Save Settings**
   - Enable/disable auto-save for goals
   - Update auto-save settings
   - Frequency and time validation
   - Amount validation

3. **Auto-Save Execution**
   - Successful auto-save execution
   - Failed auto-save execution
   - Goal completion handling
   - Retry logic

4. **Error Handling**
   - Insufficient funds
   - Network issues
   - Invalid wallets
   - Goal not found

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

---

## Deployment

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dreambox

# Mobile Money API Keys
MTN_API_KEY=your_mtn_api_key
TELECEL_API_KEY=your_telecel_api_key
AIRTELTIGO_API_KEY=your_airteltigo_api_key

# Background Job Settings
AUTO_SAVE_CHECK_INTERVAL=3600  # seconds
```

### Production Setup
1. Run database migrations
2. Start the main FastAPI application
3. Start the background job scheduler
4. Configure monitoring and logging
5. Set up mobile money provider credentials

### Monitoring
- Monitor auto-save execution success rates
- Track payment failure reasons
- Monitor background job health
- Set up alerts for critical failures
