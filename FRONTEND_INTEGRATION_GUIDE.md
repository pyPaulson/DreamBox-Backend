# Frontend Integration Guide - Auto-Save Feature

## 🚀 Overview
This guide provides everything the frontend team needs to integrate the auto-save feature with the DreamBox backend API.

## 📋 Prerequisites
- Backend server running on `http://localhost:8000` (or your deployed URL)
- User authentication with JWT tokens
- Existing goal management functionality

---

## 🔗 API Endpoints Summary

### Base URL
```
http://localhost:8000
```

### Authentication
All requests require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

---

## 💳 Wallet Management

### 1. Get User Wallets
```http
GET /wallets/
```

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
```http
POST /wallets/
```

**Request Body:**
```json
{
  "provider": "MTN",
  "phone_number": "0241234567",
  "account_name": "John Doe",
  "is_default": false
}
```

**Validation Rules:**
- `provider`: Must be "MTN", "Telecel", or "AirtelTigo"
- `phone_number`: Ghanaian format (0241234567, 0201234567, etc.)
- `account_name`: Minimum 2 characters
- `is_default`: Boolean

### 3. Update Wallet
```http
PUT /wallets/{wallet_id}
```

### 4. Delete Wallet
```http
DELETE /wallets/{wallet_id}
```

### 5. Set Default Wallet
```http
PUT /wallets/{wallet_id}/set-default
```

---

## 🔄 Auto-Save Management

### 1. Create Auto-Save Setting
```http
POST /auto-save/goals/{goal_id}/auto-save
```

**Request Body:**
```json
{
  "wallet_id": "uuid",
  "frequency": "weekly",
  "time": "09:00",
  "amount": 50.00
}
```

**Validation Rules:**
- `frequency`: "daily", "weekly", or "monthly"
- `time`: HH:MM format (00:00 to 23:59)
- `amount`: 1.00 to 10,000.00
- One auto-save per goal maximum
- Maximum 10 auto-save settings per user

### 2. Update Auto-Save Setting
```http
PUT /auto-save/goals/{goal_id}/auto-save
```

### 3. Delete Auto-Save Setting
```http
DELETE /auto-save/goals/{goal_id}/auto-save
```

### 4. Get Auto-Save Setting
```http
GET /auto-save/goals/{goal_id}/auto-save
```

### 5. Get Auto-Save Transaction History
```http
GET /auto-save/transactions?goal_id={goal_id}&limit=20&offset=0
```

**Query Parameters:**
- `goal_id` (optional): Filter by specific goal
- `limit` (optional): 1-100, default 20
- `offset` (optional): Default 0

---

## 🎨 Frontend Implementation Examples

### React/TypeScript Example

#### 1. Wallet Management Component
```typescript
interface Wallet {
  id: string;
  provider: 'MTN' | 'Telecel' | 'AirtelTigo';
  phone_number: string;
  account_name: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

interface CreateWalletRequest {
  provider: 'MTN' | 'Telecel' | 'AirtelTigo';
  phone_number: string;
  account_name: string;
  is_default: boolean;
}

// API Service
class WalletService {
  private baseUrl = 'http://localhost:8000';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private getHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }

  async getWallets(): Promise<{ wallets: Wallet[] }> {
    const response = await fetch(`${this.baseUrl}/wallets/`, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  async createWallet(wallet: CreateWalletRequest): Promise<Wallet> {
    const response = await fetch(`${this.baseUrl}/wallets/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(wallet)
    });
    return response.json();
  }

  async updateWallet(walletId: string, wallet: Partial<CreateWalletRequest>): Promise<Wallet> {
    const response = await fetch(`${this.baseUrl}/wallets/${walletId}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(wallet)
    });
    return response.json();
  }

  async deleteWallet(walletId: string): Promise<void> {
    await fetch(`${this.baseUrl}/wallets/${walletId}`, {
      method: 'DELETE',
      headers: this.getHeaders()
    });
  }

  async setDefaultWallet(walletId: string): Promise<void> {
    await fetch(`${this.baseUrl}/wallets/${walletId}/set-default`, {
      method: 'PUT',
      headers: this.getHeaders()
    });
  }
}
```

#### 2. Auto-Save Management Component
```typescript
interface AutoSaveSetting {
  id: string;
  wallet_id: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  time: string; // HH:MM format
  amount: number;
  is_active: boolean;
  next_execution: string | null;
  created_at: string;
  updated_at: string;
}

interface CreateAutoSaveRequest {
  wallet_id: string;
  frequency: 'daily' | 'weekly' | 'monthly';
  time: string;
  amount: number;
}

interface AutoSaveTransaction {
  id: string;
  amount: number;
  status: 'pending' | 'success' | 'failed' | 'cancelled';
  payment_reference: string | null;
  error_message: string | null;
  executed_at: string;
}

class AutoSaveService {
  private baseUrl = 'http://localhost:8000';
  private token: string;

  constructor(token: string) {
    this.token = token;
  }

  private getHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json'
    };
  }

  async createAutoSave(goalId: string, autoSave: CreateAutoSaveRequest): Promise<AutoSaveSetting> {
    const response = await fetch(`${this.baseUrl}/auto-save/goals/${goalId}/auto-save`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(autoSave)
    });
    return response.json();
  }

  async updateAutoSave(goalId: string, autoSave: Partial<CreateAutoSaveRequest>): Promise<AutoSaveSetting> {
    const response = await fetch(`${this.baseUrl}/auto-save/goals/${goalId}/auto-save`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(autoSave)
    });
    return response.json();
  }

  async deleteAutoSave(goalId: string): Promise<void> {
    await fetch(`${this.baseUrl}/auto-save/goals/${goalId}/auto-save`, {
      method: 'DELETE',
      headers: this.getHeaders()
    });
  }

  async getAutoSave(goalId: string): Promise<AutoSaveSetting> {
    const response = await fetch(`${this.baseUrl}/auto-save/goals/${goalId}/auto-save`, {
      headers: this.getHeaders()
    });
    return response.json();
  }

  async getAutoSaveTransactions(goalId?: string, limit = 20, offset = 0): Promise<{
    transactions: AutoSaveTransaction[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString()
    });
    
    if (goalId) {
      params.append('goal_id', goalId);
    }

    const response = await fetch(`${this.baseUrl}/auto-save/transactions?${params}`, {
      headers: this.getHeaders()
    });
    return response.json();
  }
}
```

#### 3. React Component Example
```tsx
import React, { useState, useEffect } from 'react';

interface AutoSaveSetupProps {
  goalId: string;
  token: string;
}

const AutoSaveSetup: React.FC<AutoSaveSetupProps> = ({ goalId, token }) => {
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [autoSave, setAutoSave] = useState<AutoSaveSetting | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const walletService = new WalletService(token);
  const autoSaveService = new AutoSaveService(token);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [walletsData, autoSaveData] = await Promise.all([
        walletService.getWallets(),
        autoSaveService.getAutoSave(goalId).catch(() => null)
      ]);
      
      setWallets(walletsData.wallets);
      setAutoSave(autoSaveData);
    } catch (err) {
      setError('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAutoSave = async (formData: CreateAutoSaveRequest) => {
    try {
      setLoading(true);
      const newAutoSave = await autoSaveService.createAutoSave(goalId, formData);
      setAutoSave(newAutoSave);
      setError(null);
    } catch (err) {
      setError('Failed to create auto-save setting');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAutoSave = async () => {
    try {
      setLoading(true);
      await autoSaveService.deleteAutoSave(goalId);
      setAutoSave(null);
      setError(null);
    } catch (err) {
      setError('Failed to delete auto-save setting');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="auto-save-setup">
      <h3>Auto-Save Settings</h3>
      
      {autoSave ? (
        <div className="existing-auto-save">
          <p>Auto-save is active</p>
          <p>Frequency: {autoSave.frequency}</p>
          <p>Amount: GHS {autoSave.amount}</p>
          <p>Time: {autoSave.time}</p>
          <p>Next execution: {autoSave.next_execution}</p>
          <button onClick={handleDeleteAutoSave}>Disable Auto-Save</button>
        </div>
      ) : (
        <AutoSaveForm 
          wallets={wallets}
          onSubmit={handleCreateAutoSave}
        />
      )}
    </div>
  );
};

const AutoSaveForm: React.FC<{
  wallets: Wallet[];
  onSubmit: (data: CreateAutoSaveRequest) => void;
}> = ({ wallets, onSubmit }) => {
  const [formData, setFormData] = useState<CreateAutoSaveRequest>({
    wallet_id: '',
    frequency: 'weekly',
    time: '09:00',
    amount: 50
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Wallet:</label>
        <select 
          value={formData.wallet_id} 
          onChange={(e) => setFormData({...formData, wallet_id: e.target.value})}
          required
        >
          <option value="">Select a wallet</option>
          {wallets.map(wallet => (
            <option key={wallet.id} value={wallet.id}>
              {wallet.provider} - {wallet.phone_number} ({wallet.account_name})
            </option>
          ))}
        </select>
      </div>

      <div>
        <label>Frequency:</label>
        <select 
          value={formData.frequency} 
          onChange={(e) => setFormData({...formData, frequency: e.target.value as any})}
        >
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
        </select>
      </div>

      <div>
        <label>Time:</label>
        <input 
          type="time" 
          value={formData.time} 
          onChange={(e) => setFormData({...formData, time: e.target.value})}
          required
        />
      </div>

      <div>
        <label>Amount (GHS):</label>
        <input 
          type="number" 
          min="1" 
          max="10000" 
          step="0.01" 
          value={formData.amount} 
          onChange={(e) => setFormData({...formData, amount: parseFloat(e.target.value)})}
          required
        />
      </div>

      <button type="submit">Enable Auto-Save</button>
    </form>
  );
};

export default AutoSaveSetup;
```

---

## 📱 Mobile App Integration (React Native)

### 1. API Service (React Native)
```typescript
// services/AutoSaveService.ts
import AsyncStorage from '@react-native-async-storage/async-storage';

class AutoSaveService {
  private baseUrl = 'http://localhost:8000'; // Replace with your API URL

  private async getAuthHeaders() {
    const token = await AsyncStorage.getItem('auth_token');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async getWallets() {
    const response = await fetch(`${this.baseUrl}/wallets/`, {
      headers: await this.getAuthHeaders()
    });
    return response.json();
  }

  async createAutoSave(goalId: string, autoSaveData: any) {
    const response = await fetch(`${this.baseUrl}/auto-save/goals/${goalId}/auto-save`, {
      method: 'POST',
      headers: await this.getAuthHeaders(),
      body: JSON.stringify(autoSaveData)
    });
    return response.json();
  }

  // ... other methods
}

export default new AutoSaveService();
```

### 2. React Native Component
```tsx
// components/AutoSaveSetup.tsx
import React, { useState, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert } from 'react-native';
import AutoSaveService from '../services/AutoSaveService';

const AutoSaveSetup = ({ goalId }) => {
  const [wallets, setWallets] = useState([]);
  const [autoSave, setAutoSave] = useState(null);
  const [formData, setFormData] = useState({
    wallet_id: '',
    frequency: 'weekly',
    time: '09:00',
    amount: 50
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const walletsData = await AutoSaveService.getWallets();
      setWallets(walletsData.wallets);
      
      // Try to get existing auto-save
      try {
        const autoSaveData = await AutoSaveService.getAutoSave(goalId);
        setAutoSave(autoSaveData);
      } catch (err) {
        // No auto-save exists yet
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to load data');
    }
  };

  const handleSubmit = async () => {
    try {
      const result = await AutoSaveService.createAutoSave(goalId, formData);
      setAutoSave(result);
      Alert.alert('Success', 'Auto-save enabled successfully!');
    } catch (error) {
      Alert.alert('Error', 'Failed to enable auto-save');
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 20 }}>
        Auto-Save Settings
      </Text>
      
      {autoSave ? (
        <View>
          <Text>Auto-save is active</Text>
          <Text>Frequency: {autoSave.frequency}</Text>
          <Text>Amount: GHS {autoSave.amount}</Text>
          <Text>Time: {autoSave.time}</Text>
        </View>
      ) : (
        <View>
          <Text>Wallet:</Text>
          {/* Wallet picker component */}
          
          <Text>Frequency:</Text>
          {/* Frequency picker */}
          
          <Text>Time:</Text>
          <TextInput
            value={formData.time}
            onChangeText={(text) => setFormData({...formData, time: text})}
            placeholder="09:00"
          />
          
          <Text>Amount (GHS):</Text>
          <TextInput
            value={formData.amount.toString()}
            onChangeText={(text) => setFormData({...formData, amount: parseFloat(text)})}
            keyboardType="numeric"
            placeholder="50"
          />
          
          <TouchableOpacity onPress={handleSubmit}>
            <Text>Enable Auto-Save</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
};

export default AutoSaveSetup;
```

---

## 🎯 UI/UX Recommendations

### 1. Wallet Management Screen
- **List View**: Show all wallets with provider icons
- **Add Wallet**: Form with provider selection and phone number input
- **Default Wallet**: Clear indication of which wallet is default
- **Edit/Delete**: Swipe actions or context menus

### 2. Auto-Save Setup Screen
- **Goal Selection**: Show goal details (name, target amount, current amount)
- **Wallet Selection**: Dropdown/picker with wallet details
- **Frequency Picker**: Visual selector (daily/weekly/monthly)
- **Time Picker**: Native time picker component
- **Amount Input**: Number input with validation
- **Preview**: Show next execution time
- **Enable/Disable**: Clear toggle button

### 3. Auto-Save Status
- **Active Indicator**: Show if auto-save is active for a goal
- **Next Execution**: Display when next auto-save will occur
- **Last Transaction**: Show last auto-save transaction status
- **Quick Actions**: Enable/disable auto-save

### 4. Transaction History
- **List View**: Show auto-save transactions with status indicators
- **Filtering**: Filter by goal, status, date range
- **Status Icons**: Success ✅, Failed ❌, Pending ⏳
- **Details**: Tap to see transaction details

---

## 🔔 Notification Integration

### 1. Auto-Save Success Notification
```json
{
  "title": "Auto-Save Successful! 🎉",
  "message": "GHS 50.00 has been automatically added to your Emergency Fund goal.",
  "type": "auto_save_success",
  "data": {
    "goal_id": "uuid",
    "amount": 50.00,
    "goal_name": "Emergency Fund"
  }
}
```

### 2. Auto-Save Failure Notification
```json
{
  "title": "Auto-Save Failed",
  "message": "Auto-save failed: Insufficient funds in your MTN wallet. Please add funds and try again.",
  "type": "auto_save_failed",
  "data": {
    "goal_id": "uuid",
    "error": "insufficient_funds"
  }
}
```

---

## ⚠️ Error Handling

### Common Error Responses
```json
// 400 Bad Request
{
  "detail": "Phone number must be in Ghanaian format (e.g., 0241234567)"
}

// 404 Not Found
{
  "detail": "Goal not found"
}

// 400 Bad Request
{
  "detail": "Maximum of 10 auto-save settings allowed per user"
}
```

### Frontend Error Handling
```typescript
const handleApiError = (error: any) => {
  if (error.response?.status === 400) {
    // Show validation error
    setError(error.response.data.detail);
  } else if (error.response?.status === 404) {
    // Show not found error
    setError('Resource not found');
  } else {
    // Show generic error
    setError('Something went wrong. Please try again.');
  }
};
```

---

## 🧪 Testing

### 1. Test Data
```typescript
const testWallet = {
  provider: 'MTN',
  phone_number: '0241234567',
  account_name: 'Test User',
  is_default: false
};

const testAutoSave = {
  wallet_id: 'wallet-uuid',
  frequency: 'weekly',
  time: '09:00',
  amount: 50.00
};
```

### 2. Test Scenarios
- Create wallet with valid data
- Create wallet with invalid phone number
- Set default wallet
- Create auto-save setting
- Update auto-save setting
- Delete auto-save setting
- View transaction history

---

## 🚀 Deployment Checklist

### 1. Environment Variables
```bash
# Update API base URL for production
REACT_APP_API_URL=https://your-api-domain.com
```

### 2. Build Configuration
```json
// package.json
{
  "scripts": {
    "build": "react-scripts build",
    "start": "react-scripts start"
  }
}
```

### 3. Production Considerations
- Use HTTPS for API calls
- Implement proper error boundaries
- Add loading states
- Implement offline handling
- Add analytics tracking

---

## 📞 Support

If you encounter any issues during integration:

1. **Check API Documentation**: `AUTO_SAVE_API_DOCUMENTATION.md`
2. **Test with Postman**: Use the provided examples
3. **Check Backend Logs**: Look for error messages
4. **Verify Authentication**: Ensure JWT tokens are valid
5. **Database Migrations**: Ensure all migrations are run

---

## 🎉 Success Criteria

Your integration is successful when:
- ✅ Users can create and manage wallets
- ✅ Users can enable auto-save for goals
- ✅ Auto-save settings are displayed correctly
- ✅ Transaction history is shown
- ✅ Error handling works properly
- ✅ Notifications are received
- ✅ UI/UX is intuitive and responsive

Good luck with the integration! 🚀
