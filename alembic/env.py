from logging.config import fileConfig
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import create_engine
from alembic import context

# Add the app directory to Python path so we can import app modules
sys.path.insert(0, "/app")

# Load .env file variables into environment
# Assumes .env is in the project root (one level up from alembic dir)
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# Import your Base from the app's db module
from app.db.base import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Get the database URL from the environment variable
# Fallback to DATABASE_URL if ALEMBIC_DATABASE_URL is not set, then to the value in alembic.ini
ALEMBIC_DATABASE_URL = (
    os.getenv("ALEMBIC_DATABASE_URL")
    or os.getenv("DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
)

# Debug logging
print(f"ALEMBIC_DATABASE_URL from env: {os.getenv('ALEMBIC_DATABASE_URL')}")
print(f"DATABASE_URL from env: {os.getenv('DATABASE_URL')}")
print(f"sqlalchemy.url from config: {config.get_main_option('sqlalchemy.url')}")
print(f"Final ALEMBIC_DATABASE_URL: {ALEMBIC_DATABASE_URL}")

if not ALEMBIC_DATABASE_URL:
    raise ValueError(
        "Neither ALEMBIC_DATABASE_URL nor DATABASE_URL environment variables are set, and sqlalchemy.url is not configured in alembic.ini"
    )

# Update the config object so engine_from_config can use it if needed,
# but we'll primarily use the ALEMBIC_DATABASE_URL variable directly.
config.set_main_option("sqlalchemy.url", ALEMBIC_DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use the ALEMBIC_DATABASE_URL obtained from environment or config
    context.configure(
        url=ALEMBIC_DATABASE_URL,  # Use the variable directly
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create engine directly using the ALEMBIC_DATABASE_URL
    # We know ALEMBIC_DATABASE_URL is not None because of the check above
    connectable = create_engine(str(ALEMBIC_DATABASE_URL), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
