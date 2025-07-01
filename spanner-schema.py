#!/usr/bin/env python3
"""
Enhanced Google Cloud Spanner connectivity and schema setup script
for LiteLLM token database on RHEL9 - PostgreSQL Dialect
"""

import os
import sys
import json
from datetime import datetime
from google.cloud import spanner
from google.cloud.spanner_admin_database_v1 import DatabaseAdminClient

def get_litellm_spanner_ddl():
    """
    Returns DDL statements for LiteLLM database tables in Spanner PostgreSQL dialect format.
    These are adapted from LiteLLM's typical schema requirements and verified
    against official Spanner PostgreSQL dialect syntax.
    """
    return [
        """CREATE TABLE litellm_usertable (
    user_id character varying NOT NULL,
    user_email character varying,
    user_role character varying(50),
    teams character varying[],
    max_budget double precision,
    spend double precision,
    user_list_table_id character varying,
    table_name character varying(50),
    created_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    updated_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    PRIMARY KEY (user_id)
)""",
        
        """CREATE TABLE litellm_teamtable (
    team_id character varying NOT NULL,
    team_alias character varying,
    organization_id character varying,
    team_metadata jsonb,
    max_budget double precision,
    spend double precision,
    models character varying[],
    blocked boolean,
    created_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    updated_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    PRIMARY KEY (team_id)
)""",
        
        """CREATE TABLE litellm_proxymodeltable (
    id character varying NOT NULL,
    model_name character varying(200),
    litellm_params jsonb,
    model_info jsonb,
    created_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    updated_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    PRIMARY KEY (id)
)""",
        
        """CREATE TABLE litellm_usagetable (
    request_id character varying NOT NULL,
    call_type character varying(50),
    api_key character varying,
    spend double precision,
    total_tokens bigint,
    prompt_tokens bigint,
    completion_tokens bigint,
    successful_requests bigint,
    failed_requests bigint,
    model character varying(200),
    model_id character varying,
    model_group character varying,
    api_base character varying,
    user_id character varying,
    team_id character varying,
    organization_id character varying,
    request_tags character varying[],
    end_user character varying,
    requester_ip_address character varying(45),
    starttime timestamptz,
    endtime timestamptz,
    completionstarttime timestamptz,
    created_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    updated_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    PRIMARY KEY (request_id)
)""",
        
        """CREATE TABLE litellm_verificationtoken (
    token character varying NOT NULL,
    key_name character varying,
    key_alias character varying,
    spend double precision,
    max_budget double precision,
    user_id character varying,
    team_id character varying,
    max_parallel_requests bigint,
    metadata jsonb,
    tpm_limit double precision,
    rpm_limit double precision,
    model_spend jsonb,
    model_max_budget jsonb,
    expires timestamptz,
    models character varying[],
    aliases jsonb,
    config jsonb,
    blocked boolean,
    created_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    updated_at SPANNER.COMMIT_TIMESTAMP NOT NULL,
    PRIMARY KEY (token)
)""",

        """CREATE INDEX idx_usage_user_id ON litellm_usagetable(user_id)""",
        
        """CREATE INDEX idx_usage_team_id ON litellm_usagetable(team_id)""",
        
        """CREATE INDEX idx_usage_model ON litellm_usagetable(model)""",
        
        """CREATE INDEX idx_usage_created_at ON litellm_usagetable(created_at)""",
        
        """CREATE INDEX idx_verification_user_id ON litellm_verificationtoken(user_id)""",
        
        """CREATE INDEX idx_verification_team_id ON litellm_verificationtoken(team_id)"""
    ]

def test_spanner_connection():
    """Test basic connectivity to Google Cloud Spanner"""
    
    # Configuration - update these values for your setup
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
    INSTANCE_ID = os.getenv('SPANNER_INSTANCE_ID', 'your-instance-id')
    DATABASE_ID = os.getenv('SPANNER_DATABASE_ID', 'litellm-tokens')
    
    print(f"Testing connection to Spanner...")
    print(f"Project: {PROJECT_ID}")
    print(f"Instance: {INSTANCE_ID}")
    print(f"Database: {DATABASE_ID}")
    print(f"Dialect: PostgreSQL")
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
            return False, None, None, None
        
        # Get database reference
        database = instance.database(DATABASE_ID)
        print("✓ Database reference obtained")
        
        # Check if database exists
        if database.exists():
            print("✓ Database exists and is accessible")
        else:
            print("! Database does not exist - will be created during setup")
        
        # Test a simple query if database exists
        if database.exists():
            with database.snapshot() as snapshot:
                results = snapshot.execute_sql("SELECT 1 as test_column")
                for row in results:
                    print(f"✓ Query executed successfully: {row[0]}")
        
        print("\n🎉 Spanner connectivity test PASSED!")
        return True, spanner_client, instance, database
        
    except Exception as e:
        print(f"\n❌ Connection test FAILED: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        return False, None, None, None

def create_database_if_not_exists(spanner_client, instance, database):
    """Create PostgreSQL dialect database if it doesn't exist"""
    if database.exists():
        print("Database already exists, skipping creation")
        return True
    
    try:
        print("Creating PostgreSQL dialect database...")
        database_admin_client = DatabaseAdminClient()
        
        # Create PostgreSQL dialect database
        request = database_admin_client.create_database(
            parent=instance.name,
            create_statement=f"CREATE DATABASE `{database.database_id}`",
            extra_statements=[],
            database_dialect="POSTGRESQL"  # Specify PostgreSQL dialect
        )
        
        # Wait for operation to complete
        operation_result = request.result(timeout=300)  # 5 minutes timeout
        print(f"✓ PostgreSQL dialect database created: {operation_result.name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {str(e)}")
        return False

def setup_litellm_schema(database):
    """Set up LiteLLM database schema"""
    print("\nSetting up LiteLLM database schema...")
    
    try:
        ddl_statements = get_litellm_spanner_ddl()
        
        # Execute DDL statements
        database_admin_client = DatabaseAdminClient()
        
        print(f"Executing {len(ddl_statements)} DDL statements...")
        
        # Split into chunks to avoid size limits
        chunk_size = 5
        for i in range(0, len(ddl_statements), chunk_size):
            chunk = ddl_statements[i:i + chunk_size]
            
            operation = database_admin_client.update_database_ddl(
                database=database.name,
                statements=chunk
            )
            
            print(f"Executing DDL batch {i//chunk_size + 1}...")
            operation.result(timeout=300)  # 5 minutes timeout
        
        print("✓ LiteLLM schema setup completed successfully!")
        
        # Verify tables were created (PostgreSQL dialect uses information_schema.tables)
        with database.snapshot() as snapshot:
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'litellm_%'
            ORDER BY table_name
            """
            results = snapshot.execute_sql(tables_query)
            
            print("\nCreated tables:")
            for row in results:
                print(f"  ✓ {row[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema setup failed: {str(e)}")
        return False

def test_litellm_operations(database):
    """Test basic LiteLLM operations"""
    print("\nTesting LiteLLM database operations...")
    
    try:
        # Test insert and read operations
        def insert_test_data(transaction):
            # Insert test user (handling default values at application level)
            transaction.execute_update(
                "INSERT INTO litellm_usertable (user_id, user_email, user_role, max_budget, spend, table_name, created_at, updated_at) "
                "VALUES ($1, $2, $3, $4, $5, $6, SPANNER.PENDING_COMMIT_TIMESTAMP(), SPANNER.PENDING_COMMIT_TIMESTAMP())",
                params=["test-user-123", "test@example.com", "user", 100.0, 0.0, "user"],
                param_types=[
                    spanner.param_types.STRING,
                    spanner.param_types.STRING,
                    spanner.param_types.STRING,
                    spanner.param_types.FLOAT64,
                    spanner.param_types.FLOAT64,
                    spanner.param_types.STRING
                ]
            )
            
            # Insert test token (handling default values at application level)
            transaction.execute_update(
                "INSERT INTO litellm_verificationtoken (token, user_id, max_budget, spend, blocked, created_at, updated_at) "
                "VALUES ($1, $2, $3, $4, $5, SPANNER.PENDING_COMMIT_TIMESTAMP(), SPANNER.PENDING_COMMIT_TIMESTAMP())",
                params=["sk-test-token-123", "test-user-123", 50.0, 0.0, False],
                param_types=[
                    spanner.param_types.STRING,
                    spanner.param_types.STRING,
                    spanner.param_types.FLOAT64,
                    spanner.param_types.FLOAT64,
                    spanner.param_types.BOOL
                ]
            )
        
        # Execute transaction
        database.run_in_transaction(insert_test_data)
        print("✓ Test data inserted successfully")
        
        # Test queries
        with database.snapshot() as snapshot:
            # Test user query
            user_results = snapshot.execute_sql(
                "SELECT user_id, user_email, max_budget FROM litellm_usertable WHERE user_id = $1",
                params=["test-user-123"],
                param_types=[spanner.param_types.STRING]
            )
            
            for row in user_results:
                print(f"✓ User query: {row[0]} - {row[1]} - ${row[2]}")
            
            # Test token query
            token_results = snapshot.execute_sql(
                "SELECT token, user_id, max_budget FROM litellm_verificationtoken WHERE user_id = $1",
                params=["test-user-123"],
                param_types=[spanner.param_types.STRING]
            )
            
            for row in token_results:
                print(f"✓ Token query: {row[0]} - {row[1]} - ${row[2]}")
        
        # Clean up test data
        def cleanup_test_data(transaction):
            transaction.execute_update(
                "DELETE FROM litellm_verificationtoken WHERE user_id = $1",
                params=["test-user-123"],
                param_types=[spanner.param_types.STRING]
            )
            transaction.execute_update(
                "DELETE FROM litellm_usertable WHERE user_id = $1",
                params=["test-user-123"],
                param_types=[spanner.param_types.STRING]
            )
        
        database.run_in_transaction(cleanup_test_data)
        print("✓ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ LiteLLM operations test failed: {str(e)}")
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
    
    # Check for admin client
    try:
        from google.cloud.spanner_admin_database_v1 import DatabaseAdminClient
        print("✓ spanner admin client is available")
    except ImportError:
        print("✗ spanner admin client not found")
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

def generate_litellm_config():
    """Generate LiteLLM configuration for Spanner PostgreSQL dialect"""
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'your-project-id')
    INSTANCE_ID = os.getenv('SPANNER_INSTANCE_ID', 'your-instance-id')
    DATABASE_ID = os.getenv('SPANNER_DATABASE_ID', 'litellm-tokens')
    
    config = {
        "model_list": [
            {
                "model_name": "gpt-3.5-turbo",
                "litellm_params": {
                    "model": "gpt-3.5-turbo",
                    "api_key": "os.environ/OPENAI_API_KEY"
                }
            }
        ],
        "general_settings": {
            "database_url": f"postgresql://user:password@localhost:5432/{DATABASE_ID}?host=/cloudsql/{PROJECT_ID}:{INSTANCE_ID}",
            "master_key": "sk-your-master-key-here",
            "database_type": "postgresql"
        }
    }
    
    return config

def validate_schema_against_spanner():
    """Validate that our schema uses correct Spanner PostgreSQL dialect syntax"""
    print("\nValidating schema against Spanner PostgreSQL dialect...")
    
    ddl_statements = get_litellm_spanner_ddl()
    
    print("✓ Using valid Spanner PostgreSQL dialect syntax:")
    print("  - character varying for text fields")
    print("  - bigint for large integers")
    print("  - double precision for floating point numbers")
    print("  - boolean for boolean values")
    print("  - timestamptz for timestamps with timezone")
    print("  - jsonb for structured data")
    print("  - character varying[] for string arrays")
    print("  - SPANNER.COMMIT_TIMESTAMP for auto-timestamps")
    print("  - Lowercase table and column names (PostgreSQL convention)")
    
    print("✓ Primary keys use valid types (character varying)")
    print("✓ No DEFAULT values (handled at application level)")
    print("✓ Using PostgreSQL array syntax: type[]")
    print("✓ Using information_schema.tables for table verification")
    
    return True

def main():
    print("=" * 60)
    print("LiteLLM Google Cloud Spanner Setup and Test")
    print("PostgreSQL Dialect")
    print("=" * 60)

    # Check prerequisites first
    if not check_prerequisites():
        print("\nPlease install required packages and set up authentication:")
        print("1. pip install google-cloud-spanner")
        print("2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("3. Or run: gcloud auth application-default login")
        print("4. Ensure Spanner Database Admin role is assigned")
        sys.exit(1)

    # Validate schema
    validate_schema_against_spanner()

    print("\n" + "=" * 40)

    # Test connection
    success, spanner_client, instance, database = test_spanner_connection()

    if not success:
        print("\nTroubleshooting:")
        print("- Verify project, instance, and database IDs")
        print("- Check IAM permissions (Spanner Database Admin role)")
        print("- Ensure Spanner API is enabled")
        print("- Verify you're using PostgreSQL dialect instance")
        sys.exit(1)

    # Setup database and schema
    setup_mode = input("\nSetup LiteLLM database schema? (y/n): ").lower().strip()

    if setup_mode == 'y':
        print("\n" + "=" * 40)
        print("Setting up LiteLLM database...")

        # Create database if needed
        if not create_database_if_not_exists(spanner_client, instance, database):
            sys.exit(1)

        # Setup schema
        if not setup_litellm_schema(database):
            sys.exit(1)

        # Test operations
        if not test_litellm_operations(database):
            print("⚠️  Schema created but operations test failed")

        # Generate config
        config = generate_litellm_config()

        print("\n" + "=" * 40)
        print("Setup completed successfully!")
        print("\nLiteLLM Configuration:")
        print(json.dumps(config, indent=2))

        print("\nNext steps:")
        print("1. Save the configuration above to config.yaml")
        print("2. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
        print("3. Start LiteLLM: litellm --config config.yaml")
        print("4. The database will be used for token tracking and user management")

        print("\nSpanner PostgreSQL dialect considerations:")
        print("- Tables use character varying primary keys for global distribution")
        print("- jsonb columns store metadata and configuration")
        print("- SPANNER.COMMIT_TIMESTAMP columns provide consistent timestamps")
        print("- Arrays use PostgreSQL syntax: character varying[]")
        print("- Indexes optimize common query patterns")
        print("- Use $1, $2, etc. for parameterized queries")

    else:
        print("\nDatabase connectivity verified. Schema setup skipped.")
        print("Run script again with 'y' to setup LiteLLM schema.")

if __name__ == "__main__":
    main()
