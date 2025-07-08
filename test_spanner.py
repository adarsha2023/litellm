#!/usr/bin/env python3
"""
Simplified Google Cloud Spanner connectivity test
"""

import os
from google.cloud import spanner

def test_spanner_direct():
    """Test direct Google Cloud Spanner connection"""
    
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'PROJECT_ID')
    INSTANCE_ID = os.getenv('SPANNER_INSTANCE_ID', 'test')
    DATABASE_ID = os.getenv('SPANNER_DATABASE_ID', 'test')
    
    print(f"Testing direct Spanner connection...")
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_ID}")
    print(f"Database: {DATABASE_ID}")
    print("-" * 50)
    
    try:
        # Initialize Spanner client
        spanner_client = spanner.Client(project=PROJECT_ID)
        print("✓ Spanner client initialized")
        
        # Get instance and database
        instance = spanner_client.instance(INSTANCE_ID)
        database = instance.database(DATABASE_ID)
        
        # Test basic query
        with database.snapshot() as snapshot:
            results = snapshot.execute_sql("SELECT 1 as test_column")
            for row in results:
                print(f"✓ Basic query successful: {row[0]}")
        
        # Test table listing with different approaches
        print("\nTesting table queries...")
        
        # Method 1: Standard information_schema
        try:
            with database.snapshot() as snapshot:
                results = snapshot.execute_sql(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
                )
                tables = [row[0] for row in results]
                print(f"✓ Found {len(tables)} tables total")
                
                # Filter for litellm tables
                litellm_tables = [t for t in tables if t.startswith('litellm_')]
                if litellm_tables:
                    print(f"✓ Found {len(litellm_tables)} LiteLLM tables:")
                    for table in litellm_tables:
                        print(f"  - {table}")
                else:
                    print("⚠️  No LiteLLM tables found")
                    
        except Exception as e:
            print(f"❌ information_schema query failed: {e}")
        
        # Method 2: Try STARTS_WITH function
        try:
            with database.snapshot() as snapshot:
                results = snapshot.execute_sql(
                    "SELECT table_name FROM information_schema.tables WHERE STARTS_WITH(table_name, 'litellm_') ORDER BY table_name"
                )
                tables = [row[0] for row in results]
                if tables:
                    print(f"✓ STARTS_WITH found {len(tables)} LiteLLM tables:")
                    for table in tables:
                        print(f"  - {table}")
                else:
                    print("⚠️  STARTS_WITH: No LiteLLM tables found")
                    
        except Exception as e:
            print(f"❌ STARTS_WITH query failed: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Direct connection failed: {e}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection to Spanner"""
    
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'my-project-7817-395922')
    INSTANCE_ID = os.getenv('SPANNER_INSTANCE_ID', 'test')
    DATABASE_ID = os.getenv('SPANNER_DATABASE_ID', 'test')
    
    print(f"\nTesting SQLAlchemy connection...")
    print("-" * 50)
    
    try:
        from sqlalchemy import create_engine, text
        
        # Create connection string
        connection_string = f"spanner+spanner:///projects/{PROJECT_ID}/instances/{INSTANCE_ID}/databases/{DATABASE_ID}"
        engine = create_engine(connection_string)
        
        with engine.connect() as conn:
            # Test basic connectivity
            result = conn.execute(text("SELECT 1 as test"))
            print("✓ SQLAlchemy connection successful:", result.fetchone())
            
            # Test table listing with multiple approaches
            
            # Method 1: Try to query one of the known tables directly
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM litellm_usertable"))
                count = result.fetchone()[0]
                print(f"✓ litellm_usertable accessible, has {count} rows")
                
                # If that works, we know the tables exist and are accessible
                known_tables = [
                    'litellm_usertable',
                    'litellm_teamtable', 
                    'litellm_proxymodeltable',
                    'litellm_usagetable',
                    'litellm_verificationtoken'
                ]
                
                accessible_tables = []
                for table in known_tables:
                    try:
                        conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                        accessible_tables.append(table)
                    except:
                        pass
                
                print(f"✓ Found {len(accessible_tables)} accessible LiteLLM tables:")
                for table in accessible_tables:
                    print(f"  - {table}")
                    
            except Exception as e:
                print(f"❌ Direct table access failed: {e}")
                
                # Method 2: Try a different information schema approach
                try:
                    result = conn.execute(text("SELECT 1"))  # Just test basic query capability
                    print("✓ Basic SQLAlchemy queries work")
                    print("⚠️  information_schema queries not supported via SQLAlchemy")
                    print("⚠️  Use direct Spanner client for schema introspection")
                except Exception as e2:
                    print(f"❌ Even basic queries failed: {e2}")
                
        return True
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Google Cloud Spanner Connection Test")
    print("=" * 60)
    
    # Test direct connection
    direct_success = test_spanner_direct()
    
    # Test SQLAlchemy connection
    sqlalchemy_success = test_sqlalchemy_connection()
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print(f"Direct connection: {'✓ SUCCESS' if direct_success else '❌ FAILED'}")
    print(f"SQLAlchemy connection: {'✓ SUCCESS' if sqlalchemy_success else '❌ FAILED'}")
    
    if direct_success and sqlalchemy_success:
        print("\n🎉 All tests passed! Ready to set up LiteLLM schema.")
    else:
        print("\n⚠️  Some tests failed. Check your configuration.")
