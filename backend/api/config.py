"""
Configuration for API
"""
import os
from pathlib import Path

# Get DB config from parent directory
DB_CONFIG_PATH = Path(__file__).parent.parent / "db" / "db_config.py"

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'amwine_products'),
    'user': os.getenv('DB_USER', 'postgres')
}

# Add host/port/password only if specified (for remote connections)
if os.getenv('DB_HOST'):
    DB_CONFIG['host'] = os.getenv('DB_HOST', 'localhost')
    DB_CONFIG['port'] = os.getenv('DB_PORT', '5432')
    DB_CONFIG['password'] = os.getenv('DB_PASSWORD', 'postgres')

# API settings
API_TITLE = "AmWine Recommendations API"
API_VERSION = "1.0.0"
API_DESCRIPTION = "API для рекомендаций вин на основе квиза"

# Recommendation settings
DEFAULT_RECOMMENDATIONS_COUNT = 10
