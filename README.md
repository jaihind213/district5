# District 5 
Python 3 DB-API and SQLAlchemy dialect to connect to [duckdb](https://duckdb.org) 
over http i.e ( [Radio-Duck](https://github.com/jaihind213/radio-duck) )

(inspiried by my favourite movie [Mighty ducks](https://www.imdb.com/title/tt0104868) - district5 was the original team name for the mighty ducks )

## Requirements

- install mamba https://mamba.readthedocs.io/en/latest/
- install docker

```
cd PROJECT_DIR
mamba create -n district5 python=3.9
mamba activate district5
mamba install poetry
poetry install
```

## Run Tests
```
#-without integration test
pytest -m "not integration_test" 
#-with integration test
docker run -d -p 8000:8000 -t jaihind213/radio-duck:latest
pytest
```

## Let's try it out:
```
#python 3.9^
pip install district5
#start the duckdb server i.e. radio-duck
docker run -p 8000:8000 -t jaihind213/radio-duck:latest
#the duckdb starts up with a sample table whose ddl is: 
#'create table pond(duck_type string, total int)'
echo "we will try to query that"
```

```

from sqlalchemy import create_engine, text
from sqlalchemy.dialects import registry

registry.register(
    "radio_duck.district5", "radio_duck.sqlalchemy", "RadioDuckDialect"
)


#run docker instance of radio-duck
#docker run -p 8000:8000 -t jaihind213/radio-duck:latest
engine = create_engine(
    "radio_duck+district5://user:pass@localhost:8000/?api=/v1/sql/&scheme=http"
)
# Establish a database connection
conn = engine.connect()

# Define a SQL query using qmark style or positional style
try:
    query_1 = text("""SELECT duck_type, total FROM pond where total > :total""")
    params = {"total": 0}
    result = conn.execute(query_1, params)
    # Fetch and print the results
    for row in result:
        print(row)

    print("--------------")
    query_2 = "SELECT duck_type, total FROM pond where total > ?"
    result = conn.execute(query_2, (0,))

    for row in result:
        print(row)

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Close the database connection
    conn.close()
    engine.dispose()

```