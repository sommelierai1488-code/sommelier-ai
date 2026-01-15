"""
Database configuration for PostgreSQL
"""
import os

# For local connections as postgres user, don't use password
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'amwine_products'),
    'user': os.getenv('DB_USER', 'postgres')
}

# Add host/port/password only if specified (for remote connections)
if os.getenv('DB_HOST'):
    DB_CONFIG['host'] = os.getenv('DB_HOST', 'localhost')
    DB_CONFIG['port'] = os.getenv('DB_PORT', '5432')
    DB_CONFIG['password'] = os.getenv('DB_PASSWORD', 'postgres')
