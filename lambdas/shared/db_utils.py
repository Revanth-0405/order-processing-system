import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """Provides an isolated DB connection for Lambdas, decoupling them from Flask."""
    conn = psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)
    return conn