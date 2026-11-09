import os
from alembic import context
from cheapwings.storage.db import database
from cheapwings.storage.models import Base

config = context.config
url = (
    config.attributes.get("database_url")
    or os.getenv("DATABASE_URL")
    or config.get_main_option("sqlalchemy.url")
)
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = database(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
