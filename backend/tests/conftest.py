import os


# Test-only configuration. This is set before FastAPI imports Settings and is
# never used by Docker or production deployment.
os.environ.setdefault("JWT_SECRET_KEY", "test-only-jwt-secret-that-is-longer-than-32-bytes")
