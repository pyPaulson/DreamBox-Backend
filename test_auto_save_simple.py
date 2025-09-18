#!/usr/bin/env python3
"""
Simple test script to verify auto-save functionality
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.auto_save_scheduler import auto_save_scheduler
from app.core.database import SessionLocal
from app.models.auto_save import AutoSaveSetting
from app.models.wallets import Wallet
from app.models.goals import SafeLockAccount
from sqlalchemy import and_

async def test_auto_save_scheduler():
    """Test the auto-save scheduler functionality"""
    print("🧪 Testing auto-save scheduler...")
    
    # Test database connection
    db = SessionLocal()
    try:
        # Check if we have any auto-save settings
        auto_save_count = db.query(AutoSaveSetting).count()
        print(f"📊 Found {auto_save_count} auto-save settings in database")
        
        # Check if we have any wallets
        wallet_count = db.query(Wallet).count()
        print(f"💳 Found {wallet_count} wallets in database")
        
        # Check if we have any goals
        goal_count = db.query(SafeLockAccount).count()
        print(f"🎯 Found {goal_count} SafeLock goals in database")
        
        # Test scheduler initialization
        print("⚙️ Testing scheduler initialization...")
        scheduler = auto_save_scheduler
        print(f"✅ Scheduler initialized: {scheduler}")
        
        # Test next execution calculation
        from datetime import datetime, time, timedelta
        from app.routes.auto_save import calculate_next_execution
        
        test_time = time(9, 0)  # 9:00 AM
        next_exec = calculate_next_execution("weekly", test_time)
        print(f"📅 Next execution calculation test: {next_exec}")
        
        print("✅ Auto-save scheduler test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing auto-save scheduler: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_auto_save_scheduler())
