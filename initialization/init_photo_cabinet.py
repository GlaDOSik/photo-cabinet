#!/usr/bin/env python3
"""
Photo Cabinet Database Initialization Script

This script initializes the database with exiftool metadata information.
It should be run during Docker container startup to set up the database content.

The script:
1. Gets the exiftool version and saves it to app_data
2. Gets the list of metadata groups, tags and values from exiftool and writes them to CSV files
"""

import logging
import sys
import time

from database import DBSession
from domain.app_data_field import AppDataField
from dbe.app_data import get_app_data_val, set_app_data_value
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
    """Load exiftool docs from initialization/metadata_docs CSVs when AppData LOAD_METADATA_DOCS is True."""
    if not get_app_data_val(session, AppDataField.LOAD_METADATA_DOCS):
        return
    logger.info("Loading metadata docs from CSVs...")
    exif_service.load_metadata_docs_from_csv(session)
    set_app_data_value(session, AppDataField.LOAD_METADATA_DOCS, False)
    logger.info("Metadata docs loaded.")


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
