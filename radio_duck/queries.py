# refer https://duckdb.org/docs/sql/duckdb_table_functions.html
has_index_query = "SELECT indexname FROM pg_indexes where schemaname = ? and tablename = ? and indexname = ?"  # noqa: E501,B950
has_table_query = "select table_name from information_schema.tables where table_schema = ? and table_name = ?"  # noqa: E501,B950
has_sequence_query = "select sequencename from pg_sequences where schemaname = ? and sequencename = ?"  # noqa: E501,B950
get_tables = (
    "select tablename from pg_tables where schemaname = ?"  # noqa: E501,B950
)
get_schemas = "SELECT schema_name FROM information_schema.schemata where catalog_name not in ('system','temp')"  # noqa: E501,B950
get_views = "select view_name from duckdb_views where schema_name = ?"  # noqa: E501,B950
get_view_sql = "select sql from duckdb_views where schema_name = ? and view_name= ?"  # noqa: E501,B950
get_constraints = "select constraint_text as name,constraint_column_names as column_names from duckdb_constraints where schema_name = ? and table_name = ? and constraint_type = ?"  # noqa: E501,B950
get_temp_views = "select view_name from duckdb_views where temporary = true;"  # noqa: E501,B950
get_temp_tables = "select table_name from information_schema.tables where table_schema = ? and table_type like '%TEMPORARY%';"  # noqa: E501,B950
get_sequences = "select sequencename from pg_sequences where schemaname = ?"  # noqa: E501,B950
get_indexes = "select index_name, sql, is_unique from duckdb_indexes where schema_name = ? and table_name = ?"  # noqa: E501,B950
get_columns = "SET schema '{}'; PRAGMA table_info('{}')"
get_check_constraint = "select constraint_text as name,expression as sqltext from duckdb_constraints where schema_name = ? and table_name = ? and constraint_type = 'CHECK'"  # noqa: E501,B950
