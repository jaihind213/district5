from __future__ import annotations

from superset.db_engine_specs.duckdb import DuckDBEngineSpec
from sqlalchemy.dialects import registry

class RadioDuckEngineSpec(DuckDBEngineSpec):
    engine = "district5"
    engine_name = "Radio-Duck"

    sqlalchemy_uri_placeholder = "radio_duck+district5://user:pass@localhost:8000/?api=/v1/sql/&scheme=http"
    registry.register(
        "radio_duck.district5", "radio_duck.sqlalchemy", "RadioDuckDialect"
    )
