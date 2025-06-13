"""
Debug script to check configuration and environment variables
"""
import os
from src.core.config import settings

print("=== Environment Variables ===")
# Check for database-related environment variables
db_vars = [
    'DATABASE_URL',
    'DB_HOST',
    'DB_PORT',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
    'DB_SSL_MODE',
    'POSTGRES_URL',
    'POSTGRES_HOST',
    'POSTGRES_PORT',
    'POSTGRES_DATABASE',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD',
    'POSTGRES_SSL_MODE'
]

for var in db_vars:
    value = os.environ.get(var)
    if value:
        # Mask sensitive information
        if 'PASSWORD' in var or 'URL' in var:
            masked_value = value[:10] + '...' if len(value) > 10 else value
            print(f"{var}: {masked_value}")
        else:
            print(f"{var}: {value}")

print("\n=== Redis Variables ===")
redis_vars = [
    'REDIS_URL',
    'REDIS_HOST',
    'REDIS_PORT',
    'REDIS_PASSWORD',
    'REDIS_SSL'
]

for var in redis_vars:
    value = os.environ.get(var)
    if value:
        if 'PASSWORD' in var or 'URL' in var:
            masked_value = value[:10] + '...' if len(value) > 10 else value
            print(f"{var}: {masked_value}")
        else:
            print(f"{var}: {value}")

print("\n=== Settings Configuration ===")
print(f"DATABASE_URL: {settings.DATABASE_URL[:30]}...")
print(f"DB_SSL_MODE: {settings.DB_SSL_MODE}")
print(f"REDIS_URL: {settings.REDIS_URL[:30]}...")
print(f"REDIS_SSL: {settings.REDIS_SSL}") 