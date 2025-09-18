# Paystack Integration Setup Guide

## 🚀 **Updated Auto-Save Feature - Now Using Paystack!**

The auto-save feature has been updated to use **Paystack API** instead of direct mobile money provider APIs. This provides better integration with your existing payment system.

---

## 🔧 **Environment Configuration**

### **Required Environment Variables:**
```bash
# Paystack Configuration
PAYSTACK_SECRET_KEY=sk_test_your_paystack_secret_key_here
PAYSTACK_PUBLIC_KEY=pk_test_your_paystack_public_key_here

# Database Configuration  
DATABASE_URL=postgresql://postgres:password@localhost/DreamBox

# JWT Configuration
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Auto-Save Configuration
AUTO_SAVE_CHECK_INTERVAL=3600  # seconds (1 hour)
MAX_RETRY_ATTEMPTS=3
RETRY_DELAY_HOURS=24
```

---

## 💳 **How Paystack Integration Works**

### **Payment Flow:**
```
1. User sets up auto-save with mobile money number
2. Background scheduler triggers payment at scheduled time
3. Backend calls Paystack API to initialize payment
4. Paystack processes payment through user's mobile money
5. Paystack sends webhook to confirm payment status
6. Backend updates goal balance and transaction records
```

### **Key Benefits:**
- ✅ **Consistent with existing deposits** - Same payment provider
- ✅ **Better error handling** - Paystack's robust error management
- ✅ **Webhook support** - Real-time payment confirmation
- ✅ **Multiple payment methods** - Mobile money, cards, bank transfers
- ✅ **Better analytics** - Paystack dashboard for transaction monitoring

---

## 🔗 **API Endpoints**

### **Auto-Save Management (Unchanged):**
- `POST /auto-save/goals/{goal_id}/auto-save` - Create auto-save
- `GET /auto-save/goals/{goal_id}/auto-save` - Get auto-save setting
- `PUT /auto-save/goals/{goal_id}/auto-save` - Update auto-save
- `DELETE /auto-save/goals/{goal_id}/auto-save` - Delete auto-save
- `GET /auto-save/transactions` - Get transaction history

### **Wallet Management (Unchanged):**
- `GET /wallets/` - Get user wallets
- `POST /wallets/` - Create wallet
- `PUT /wallets/{wallet_id}` - Update wallet
- `DELETE /wallets/{wallet_id}` - Delete wallet
- `PUT /wallets/{wallet_id}/set-default` - Set default wallet

### **New Webhook Endpoint:**
- `POST /webhooks/paystack` - Paystack payment confirmation webhook

---

## 🎯 **Payment Processing**

### **Paystack Payment Initialization:**
```python
# When auto-save is triggered:
payment_result = await paystack_service.process_payment(
    provider=wallet.provider,        # MTN, Telecel, AirtelTigo
    phone_number=wallet.phone_number, # User's mobile money number
    amount=float(auto_save.amount),   # Amount to save
    reference=reference,              # Unique transaction reference
    description=f"Auto-save deposit to {goal.goal_name}"
)
```

### **Paystack API Call:**
```json
POST https://api.paystack.co/transaction/initialize
{
  "amount": 5000,  // Amount in kobo (50.00 GHS)
  "currency": "GHS",
  "reference": "AUTO_SAVE_ABC123",
  "description": "Auto-save deposit to Emergency Fund",
  "customer": {
    "phone": "0241234567"
  },
  "metadata": {
    "provider": "MTN",
    "auto_save": true,
    "description": "Auto-save deposit - AUTO_SAVE_ABC123"
  },
  "channels": ["mobile_money"]
}
```

---

## 🔔 **Webhook Handling**

### **Webhook Events:**
- `charge.success` - Payment completed successfully
- `charge.failed` - Payment failed

### **Webhook Processing:**
```python
# When Paystack sends webhook:
if event_type == "charge.success":
    # Update goal balance
    # Mark transaction as successful
    # Send success notification
    
elif event_type == "charge.failed":
    # Mark transaction as failed
    # Schedule retry
    # Send failure notification
```

### **Webhook Security:**
- **Signature verification** using Paystack secret key
- **HMAC-SHA512** validation
- **Secure endpoint** for payment confirmations

---

## 🛠️ **Setup Instructions**

### **1. Get Paystack Credentials:**
1. Go to [Paystack Dashboard](https://dashboard.paystack.com)
2. Get your **Secret Key** and **Public Key**
3. Set up webhook URL: `https://yourdomain.com/webhooks/paystack`

### **2. Update Environment Variables:**
```bash
# Add to your .env file
PAYSTACK_SECRET_KEY=sk_test_your_actual_secret_key
PAYSTACK_PUBLIC_KEY=pk_test_your_actual_public_key
```

### **3. Configure Webhook:**
- **Webhook URL**: `https://yourdomain.com/webhooks/paystack`
- **Events to send**: `charge.success`, `charge.failed`
- **Secret**: Use your Paystack secret key

### **4. Test Integration:**
```bash
# Test payment initialization
curl -X POST http://localhost:8000/auto-save/goals/{goal_id}/auto-save \
  -H "Authorization: Bearer your_jwt_token" \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_id": "wallet-uuid",
    "frequency": "weekly",
    "time": "09:00",
    "amount": 50.00
  }'
```

---

## 📱 **User Experience**

### **Auto-Save Setup:**
1. **User enters mobile money number** (e.g., 0241234567)
2. **Selects provider** (MTN, Telecel, AirtelTigo)
3. **Sets frequency, time, and amount**
4. **System stores configuration**

### **Auto-Save Execution:**
1. **Background job runs** at scheduled time
2. **Paystack initializes payment** with user's mobile money
3. **User receives SMS** from their mobile money provider
4. **User approves payment** (if required by provider)
5. **Paystack confirms payment** via webhook
6. **Goal balance updates** automatically
7. **User receives notification** of successful auto-save

---

## 🔍 **Monitoring & Analytics**

### **Paystack Dashboard:**
- **Transaction history** - All auto-save payments
- **Success rates** - Payment completion statistics
- **Error analysis** - Failed payment reasons
- **Revenue tracking** - Auto-save amounts collected

### **Backend Logs:**
```python
# Auto-save execution logs
logger.info(f"Processing auto-save {auto_save.id} for goal {goal.id}")
logger.info(f"Paystack payment initialized: {reference}")
logger.info(f"Auto-save successful for goal {goal.id}, amount: {amount}")

# Webhook processing logs
logger.info(f"Received Paystack webhook: {event_type}")
logger.info(f"Successfully processed auto-save payment: {reference}")
```

---

## ⚠️ **Important Notes**

### **Payment Confirmation:**
- **Webhook-based** - Payments confirmed via Paystack webhooks
- **Real-time updates** - Goal balances update immediately
- **Retry logic** - Failed payments retry automatically

### **Security:**
- **Webhook signature verification** - Prevents fake webhooks
- **JWT authentication** - All endpoints require valid tokens
- **Input validation** - Phone numbers and amounts validated

### **Error Handling:**
- **Network timeouts** - 30-second timeout for API calls
- **Payment failures** - Automatic retry in 24 hours
- **Webhook failures** - Logged for manual investigation

---

## 🚀 **Production Deployment**

### **1. Update Environment:**
```bash
# Production Paystack keys
PAYSTACK_SECRET_KEY=sk_live_your_live_secret_key
PAYSTACK_PUBLIC_KEY=pk_live_your_live_public_key
```

### **2. Configure Webhook:**
- **Production URL**: `https://yourdomain.com/webhooks/paystack`
- **SSL required** - Paystack requires HTTPS for webhooks
- **Test webhook** - Verify webhook is receiving events

### **3. Monitor Performance:**
- **Check webhook logs** - Ensure payments are being confirmed
- **Monitor success rates** - Track auto-save completion rates
- **Set up alerts** - Notify on high failure rates

---

## 🎉 **Benefits of Paystack Integration**

### **For Users:**
- **Familiar payment experience** - Same as manual deposits
- **Multiple payment options** - Mobile money, cards, bank transfers
- **Real-time confirmations** - Immediate balance updates
- **Better error messages** - Clear failure reasons

### **For Business:**
- **Unified payment system** - One provider for all payments
- **Better analytics** - Comprehensive transaction reporting
- **Reduced complexity** - No need to manage multiple APIs
- **Improved reliability** - Paystack's robust infrastructure

---

The auto-save feature now seamlessly integrates with your existing Paystack payment system, providing a consistent and reliable experience for your users! 🚀
