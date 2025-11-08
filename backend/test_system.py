#!/usr/bin/env python3
"""
System test script to verify all components are working
Run this after installation to check everything is configured correctly
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_imports():
    """Test that all required packages are installed"""
    print("🔍 Testing imports...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import requests
        import pandas
        import openpyxl
        print("✅ All required packages installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return False


def test_env_variables():
    """Test that environment variables are set"""
    print("\n🔍 Testing environment variables...")

    required_vars = ["UNIPILE_API_KEY"]
    optional_vars = ["DATABASE_URL", "API_HOST", "API_PORT"]

    all_good = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10} (set)")
        else:
            print(f"❌ {var}: Not set (REQUIRED)")
            all_good = False

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (using default)")

    return all_good


def test_database():
    """Test database connection and tables"""
    print("\n🔍 Testing database...")
    try:
        import sqlalchemy
        from database import engine, Base, LinkedInPost, Lead, Comment

        # Check if tables exist
        inspector = sqlalchemy.inspect(engine)
        tables = inspector.get_table_names()

        expected_tables = ['linkedin_posts', 'leads', 'comments', 'unipile_accounts', 'workspaces']

        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"⚠️  Table '{table}' missing - run: python database.py")

        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_unipile_connection():
    """Test connection to Unipile API"""
    print("\n🔍 Testing Unipile API connection...")

    use_mock = os.getenv("USE_MOCK_UNIPILE", "false").lower() == "true"

    if use_mock:
        print("⚠️  Using MOCK Unipile service (set USE_MOCK_UNIPILE=false for real API)")
        from unipile_service import MockUnipileService
        unipile = MockUnipileService()
    else:
        from unipile_service import UnipileService
        unipile = UnipileService()

    try:
        accounts = unipile.get_accounts()

        if accounts:
            print(f"✅ Connected to Unipile - Found {len(accounts)} account(s)")
            for acc in accounts:
                print(f"   - {acc.get('provider')}: {acc.get('username', acc.get('id'))}")
            return True
        else:
            print("⚠️  No accounts found - connect a LinkedIn account in Unipile dashboard")
            return False

    except Exception as e:
        print(f"❌ Unipile connection failed: {e}")
        print("   Check your UNIPILE_API_KEY in .env file")
        return False


def test_api_server():
    """Test if API server can start"""
    print("\n🔍 Testing API server...")
    try:
        from main import app
        print("✅ FastAPI app loaded successfully")
        print("   Run: python main.py")
        print("   Or: uvicorn main:app --reload")
        return True
    except Exception as e:
        print(f"❌ API server error: {e}")
        return False


def test_lead_extractor():
    """Test lead extraction logic"""
    print("\n🔍 Testing lead extraction logic...")
    try:
        from lead_extractor import LeadExtractor
        from unipile_service import MockUnipileService
        from database import SessionLocal

        db = SessionLocal()
        unipile = MockUnipileService()
        extractor = LeadExtractor(db, unipile)

        print("✅ Lead extractor initialized successfully")
        db.close()
        return True
    except Exception as e:
        print(f"❌ Lead extractor error: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("LinkedIn Leads Extractor - System Test")
    print("=" * 60)

    results = {
        "Imports": test_imports(),
        "Environment": test_env_variables(),
        "Database": test_database(),
        "Unipile API": test_unipile_connection(),
        "API Server": test_api_server(),
        "Lead Extractor": test_lead_extractor(),
    }

    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20} {status}")

    all_passed = all(results.values())

    print("=" * 60)

    if all_passed:
        print("🎉 All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Start backend: python main.py")
        print("2. Start frontend: cd ../frontend && npm run dev")
        print("3. Open browser: http://localhost:3000")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install packages: pip install -r requirements.txt")
        print("- Setup .env file: cp .env.example .env")
        print("- Initialize DB: python database.py")
        print("- Add Unipile API key to .env")
        return 1


if __name__ == "__main__":
    sys.exit(main())
