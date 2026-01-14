import os
from urllib.parse import urlparse
from pathlib import Path
import asyncpg
from asyncpg.exceptions import ConnectionDoesNotExistError
import asyncio
import subprocess
import sys
from redis import Redis
import time

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

def ensure_redis_available(redis_url: str, retries: int = 6, delay: float = 1.0) -> None:
    """Проверка Redis; при отсутствии пытаемся запустить через Docker (если доступен)."""
    for attempt in range(1, retries + 1):
        try:
            r = Redis.from_url(redis_url, socket_connect_timeout=2)
            if r.ping():
                print(f"Redis is available at {redis_url}")
                return
        except Exception as e:
            print(f"Redis not available (attempt {attempt}/{retries}): {e}")

        time.sleep(delay)
        delay = min(5, delay * 2)

    # Финальная проверка
    try:
        r = Redis.from_url(redis_url, socket_connect_timeout=2)
        if not r.ping():
            raise RuntimeError("Redis is not available after attempts")
    except Exception:
        raise RuntimeError("Redis is not available after attempts. Start Redis or check redis_url.")

def start_worker(redis_url: str, work_queue: str = "emails") -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)

    python_bin_dir = Path(sys.executable).parent
    # Windows: rq.exe, POSIX: rq
    candidate = python_bin_dir / ("rq.exe" if os.name == "nt" else "rq")

    if candidate.exists():
        cmd = [str(candidate), "worker", "-u", redis_url, work_queue]
    else:
        # fallback: попробовать модуль CLI (rq.cli), затем просто 'rq' из PATH
        cmd = [sys.executable, "-m", "rq.cli", "worker", "-u", redis_url, work_queue]

    print("Starting rq worker:", " ".join(cmd))
    try:
        return subprocess.Popen(cmd, env=env, cwd=str(BASE_DIR))
    except FileNotFoundError:
        # последний резерват: попытаться вызвать rq из PATH
        cmd2 = ["rq", "worker", "-u", redis_url, work_queue]
        print("Falling back to PATH command:", " ".join(cmd2))
        return subprocess.Popen(cmd2, env=env, cwd=str(BASE_DIR))

def start_uvicorn() -> subprocess.Popen:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    cmd = [
        sys.executable, "-m", "uvicorn", "app.main:app",
        "--host", "localhost", "--port", "8000",
        "--reload", "--log-level", "info", "--access-log"
    ]
    print("Starting uvicorn:", " ".join(cmd))
    return subprocess.Popen(cmd, env=env, cwd=str(BASE_DIR))

def main() -> None:
    # 1) bootstrap DB + migrations
    asyncio.run(bootstrap())

    # 2) ensure redis
    redis_url = os.getenv("REDIS_URL") or settings.redis_url
    try:
        ensure_redis_available(redis_url)
    except Exception as e:
        print("ERROR: Redis is not available and could not be started automatically:", e)
        print("Please start Redis manually and re-run.")
        sys.exit(1)

    # 3) start worker and uvicorn
    worker_proc = start_worker(redis_url)
    uvicorn_proc = start_uvicorn()

    try:
        # Прослушивание процессов; просто ждём, пока пользователь не нажмёт Ctrl+C
        while True:
            # проверяем живы ли процессы
            if worker_proc.poll() is not None:
                print("RQ worker exited with code", worker_proc.returncode)
                break
            if uvicorn_proc.poll() is not None:
                print("Uvicorn exited with code", uvicorn_proc.returncode)
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutdown requested, terminating child processes...")
    finally:
        for proc, name in ((uvicorn_proc, "uvicorn"), (worker_proc, "rq worker")):
            if proc and proc.poll() is None:
                print(f"Terminating {name} (pid={proc.pid})...")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except Exception:
                    print(f"Killing {name} (pid={proc.pid})...")
                    proc.kill()
        print("Processes stopped.")

if __name__ == "__main__":
    main()
