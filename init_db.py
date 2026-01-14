"""\nDatabase initialization script\nRun this to set up the SQLite database for the CAPE Demo application\nDeveloped by [Julian Kaljuvee](https://kaljuvee.github.io)\n"""

import os
import sys
from utils.db_utils import init_database, cleanup_expired_cache

def main():
    """Initialize the database and perform setup tasks"""
    
    print("🗄️  Initializing CAPE Demo Database...")
    
    # Create db directory if it doesn't exist
    if not os.path.exists('db'):
        os.makedirs('db')
        print("✅ Created 'db' directory")
    
    # Initialize database tables
    try:
        init_database()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)
    
    # Clean up any expired cache entries
    try:
        cleaned_count = cleanup_expired_cache()
        print(f"✅ Cleaned up {cleaned_count} expired cache entries")
    except Exception as e:
        print(f"⚠️  Warning: Could not clean cache: {e}")
    
    print("\n🎉 Database initialization complete!")
    print("You can now run the Streamlit application with: streamlit run Home.py")

if __name__ == "__main__":
    main()
