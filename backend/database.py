import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Configure these environment variables in the terminal before starting FastAPI.
# The database password is deliberately not stored in this source file.
required = ["DB_PASSWORD"]
missing = [name for name in required if not os.getenv(name)]
if missing:
    raise RuntimeError(
        "Missing database setting: " + ", ".join(missing) +
        ". Set DB_PASSWORD in your terminal before starting the server."
    )

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "127.0.0.1"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "integrity_system"),
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
