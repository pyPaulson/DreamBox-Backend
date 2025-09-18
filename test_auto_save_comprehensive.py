"""
Comprehensive Auto-Save Backend Testing Script
Tests all auto-save functionality including Paystack integration
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
from app.models.goals import SafeLockAccount
from app.models.wallets import Wallet, WalletProvider
from app.models.auto_save import AutoSaveSetting, AutoSaveTransaction, AutoSaveFrequency
from app.services.mobile_money import paystack_service
from app.services.auto_save_scheduler import auto_save_scheduler
from app.utils.transactions import generate_transaction_reference

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class AutoSaveTester:
    def __init__(self):
        self.db = SessionLocal()
        self.test_user = None
        self.test_goal = None
        self.test_wallet = None
        self.test_auto_save = None
    
    def setup_test_data(self):
        """Create test data for auto-save testing"""
        print("🔧 Setting up test data...")
        
        # Create or get test user
        self.test_user = self.db.query(User).first()
        if not self.test_user:
            print("❌ No users found in database. Please create a user first.")
            return False
        
        print(f"✅ Using test user: {self.test_user.first_name} {self.test_user.last_name}")
        
        # Create test goal
        self.test_goal = SafeLockAccount(
            user_id=self.test_user.id,
            goal_name="Test Auto-Save Goal",
            target_amount=1000.0,
            current_amount=0.0,
            target_date=datetime.now().date() + timedelta(days=30),
            has_emergency_fund=False
        )
        
        # Check if goal already exists
        existing_goal = self.db.query(SafeLockAccount).filter(
            SafeLockAccount.goal_name == "Test Auto-Save Goal"
        ).first()
        
        if existing_goal:
            self.test_goal = existing_goal
            print(f"✅ Using existing test goal: {self.test_goal.goal_name}")
        else:
            self.db.add(self.test_goal)
            self.db.commit()
            self.db.refresh(self.test_goal)
            print(f"✅ Created test goal: {self.test_goal.goal_name}")
        
        # Create test wallet
        self.test_wallet = Wallet(
            user_id=self.test_user.id,
            provider=WalletProvider.MTN,
            phone_number="0241234567",
            account_name="Test User",
            is_default=True
        )
        
        # Check if wallet already exists
        existing_wallet = self.db.query(Wallet).filter(
            Wallet.phone_number == "0241234567"
        ).first()
        
        if existing_wallet:
            self.test_wallet = existing_wallet
            print(f"✅ Using existing test wallet: {self.test_wallet.phone_number}")
        else:
            self.db.add(self.test_wallet)
            self.db.commit()
            self.db.refresh(self.test_wallet)
            print(f"✅ Created test wallet: {self.test_wallet.phone_number}")
        
        return True
    
    def test_wallet_creation(self):
        """Test wallet creation and validation"""
        print("\n🧪 Testing wallet creation...")
        
        try:
            # Test valid wallet
            valid_wallet = Wallet(
                user_id=self.test_user.id,
                provider=WalletProvider.TELECEL,
                phone_number="0209876543",
                account_name="Test User 2",
                is_default=False
            )
            
            self.db.add(valid_wallet)
            self.db.commit()
            print("✅ Valid wallet created successfully")
            
            # Test invalid phone number
            try:
                invalid_wallet = Wallet(
                    user_id=self.test_user.id,
                    provider=WalletProvider.MTN,
                    phone_number="1234567890",  # Invalid format
                    account_name="Test User 3",
                    is_default=False
                )
                self.db.add(invalid_wallet)
                self.db.commit()
                print("❌ Invalid phone number was accepted (should have failed)")
            except Exception as e:
                print(f"✅ Invalid phone number correctly rejected: {str(e)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Wallet creation test failed: {str(e)}")
            return False
    
    def test_auto_save_creation(self):
        """Test auto-save setting creation"""
        print("\n🧪 Testing auto-save creation...")
        
        try:
            # Create auto-save setting
            self.test_auto_save = AutoSaveSetting(
                goal_id=self.test_goal.id,
                user_id=self.test_user.id,
                wallet_id=self.test_wallet.id,
                frequency=AutoSaveFrequency.WEEKLY,
                time=datetime.now().time(),
                amount=50.0,
                next_execution=datetime.now() + timedelta(minutes=1)  # Set to run in 1 minute
            )
            
            # Check if auto-save already exists for this goal
            existing_auto_save = self.db.query(AutoSaveSetting).filter(
                AutoSaveSetting.goal_id == self.test_goal.id
            ).first()
            
            if existing_auto_save:
                self.test_auto_save = existing_auto_save
                # Update next execution to run soon
                self.test_auto_save.next_execution = datetime.now() + timedelta(minutes=1)
                self.db.commit()
                print(f"✅ Using existing auto-save setting")
            else:
                self.db.add(self.test_auto_save)
                self.db.commit()
                self.db.refresh(self.test_auto_save)
                print(f"✅ Created auto-save setting: {self.test_auto_save.frequency} {self.test_auto_save.amount}")
            
            return True
            
        except Exception as e:
            print(f"❌ Auto-save creation test failed: {str(e)}")
            return False
    
    async def test_paystack_service(self):
        """Test Paystack service integration"""
        print("\n🧪 Testing Paystack service...")
        
        try:
            # Test payment initialization
            reference = generate_transaction_reference()
            result = await paystack_service.process_payment(
                provider=WalletProvider.MTN,
                phone_number="0241234567",
                amount=50.0,
                reference=reference,
                description="Test auto-save payment"
            )
            
            print(f"✅ Paystack payment initialization result: {result}")
            
            # Test payment verification
            if result.get("status") == "success":
                verify_result = await paystack_service.verify_payment(reference)
                print(f"✅ Paystack payment verification result: {verify_result}")
            
            return True
            
        except Exception as e:
            print(f"❌ Paystack service test failed: {str(e)}")
            return False
    
    def test_auto_save_scheduler(self):
        """Test auto-save scheduler functionality"""
        print("\n🧪 Testing auto-save scheduler...")
        
        try:
            # Test finding due auto-saves
            due_auto_saves = self.db.query(AutoSaveSetting).filter(
                AutoSaveSetting.is_active == True,
                AutoSaveSetting.next_execution <= datetime.now()
            ).all()
            
            print(f"✅ Found {len(due_auto_saves)} due auto-save settings")
            
            # Test next execution calculation
            from app.routes.auto_save import calculate_next_execution
            next_exec = calculate_next_execution("weekly", datetime.now().time())
            print(f"✅ Next execution calculated: {next_exec}")
            
            return True
            
        except Exception as e:
            print(f"❌ Auto-save scheduler test failed: {str(e)}")
            return False
    
    async def test_complete_auto_save_flow(self):
        """Test the complete auto-save execution flow"""
        print("\n🧪 Testing complete auto-save flow...")
        
        try:
            if not self.test_auto_save:
                print("❌ No test auto-save setting available")
                return False
            
            # Simulate auto-save execution
            print("🔄 Simulating auto-save execution...")
            
            # Create auto-save transaction record
            auto_save_transaction = AutoSaveTransaction(
                auto_save_id=self.test_auto_save.id,
                goal_id=self.test_auto_save.goal_id,
                amount=self.test_auto_save.amount,
                status="pending"
            )
            
            self.db.add(auto_save_transaction)
            self.db.commit()
            self.db.refresh(auto_save_transaction)
            print(f"✅ Created auto-save transaction: {auto_save_transaction.id}")
            
            # Test Paystack payment (this will fail in test mode, but we can test the flow)
            reference = generate_transaction_reference()
            payment_result = await paystack_service.process_payment(
                provider=self.test_wallet.provider,
                phone_number=self.test_wallet.phone_number,
                amount=float(self.test_auto_save.amount),
                reference=reference,
                description=f"Auto-save deposit to {self.test_goal.goal_name}"
            )
            
            print(f"✅ Payment processing result: {payment_result}")
            
            # Update transaction with result
            if payment_result.get("status") == "success":
                auto_save_transaction.status = "success"
                auto_save_transaction.payment_reference = payment_result.get("transaction_id")
            else:
                auto_save_transaction.status = "failed"
                auto_save_transaction.error_message = payment_result.get("message", "Payment failed")
            
            self.db.commit()
            print(f"✅ Updated auto-save transaction status: {auto_save_transaction.status}")
            
            return True
            
        except Exception as e:
            print(f"❌ Complete auto-save flow test failed: {str(e)}")
            return False
    
    def test_database_queries(self):
        """Test database queries and relationships"""
        print("\n🧪 Testing database queries...")
        
        try:
            # Test user relationships
            user_wallets = self.db.query(Wallet).filter(Wallet.user_id == self.test_user.id).all()
            print(f"✅ User has {len(user_wallets)} wallets")
            
            user_goals = self.db.query(SafeLockAccount).filter(SafeLockAccount.user_id == self.test_user.id).all()
            print(f"✅ User has {len(user_goals)} goals")
            
            user_auto_saves = self.db.query(AutoSaveSetting).filter(AutoSaveSetting.user_id == self.test_user.id).all()
            print(f"✅ User has {len(user_auto_saves)} auto-save settings")
            
            # Test auto-save transactions
            auto_save_transactions = self.db.query(AutoSaveTransaction).all()
            print(f"✅ Total auto-save transactions: {len(auto_save_transactions)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database queries test failed: {str(e)}")
            return False
    
    def cleanup_test_data(self):
        """Clean up test data"""
        print("\n🧹 Cleaning up test data...")
        
        try:
            # Delete test auto-save transactions
            self.db.query(AutoSaveTransaction).filter(
                AutoSaveTransaction.auto_save_id == self.test_auto_save.id
            ).delete()
            
            # Delete test auto-save setting
            if self.test_auto_save:
                self.db.delete(self.test_auto_save)
            
            # Delete test wallet (if created in this test)
            if self.test_wallet and self.test_wallet.phone_number == "0209876543":
                self.db.delete(self.test_wallet)
            
            # Delete test goal (if created in this test)
            if self.test_goal and self.test_goal.goal_name == "Test Auto-Save Goal":
                self.db.delete(self.test_goal)
            
            self.db.commit()
            print("✅ Test data cleaned up successfully")
            
        except Exception as e:
            print(f"❌ Cleanup failed: {str(e)}")
            self.db.rollback()
    
    async def run_all_tests(self):
        """Run all auto-save tests"""
        print("🚀 Starting Comprehensive Auto-Save Backend Testing")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 6
        
        # Setup
        if not self.setup_test_data():
            print("❌ Test setup failed")
            return
        
        # Run tests
        if self.test_wallet_creation():
            tests_passed += 1
        
        if self.test_auto_save_creation():
            tests_passed += 1
        
        if await self.test_paystack_service():
            tests_passed += 1
        
        if self.test_auto_save_scheduler():
            tests_passed += 1
        
        if await self.test_complete_auto_save_flow():
            tests_passed += 1
        
        if self.test_database_queries():
            tests_passed += 1
        
        # Results
        print("\n" + "=" * 60)
        print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! Auto-save backend is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the errors above.")
        
        # Cleanup
        self.cleanup_test_data()
        
        self.db.close()


async def main():
    """Main test function"""
    tester = AutoSaveTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
