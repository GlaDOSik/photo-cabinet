This repo is a Python/Flask backend for a self-hosted photo gallery. It features:
- Flask + flask-smorest (OpenAPI + request/response schemas)
- SQLAlchemy ORM with typed models (Mapped/mapped_column)
- Postgres via psycopg2
- A small in-repo config loader (`vial.config.app_config`) reading `config.json` for technical configuration
- DB config loader (dbe.app_data.AppData) for business configuration
- Flyway-like migration runner in vial.migration_runner.MigrationRunner