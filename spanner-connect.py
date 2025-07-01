#!/usr/bin/env python3
"""
Simple Google Cloud Spanner connectivity test script
for LiteLLM token database setup on RHEL9
"""

import os
import sys
from google.cloud import spanner

def test_spanner_connection():
    """Test basic connectivity to Google Cloud Spanner"""
    
    # Configuration - update these values for your setup
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
    INSTANCE_ID = os.getenv('SPANNER_INSTANCE_ID', 'your-instance-id')
    DATABASE_ID = os.getenv('SPANNER_DATABASE_ID', 'your-database-id')
    
    print(f"Testing connection to Spanner...")
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_ID}")
    print(f"Database: {DATABASE_ID}")
    print("-" * 50)
    
    try:
        # Initialize Spanner client
        spanner_client = spanner.Client(project=PROJECT_ID)
        print("✓ Spanner client initialized")
        
        # Get instance reference
        instance = spanner_client.instance(INSTANCE_ID)
        print("✓ Instance reference obtained")
        
        # Check if instance exists
        if instance.exists():
            print("✓ Instance exists and is accessible")
        else:
            print("✗ Instance does not exist or is not accessible")
            return False
        
        # Get database reference
        database = instance.database(DATABASE_ID)
        print("✓ Database reference obtained")
        
        # Check if database exists
        if database.exists():
            print("✓ Database exists and is accessible")
        else:
            print("✗ Database does not exist or is not accessible")
            return False
        
        # Test a simple query to verify connection
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql("SELECT 1 as test_column")
            for row in results:
                print(f"✓ Query executed successfully: {row[0]}")
        
        print("\n🎉 Spanner connectivity test PASSED!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection test FAILED: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False

def check_prerequisites():
    """Check if required packages and credentials are available"""
    print("Checking prerequisites...")
    
    # Check if google-cloud-spanner is installed
    try:
        import google.cloud.spanner
        print("✓ google-cloud-spanner package is available")
    except ImportError:
        print("✗ google-cloud-spanner package not found")
        print("  Install with: pip install google-cloud-spanner")
        return False
    
    # Check for authentication
    cred_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if cred_file:
        print(f"✓ Service account key file: {cred_file}")
        if not os.path.exists(cred_file):
            print("✗ Service account key file does not exist")
            return False
    else:
        print("! No GOOGLE_APPLICATION_CREDENTIALS set - using default credentials")
    
    return True

def main():
    print("=" * 60)
    print("Google Cloud Spanner Connectivity Test for LiteLLM")
    print("=" * 60)
    
    # Check prerequisites first
    if not check_prerequisites():
        print("\nPlease install required packages and set up authentication:")
        print("1. pip install google-cloud-spanner")
        print("2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("3. Or run: gcloud auth application-default login")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    
    # Test connection
    success = test_spanner_connection()
    
    if success:
        print("\nNext steps:")
        print("- Set up LiteLLM token database schema")
        print("- Configure LiteLLM to use this Spanner database")
        sys.exit(0)
    else:
        print("\nTroubleshooting:")
        print("- Verify project, instance, and database IDs")
        print("- Check IAM permissions (Spanner Database User role)")
        print("- Ensure Spanner API is enabled")
        sys.exit(1)

if __name__ == "__main__":
    main()
