# migrations/migration_runner.py
import os
import logging
from sqlalchemy import text
from database import engine
from root import ROOT_DIR

logger = logging.getLogger(__name__)

class MigrationRunner:
    def __init__(self, migrations_dir=None):
        if migrations_dir is None:
            migrations_dir = os.path.join(ROOT_DIR, "migrations")
        self.migrations_dir = migrations_dir
        self.migrations_table = "schema_migrations"
    
    def create_migrations_table(self):
        """Create the migrations tracking table"""
        with engine.connect() as conn:
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.migrations_table} (
                    version VARCHAR(50) PRIMARY KEY,
                    description TEXT,
                    success BOOLEAN NOT NULL DEFAULT TRUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    
    def get_applied_migrations(self):
        """Get list of already applied migrations"""
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT version FROM {self.migrations_table} WHERE success = TRUE"))
            return [row[0] for row in result]

    def has_failed_migration(self) -> bool:
        """Return True if there is any failed migration recorded"""
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(1) FROM {self.migrations_table} WHERE success = FALSE"))
            count = result.scalar_one()
            return count and int(count) > 0
    
    def get_pending_migrations(self):
        """Get list of pending migrations"""
        applied = self.get_applied_migrations()
        pending = []
        
        for filename in sorted(os.listdir(self.migrations_dir)):
            if filename.endswith('.sql'):
                version = filename.split('_')[0]  # Extract version from filename
                if version not in applied:
                    pending.append(filename)
        
        return pending
    
    def _run_migration(self, filename):
        """Run a single migration file"""
        filepath = os.path.join(self.migrations_dir, filename)
        version = filename.split("_")[0]
        # Preserve full description even if it contains underscores
        description = filename.split("_", 1)[1].replace(".sql", "")

        logger.info(f"Running migration file %s", filename)
        
        with open(filepath, 'r') as f:
            sql_content = f.read()

        # Run the migration within a transaction: either fully applied or fully rolled back
        try:
            with engine.begin() as conn:  # commit on success, rollback on exception
                # Use exec_driver_sql to allow multi-statement SQL files across drivers
                conn.exec_driver_sql(sql_content)

                conn.execute(
                    text(f"""
                        INSERT INTO {self.migrations_table} (version, description, success)
                        VALUES (:version, :description, TRUE)
                    """),
                    {"version": version, "description": description},
                )

            logger.info("Applied migration: %s", filename)
        except Exception as exc:
            # The migration DDL/DML was rolled back; now persist the failure record so it won't be retried
            logger.exception("Failed to apply migration %s: %s", filename, exc)
            try:
                with engine.begin() as conn:
                    conn.execute(
                        text(f"""
                            INSERT INTO {self.migrations_table} (version, description, success)
                            VALUES (:version, :description, FALSE)
                        """),
                        {"version": version, "description": description},
                    )
                logger.info("Recorded migration failure for %s", filename)
            except Exception as record_exc:
                # Log the error when recording the failure fails - this is critical
                logger.error("Failed to record migration failure for %s: %s", filename, record_exc)
                # Re-raise to indicate the migration failure couldn't be recorded
                raise RuntimeError(f"Migration failed AND failed to record failure: {exc}") from record_exc
            raise
    
    def migrate(self) -> bool:
        """Run all pending migrations. Returns True if all migrations succeeded, False otherwise."""
        self.create_migrations_table()
        # Abort early if there is a previously failed migration
        if self.has_failed_migration():
            logger.error("Aborting migrations: a previous migration failed. Fix it and remove its row from %s.", self.migrations_table)
            return False
        pending = self.get_pending_migrations()
        logger.info("Found %d pending migrations.", len(pending))
        
        if not pending:
            logger.info("No pending migrations")
            return True
        
        try:
            for migration in pending:
                self._run_migration(migration)
            
            logger.info("Applied %d migrations", len(pending))
            return True
        except Exception as exc:
            logger.error("Migration failed, aborting remaining migrations: %s", exc)
            return False

# Usage
if __name__ == "__main__":
    runner = MigrationRunner()
    success = runner.migrate()
    exit(0 if success else 1)