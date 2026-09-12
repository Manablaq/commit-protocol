import os
import psycopg
from backend.schema_bootstrap import bootstrap_schema

if __name__ == "__main__":
    bootstrap_schema(environ=os.environ, connect=psycopg.connect)
