"""
Simple test script to verify auto-save functionality
Run this after setting up the database and starting the server
"""

import requests
import json
from datetime import datetime, time

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_TOKEN = "your_test_jwt_token_here"  # Replace with actual token

headers = {
    "Authorization": f"Bearer {TEST_USER_TOKEN}",
    "Content-Type": "application/json"
}


def test_wallet_management():
    """Test wallet CRUD operations"""
    print("Testing wallet management...")
    
    # Create a test wallet
    wallet_data = {
        "provider": "MTN",
        "phone_number": "0241234567",
        "account_name": "Test User",
        "is_default": True
    }
    
    response = requests.post(f"{BASE_URL}/wallets/", json=wallet_data, headers=headers)
    print(f"Create wallet: {response.status_code}")
    
    if response.status_code == 201:
        wallet = response.json()
        wallet_id = wallet["id"]
        print(f"Created wallet: {wallet_id}")
        
        # Get wallets
        response = requests.get(f"{BASE_URL}/wallets/", headers=headers)
        print(f"Get wallets: {response.status_code}")
        
        # Update wallet
        update_data = {
            "account_name": "Updated Test User"
        }
        response = requests.put(f"{BASE_URL}/wallets/{wallet_id}", json=update_data, headers=headers)
        print(f"Update wallet: {response.status_code}")
        
        return wallet_id
    else:
        print(f"Error creating wallet: {response.text}")
        return None


def test_auto_save_management(wallet_id, goal_id):
    """Test auto-save CRUD operations"""
    print("Testing auto-save management...")
    
    # Create auto-save setting
    auto_save_data = {
        "wallet_id": wallet_id,
        "frequency": "weekly",
        "time": "09:00",
        "amount": 50.00
    }
    
    response = requests.post(
        f"{BASE_URL}/auto-save/goals/{goal_id}/auto-save", 
        json=auto_save_data, 
        headers=headers
    )
    print(f"Create auto-save: {response.status_code}")
    
    if response.status_code == 201:
        auto_save = response.json()
        print(f"Created auto-save: {auto_save['id']}")
        
        # Get auto-save setting
        response = requests.get(f"{BASE_URL}/auto-save/goals/{goal_id}/auto-save", headers=headers)
        print(f"Get auto-save: {response.status_code}")
        
        # Update auto-save setting
        update_data = {
            "amount": 100.00,
            "frequency": "monthly"
        }
        response = requests.put(
            f"{BASE_URL}/auto-save/goals/{goal_id}/auto-save", 
            json=update_data, 
            headers=headers
        )
        print(f"Update auto-save: {response.status_code}")
        
        # Get transaction history
        response = requests.get(f"{BASE_URL}/auto-save/transactions", headers=headers)
        print(f"Get transactions: {response.status_code}")
        
        return True
    else:
        print(f"Error creating auto-save: {response.text}")
        return False


def test_validation_errors():
    """Test validation error handling"""
    print("Testing validation errors...")
    
    # Test invalid phone number
    invalid_wallet_data = {
        "provider": "MTN",
        "phone_number": "1234567890",  # Invalid format
        "account_name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/wallets/", json=invalid_wallet_data, headers=headers)
    print(f"Invalid phone number: {response.status_code}")
    
    # Test invalid amount
    invalid_auto_save_data = {
        "wallet_id": "00000000-0000-0000-0000-000000000000",
        "frequency": "weekly",
        "time": "09:00",
        "amount": 0.50  # Below minimum
    }
    
    response = requests.post(
        f"{BASE_URL}/auto-save/goals/00000000-0000-0000-0000-000000000000/auto-save", 
        json=invalid_auto_save_data, 
        headers=headers
    )
    print(f"Invalid amount: {response.status_code}")


def main():
    """Run all tests"""
    print("Starting auto-save feature tests...")
    print("=" * 50)
    
    # Test wallet management
    wallet_id = test_wallet_management()
    print()
    
    # Test validation errors
    test_validation_errors()
    print()
    
    if wallet_id:
        # You'll need to replace this with an actual goal ID from your database
        goal_id = "00000000-0000-0000-0000-000000000000"  # Replace with actual goal ID
        print(f"Note: Replace goal_id with an actual goal ID from your database")
        print(f"Using test goal_id: {goal_id}")
        
        # Test auto-save management
        test_auto_save_management(wallet_id, goal_id)
    
    print()
    print("=" * 50)
    print("Tests completed!")
    print()
    print("Next steps:")
    print("1. Replace TEST_USER_TOKEN with a real JWT token")
    print("2. Replace goal_id with an actual goal ID from your database")
    print("3. Run the background job scheduler: python app/background_jobs.py")
    print("4. Test the mobile money integration with real API keys")


if __name__ == "__main__":
    main()
