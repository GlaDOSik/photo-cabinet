#!/usr/bin/env python3
"""
Photo Cabinet Database Initialization Script

This script initializes the database with exiftool metadata information.
It should be run during Docker container startup to set up the database content.

The script:
1. Gets the exiftool version and saves it to app_data
2. Gets the list of metadata groups from exiftool and saves them to the database
3. Gets the list of metadata tags from exiftool and saves them to the database
"""

import logging
import sys
import time

from database import DBSession
from exiftool import exif_service

# Import all database models to ensure they are registered
from service.migration_runner import MigrationRunner

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def initialize_exiftool(session) -> None:
    logger.info("Initializing metadata info from exiftool...")
    try:
        exif_service.create_metadata_dbe(session)
        logger.info("Metadata groups processed successfully")

    except Exception as e:
        logger.error(f"Failed to process metadata groups: {e}")
        raise


def main():
    """
    Main initialization function.
    """
    migration_runner = MigrationRunner()
    migration_success = migration_runner.migrate()

    if not migration_success:
        logger.error("Database migration failed. Stopping initialization.")
        return

    logger.info("Starting Photo Cabinet database initialization...")
    session = DBSession()
    try:
        initialize_start = time.time()
        initialize_exiftool(session)
        initialize_end = time.time()
        logger.info("Initialization time: " + str(initialize_end - initialize_start))

        session.commit()
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        session.rollback()
        sys.exit(1)
        
    finally:
        session.close()


if __name__ == "__main__":
    main()
