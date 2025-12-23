import os
from urllib.parse import urlparse
from pathlib import Path
import asyncpg
from asyncpg.exceptions import ConnectionDoesNotExistError
import asyncio
import subprocess
import sys

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

async def ensure_database_exists(database_url: str, retries: int = 5, base_delay: float = 1.0) -> None:

    dsn = database_url
    if dsn.startswith("postgresql+asyncpg://"):
        dsn = dsn.replace("postgresql+asyncpg://", "postgresql://", 1)

    parsed = urlparse(dsn)
    db_name = parsed.path.lstrip("/")
    if not db_name:
        raise RuntimeError("No database name found in DATABASE_URL")

    admin_db = "postgres"
    admin_netloc = parsed.netloc
    admin_dsn = f"postgresql://{admin_netloc}/{admin_db}?sslmode=disable"

    print(f"Attempting to connect to {parsed.hostname}:{parsed.port} as {parsed.username}...")

    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            conn = await asyncpg.connect(admin_dsn)
            try:
                exists = await conn.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", db_name)
                if not exists:
                    print(f"Database '{db_name}' not found — creating...")
                    await conn.execute(f'CREATE DATABASE "{db_name}"')
                    print(f"Database '{db_name}' created.")
                else:
                    print(f"Database '{db_name}' already exists.")
                return
            finally:
                await conn.close()
        except (ConnectionDoesNotExistError, OSError, asyncpg.exceptions.CannotConnectNowError) as exc:
            last_exc = exc
            delay = base_delay * (2 ** (attempt - 1))
            print(f"Attempt {attempt}/{retries}: cannot connect to Postgres ({exc}). Retrying in {delay}s...")
            await asyncio.sleep(delay)
        except Exception as exc:
            raise RuntimeError(f"Cannot connect to Postgres server to create DB: {exc}") from exc

    raise RuntimeError(
        "Cannot connect to Postgres server to create DB after retries. "
        "Check that Postgres is running, DATABASE_URL is correct, and firewall/VPN is disabled. "
        f"Last error: {last_exc}"
    )

async def run_alembic_migrations() -> None:
    ALEMBIC_INI = BASE_DIR / "app" / "alembic.ini"

    if not ALEMBIC_INI.exists():
        raise RuntimeError(f"Alembic ini not found: {ALEMBIC_INI}")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "alembic",
            "-c",
            str(ALEMBIC_INI),
            "upgrade",
            "head",
        ],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("STDERR:\n", result.stderr)
        raise RuntimeError("Alembic migration failed")

    print("Alembic migrations completed successfully.")
    if result.stdout:
        print(result.stdout)


async def bootstrap() -> None:
    database_url = os.getenv("DATABASE_URL") or settings.database_url
    await ensure_database_exists(database_url)
    # Run migrations
    await run_alembic_migrations()


def run_bootstrap() -> None:
    asyncio.run(bootstrap())

def main() -> None:
    asyncio.run(bootstrap())

    subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "localhost",
            "--port",
            "8000",
            "--reload",
        ]
    )


if __name__ == "__main__":
    main()
