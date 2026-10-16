from alembic import context

from app.core.config import settings
from app.models import Base

config = context.config
target_metadata = Base.metadata
url = config.attributes.get("database_url", settings.database_url)

if context.is_offline_mode():
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    from app.core.database import make_engine

    engine = make_engine(url)
    # Migration engine has a single, explicit lifetime and never creates tables on import.
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=engine.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
