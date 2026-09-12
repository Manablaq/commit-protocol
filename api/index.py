import os
import psycopg
from backend.production_app import build_production_app
app = build_production_app(environ=os.environ, connect=psycopg.connect)
