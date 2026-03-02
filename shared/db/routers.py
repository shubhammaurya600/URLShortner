"""
shared/db/routers.py

Database router that sends all reads to the `replica` database and all
writes to the `default` (primary) database.

This implements the read replica scaling strategy with zero application
code changes required in models or repositories.
"""


class PrimaryReplicaRouter:
    """
    Route reads to replica, writes to primary.

    Configuration in settings:
        DATABASE_ROUTERS = ["shared.db.routers.PrimaryReplicaRouter"]
        DATABASES = {
            "default": {...},  # primary
            "replica": {...},  # read replica
        }
    """

    def db_for_read(self, model, **hints) -> str:
        """Send all SELECT queries to the read replica."""
        return "replica"

    def db_for_write(self, model, **hints) -> str:
        """Send all INSERT/UPDATE/DELETE queries to the primary."""
        return "default"

    def allow_relation(self, obj1, obj2, **hints) -> bool:
        """Allow relations if both objects are in primary/replica pool."""
        allowed_dbs = {"default", "replica"}
        return (
            obj1._state.db in allowed_dbs
            and obj2._state.db in allowed_dbs
        )

    def allow_migrate(self, db, app_label, model_name=None, **hints) -> bool:
        """Migrations run only on the primary (default) DB."""
        return db == "default"
