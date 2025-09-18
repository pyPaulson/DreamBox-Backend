# Frontend Setup Instructions - Auto-Save Feature

## 🚀 Quick Start Guide

### 1. **Import Postman Collection**
1. Open Postman
2. Click "Import" button
3. Select `AutoSave_API_Postman_Collection.json`
4. Update the `authToken` variable with a valid JWT token
5. Update `baseUrl` if your backend is not running on localhost:8000

### 2. **Test API Endpoints**
Run these requests in order to test the API:
#### Step 1: Create a Wallet
```http
POST /wallets/
{
  "provider": "MTN",
  "phone_number": "0241234567",
  "account_name": "Test User",
  "is_default": true
}
```
- Copy the `id` from response and set it as `walletId` variable in Postman

#### Step 2: Get a Goal ID
- Use your existing goal endpoints to get a goal ID
- Set it as `goalId` variable in Postman

#### Step 3: Create Auto-Save Setting
```http
POST /auto-save/goals/{goalId}/auto-save
{
  "wallet_id": "walletId_from_step_1",
  "frequency": "weekly",
  "time": "09:00",
  "amount": 50.00
}
```

#### Step 4: Test Other Endpoints
- Get auto-save setting
- Update auto-save setting
- Get transaction history
- Delete auto-save setting

### 3. **Frontend Integration**

#### For React/Next.js:
```bash
# Install dependencies (if not already installed)
npm install axios
# or
npm install fetch

# Copy the service classes from FRONTEND_INTEGRATION_GUIDE.md
# Implement the React components as shown in the guide
```

#### For React Native:
```bash
# Install dependencies
npm install @react-native-async-storage/async-storage

# Copy the service classes from FRONTEND_INTEGRATION_GUIDE.md
# Implement the React Native components as shown in the guide
```

### 4. **Environment Setup**

#### Create `.env` file:
```bash
# For React/Next.js
REACT_APP_API_URL=http://localhost:8000
# or for production
REACT_APP_API_URL=https://your-api-domain.com

# For React Native
API_URL=http://localhost:8000
# or for production
API_URL=https://your-api-domain.com
```

### 5. **Authentication Setup**

Make sure your app can:
1. Get JWT tokens from your auth system
2. Store tokens securely (AsyncStorage for React Native, localStorage for web)
3. Include tokens in API requests:
```javascript
headers: {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
}
```

---

## 📋 Implementation Checklist

### Phase 1: Basic Integration
- [ ] Import Postman collection and test all endpoints
- [ ] Create API service classes (WalletService, AutoSaveService)
- [ ] Implement basic wallet management UI
- [ ] Implement basic auto-save setup UI
- [ ] Test with real data

### Phase 2: Enhanced Features
- [ ] Add form validation
- [ ] Implement error handling
- [ ] Add loading states
- [ ] Create transaction history view
- [ ] Add notification handling

### Phase 3: Polish & Testing
- [ ] Add proper error messages
- [ ] Implement offline handling
- [ ] Add analytics tracking
- [ ] Test on different devices
- [ ] Performance optimization

---

## 🔧 Common Issues & Solutions

### Issue 1: "Cannot specify Depends in Annotated and default value together"
**Solution**: This was a backend issue that has been fixed. Make sure you're using the latest backend code.

### Issue 2: "Goal not found" error
**Solution**: 
- Make sure the goal ID exists in your database
- Verify the goal belongs to the authenticated user
- Check that you're using the correct goal ID format (UUID)

### Issue 3: "Wallet not found" error
**Solution**:
- Create a wallet first using the wallet endpoints
- Make sure the wallet belongs to the authenticated user
- Verify the wallet ID is correct

### Issue 4: "Maximum of 10 auto-save settings allowed per user"
**Solution**:
- This is a business rule limit
- Delete existing auto-save settings if you need to create more
- Or increase the limit in the backend if needed

### Issue 5: Phone number validation errors
**Solution**:
- Use Ghanaian phone number format: 0241234567, 0201234567, etc.
- Valid prefixes: 024, 020, 027, 055, 059, 054, 056, 057
- Remove any spaces or dashes from the phone number

---

## 📱 UI/UX Best Practices

### 1. **Wallet Management**
- Show provider icons (MTN, Telecel, AirtelTigo)
- Display phone numbers in a readable format
- Clearly indicate which wallet is default
- Provide easy edit/delete actions

### 2. **Auto-Save Setup**
- Show goal information (name, target amount, current amount)
- Use native time pickers
- Provide frequency selection with clear labels
- Show preview of next execution time
- Validate amounts in real-time

### 3. **Status Display**
- Use clear status indicators (Active/Inactive)
- Show next execution time
- Display last transaction status
- Provide quick enable/disable actions

### 4. **Error Handling**
- Show specific error messages
- Provide actionable error messages
- Use toast notifications for success/error states
- Implement retry mechanisms where appropriate

---

## 🧪 Testing Strategy

### 1. **Unit Tests**
```javascript
// Example test for wallet service
describe('WalletService', () => {
  it('should create wallet with valid data', async () => {
    const walletData = {
      provider: 'MTN',
      phone_number: '0241234567',
      account_name: 'Test User',
      is_default: false
    };
    
    const result = await walletService.createWallet(walletData);
    expect(result.id).toBeDefined();
    expect(result.provider).toBe('MTN');
  });
});
```

### 2. **Integration Tests**
- Test complete user flows
- Test error scenarios
- Test with different data combinations
- Test on different devices/browsers

### 3. **User Acceptance Tests**
- Test with real users
- Gather feedback on UI/UX
- Test accessibility
- Test performance

---

## 📞 Support & Resources

### Documentation Files:
- `FRONTEND_INTEGRATION_GUIDE.md` - Complete integration guide
- `AUTO_SAVE_API_DOCUMENTATION.md` - API documentation
- `AutoSave_API_Postman_Collection.json` - Postman collection

### Backend Files:
- `app/routes/wallets.py` - Wallet endpoints
- `app/routes/auto_save.py` - Auto-save endpoints
- `app/models/wallets.py` - Wallet models
- `app/models/auto_save.py` - Auto-save models

### Test Files:
- `test_auto_save.py` - Backend test script
- `setup_auto_save.py` - Backend setup script

---

## 🎯 Success Metrics

Your integration is successful when:
- ✅ All API endpoints work correctly
- ✅ Users can create and manage wallets
- ✅ Users can enable/disable auto-save
- ✅ Auto-save settings are displayed correctly
- ✅ Transaction history is shown
- ✅ Error handling works properly
- ✅ UI/UX is intuitive and responsive
- ✅ App works on both web and mobile
- ✅ Performance is acceptable
- ✅ Users can complete the full flow without issues

---

## 🚀 Next Steps

1. **Start with Postman testing** to understand the API
2. **Implement basic service classes** for API communication
3. **Create simple UI components** for wallet and auto-save management
4. **Add form validation and error handling**
5. **Test with real data and users**
6. **Polish the UI/UX based on feedback**
7. **Add advanced features like notifications and analytics**

Good luck with the integration! 🎉
