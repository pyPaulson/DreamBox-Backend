"""
Setup script for auto-save feature
Run this script to set up the auto-save feature in your DreamBox backend
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_requirements():
    """Check if required dependencies are installed"""
    print("🔍 Checking requirements...")
    
    required_packages = [
        "fastapi",
        "sqlalchemy",
        "psycopg2-binary",
        "pydantic",
        "httpx",
        "python-multipart"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them using: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All required packages are installed")
    return True

def setup_database():
    """Set up database tables"""
    print("🗄️ Setting up database...")
    
    # Check if migrations directory exists
    migrations_dir = Path("migrations")
    if not migrations_dir.exists():
        print("❌ Migrations directory not found")
        return False
    
    # List migration files
    migration_files = list(migrations_dir.glob("*.sql"))
    if not migration_files:
        print("❌ No migration files found")
        return False
    
    print(f"📁 Found {len(migration_files)} migration files")
    
    # Note: In a real setup, you would run these migrations against your database
    # For now, we'll just show what needs to be done
    print("📋 Migration files to run:")
    for file in sorted(migration_files):
        print(f"   - {file.name}")
    
    print("\n⚠️  Manual step required:")
    print("Please run the migration files against your PostgreSQL database:")
    print("psql -d your_database_name -f migrations/001_create_wallets_table.sql")
    print("psql -d your_database_name -f migrations/002_create_auto_save_tables.sql")
    
    return True

def setup_environment():
    """Set up environment variables"""
    print("🔧 Setting up environment variables...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_content = """# Database
DATABASE_URL=postgresql://postgres:password@localhost/DreamBox

# Mobile Money API Keys (replace with your actual keys)
MTN_API_KEY=your_mtn_api_key_here
TELECEL_API_KEY=your_telecel_api_key_here
AIRTELTIGO_API_KEY=your_airteltigo_api_key_here

# Background Job Settings
AUTO_SAVE_CHECK_INTERVAL=3600

# JWT Settings (if not already set)
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")
    
    print("\n⚠️  Please update the .env file with your actual values:")
    print("   - Database connection string")
    print("   - Mobile money API keys")
    print("   - JWT secret key")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "logs",
        "uploads/auto_save_logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created {directory}")
    
    return True

def show_next_steps():
    """Show next steps for the user"""
    print("\n" + "="*60)
    print("🎉 Auto-save feature setup completed!")
    print("="*60)
    
    print("\n📋 Next steps:")
    print("1. Update your .env file with actual values")
    print("2. Run database migrations:")
    print("   psql -d your_database_name -f migrations/001_create_wallets_table.sql")
    print("   psql -d your_database_name -f migrations/002_create_auto_save_tables.sql")
    print("3. Start your FastAPI server:")
    print("   uvicorn app.main:app --reload")
    print("4. Start the background job scheduler:")
    print("   python app/background_jobs.py")
    print("5. Test the API endpoints using the test script:")
    print("   python test_auto_save.py")
    
    print("\n📚 Documentation:")
    print("- API Documentation: AUTO_SAVE_API_DOCUMENTATION.md")
    print("- Test Script: test_auto_save.py")
    print("- Background Jobs: app/background_jobs.py")
    
    print("\n🔧 Configuration:")
    print("- Wallet providers: MTN, Telecel, AirtelTigo")
    print("- Auto-save frequencies: daily, weekly, monthly")
    print("- Amount limits: 1.00 - 10,000.00 GHS")
    print("- Max auto-save settings per user: 10")
    
    print("\n🚀 Your auto-save feature is ready to use!")

def main():
    """Main setup function"""
    print("🚀 DreamBox Auto-Save Feature Setup")
    print("="*40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        sys.exit(1)
    
    # Show next steps
    show_next_steps()

if __name__ == "__main__":
    main()
