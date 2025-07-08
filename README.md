# LiteLLM with Google Spanner & Gemini Integration

**Not tested for production. Proceed after thorough testing**

## Features

## Quick Start

### Prerequisites
- Red Hat Enterprise Linux 8+
- Python 3.13
- Google Cloud Project with billing enabled
- Gemini API key
- Google Spanner
- SQL Alchemy
- -Prisma


-------Latest update----

# Prisma + Google Cloud Spanner Compatibility Issues


## Environment Details

- **LiteLLM Version**: 1.73.6
- **Prisma Version**: 5.17.0
- **PGAdapter Version**: 0.48.4
- **Spanner**: PostgreSQL dialect
- **Database Setup**: Pre-existing Spanner tables with LiteLLM schema

## Core Issues Identified

### 1. Complex CTE Query Incompatibility

**Issue**: Prisma generates complex Common Table Expression (CTE) queries for schema introspection that are incompatible with PGAdapter's PostgreSQL emulation.

**Error Snippet**:
```
Error: ERROR: syntax error at or near "as" - Statement: 'with pg_class as (
  select
  '''"' || t.table_schema || '"."' || t.table_name || '"''' as oid,
  table_name as relname,
  case table_schema when 'pg_catalog' then 11 when 'public' then 2200 else 0 end as relnamespace,
  0 as reltype,
  0 as reloftype,
  0 as relowner,
  1 as relam,
  0 as relfilenode,
  0 as reltablespace,
  0 as relpages,
  0.0::float8 as reltuples,
  0 as relallvisible,
  0 as reltoastrelid,
  false as relhasindex,
  false as relisshared,
  'p' as relpersistence,
  CASE table_type WHEN 'BASE TABLE' THEN 'r' WHEN 'VIEW' THEN 'v' ELSE '' END as relkind,
  count(*) as relnatts,
  0 as relchecks,
  false as relhasrules,
  false as relhastriggers,
  false as relhassubclass,
  false as relrowsecurity,
  false as relforcerowsecurity,
  true as relispopulated,
  'n' as relreplident,
  false as relispartition,
  0 as relrewrite,
  0 as relfrozenxid,
  0 as relminmxid,
  '{}'::bigint[] as relacl,
  '{}'::text[] as reloptions,
  0 as relpartbound
from information_schema.tables t
inner join information_schema.columns using (table_catalog, table_schema, table_name)
group by t.table_name, t.table_schema, t.table_type
```

**Root Cause**: PGAdapter doesn't fully support the complex PostgreSQL system catalog queries that Prisma relies on for schema introspection.

### 2. Database URL Protocol Validation

**Issue**: Prisma enforces strict database URL validation that rejects Spanner connection strings.

**Error Snippet**:
```
Error: Prisma schema validation - (get-config wasm)
Error code: P1012
error: Error validating datasource `client`: the URL must start with the protocol `postgresql://` or `postgres://`.
  -->  schema.prisma:3
   | 
 2 |   provider = "postgresql"
 3 |   url      = env("DATABASE_URL")
   | 
Validation Error Count: 1
```

**Root Cause**: When `DATABASE_URL` contains `spanner+spanner://`, Prisma rejects it despite the provider being set to `postgresql`.

### 3. Migration Command Failures

**Issue**: Prisma's `db push` command fails when attempting to synchronize schema with Spanner via PGAdapter.

**Error Snippet**:
```
19:23:23 - LiteLLM Proxy:WARNING: prisma_client.py:172 - The process failed to execute. 
Details: Command '['prisma', 'db', 'push', '--accept-data-loss']' returned non-zero exit status 1.. 
Retrying... (3 attempts left)
```

**Root Cause**: Prisma's migration system cannot properly introspect the existing Spanner schema through PGAdapter.

### 4. PostgreSQL System Catalog Incompatibility

**Issue**: Prisma queries rely on PostgreSQL-specific system catalogs (`pg_class`, `pg_namespace`) that don't exist in Spanner's PostgreSQL dialect implementation.

**Error Context**:
```
FROM pg_class AS tbl
INNER JOIN pg_namespace AS namespace ON namespace.oid = tbl.relnamespace
WHERE
  ( -- (relkind = 'r' and relispartition = 't') matches partition table "duplicates"
    (tbl.relkind = 'r' AND tbl.relispartition = 'f')
      OR -- when it's a partition
    tbl.relkind = 'p'
  )
  AND namespace.nspname = ANY ( $1 )
ORDER BY namespace, table_name;
```

**Root Cause**: Spanner's PostgreSQL dialect implements `information_schema` but not the full PostgreSQL system catalog structure.

## Attempted Solutions and Results

### 1. PGAdapter with Enhanced PostgreSQL Emulation
```bash
java -jar pgadapter.jar \
  -p my-project-7817-395922 \
  -i test \
  -d test \
  -s 5432 \
  -e \
  --disable-auto-detect-client
```
**Result**: ❌ Failed - Complex CTE queries still unsupported

### 2. Custom Prisma Schema Mapping
Created Prisma schema with explicit table mappings:
```prisma
model LiteLLM_UserTable {
  user_id            String    @id @db.VarChar
  // ... other fields
  @@map("litellm_usertable")
}
```
**Result**: ❌ Failed - Schema introspection still fails

### 3. Environment Variable Overrides
```bash
export LITELLM_DATABASE_TYPE="sqlalchemy"
export DISABLE_PRISMA="true"
export LITELLM_USE_SQLALCHEMY="true"
```
**Result**: ❌ Failed - LiteLLM 1.73.6 hardcoded to use Prisma

### 4. Schema File Removal
```bash
mv schema.prisma schema.prisma.backup
```
**Result**: ❌ Failed - LiteLLM still attempts Prisma initialization

## Technical Analysis

### PGAdapter Limitations
- **Limited SQL Feature Support**: PGAdapter focuses on basic SQL operations, not complex system catalog queries
- **Incomplete PostgreSQL Emulation**: Missing critical system tables and functions
- **CTE Processing**: Cannot handle complex Common Table Expressions with multiple JOINs

### Prisma Requirements
- **Deep Schema Introspection**: Requires extensive PostgreSQL system catalog access
- **Migration System**: Needs bidirectional schema comparison capabilities
- **Type System**: Relies on PostgreSQL-specific data type information

### LiteLLM Architecture
- **Hardcoded Prisma Dependency**: Version 1.73.6 mandates Prisma for database operations
- **No Fallback Mechanism**: Cannot gracefully degrade to SQLAlchemy when Prisma fails
- **Database Feature Integration**: User management, API keys, and usage tracking all depend on Prisma

## Working Alternatives

### 1. Direct SQLAlchemy Integration
Successfully tested direct connection to Spanner:
```python
from sqlalchemy import create_engine, text
engine = create_engine('spanner+spanner:///projects/my-project-7817-395922/instances/test/databases/test')
# ✓ Basic operations work
# ✓ Can query existing tables
# ✓ Can insert/update data
```

### 2. LiteLLM Without Database Features
Successfully running LiteLLM with:
```yaml
general_settings:
  disable_database_logs: true
  allow_requests_on_db_unavailable: true
```
**Result**: ✅ Full API functionality without database dependencies

## Recommendations

### Short Term
1. **Use LiteLLM without database features** for immediate functionality
2. **Implement custom Spanner logging** via webhooks or middleware
3. **Create separate user management service** using direct Spanner client libraries

### Medium Term
1. **Evaluate PostgreSQL + Spanner sync** architecture
2. **Consider LiteLLM version downgrade** to pre-Prisma versions
3. **Implement custom database adapter** for LiteLLM

### Long Term
1. **Advocate for Spanner support** in Prisma roadmap
2. **Contribute to PGAdapter** PostgreSQL compatibility improvements
3. **Evaluate alternative proxy solutions** with native Spanner support

## Conclusion

The combination of Prisma + PGAdapter + Spanner is currently not viable for production use due to fundamental SQL compatibility issues. While each component works independently, their integration fails at the schema introspection layer. Organizations requiring Spanner integration with ORM-like functionality should consider direct database client libraries or alternative architectures that don't rely on PostgreSQL-specific system catalogs.

## References

- [Prisma Schema Reference](https://www.prisma.io/docs/reference/api-reference/prisma-schema-reference)
- [PGAdapter Documentation](https://github.com/GoogleCloudPlatform/pgadapter)
- [Spanner PostgreSQL Dialect](https://cloud.google.com/spanner/docs/postgresql-interface)
- [LiteLLM Database Integration](https://docs.litellm.ai/docs/proxy/virtual_keys)
