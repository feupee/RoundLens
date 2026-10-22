from alembic import context
from app.db import Base,engine
from app import models
if context.is_offline_mode():
    raise RuntimeError('Use migração online com DATABASE_URL configurada no ambiente')
with engine.connect() as connection:
    context.configure(connection=connection,target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
