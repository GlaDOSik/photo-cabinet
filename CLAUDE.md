This repo is a Python/Flask backend for a self-hosted photo gallery. It features:
- Flask + flask-smorest (OpenAPI + request/response schemas)
- SQLAlchemy ORM with typed models (Mapped/mapped_column)
- Postgres via psycopg2
- A small in-repo config loader (`vial.config.app_config`) reading `config.json` for technical configuration
- DB config loader (dbe.app_data.AppData) for business configuration
- Flyway-like migration runner in vial.migration_runner.MigrationRunner

# Technical structure
Flask application factory in flask_application.py.
Local startup script run_cabinet.py - uses factory.
Gunicorn entrypoint wsgi.py - uses factory.
Future deployment using Docker (not yet implemented).

# Architecture
Docker startup - executes db initialization via initialization.init_photo_cabinet.py. Then runs gunicorn with wsgi.py.
Local startup - manually run init_photo_cabinet.py (if needed). Then run run_cabinet.py.
init_photo_cabinet.py - executes incremental db migration using MigrationRunner. Initializes db with default folders,
executes exiftool to get internal metadata definitions and saves them to DB.
DB transaction created in factory using @before_request - saves to g.transaction_session. Transaction commit in @after_request.
Service scripts - stateless methods with business logic. Ideally no db queries, all data passed in arguments, easily testable.
Facade scripts - glue for service calls. DB queries here, no tests for facade.

## Business arch
exiftool is used to load photo metadata - support for filtering tags on exiftool level.
Loaded metadata saved to db - indexing.dbe.metadata_index.py. Index contains original metadata json, user changes json and
effective json (original with applied user changes used for photo queries).
User changes are incremental as stack - final index is generated. Changes can be commited to photos. Located in indexing.customize.
Long running tasks (collection scan, indexing) executed by service.task_service. Tasks in service.task.implementation.

# Feature structure (by modules)
blueprint - Svelte provider in svelte_bp.py, module api - pure api. Script xxxx_api.py - api definition, xxxx_requests.py -
request objects using marshmallow Schema, xxxx_responses.py - response objects.
dbe - database entities extending Base. Uses SQLAlchemy Mapped annotations. General db entities. Others are in specific modules.
domain - some domain objects. Enums, etc.
exiftool - exiftool handling code. exif_service.py - command execution, loading/parsing metadata definitions.
indexing - everything related to loading/parsing/manipulating metadata index, dbe entities, domain objects
initialization - app initialization, utility scrips
migrations - folder with sql db migrations
service - some service/facade scripts, handling image processing, task execution
tests - unit tests and data for testing
vial - old library with common functions - json config loader, db migration runner

# Architecture
Prefer stateless service scripts with plain methods than singleton services with state. Facades are for queries and 
calling services.

# DBE
SQLAlchemy models use `Mapped[T]` of `Mapped[Optional[T]]` for nullable. Use `mapped_column(...)` if needed.
Add query methods to dbe scripts under class model.
Save enums as db strings (validate values).

# Coding
Prefer shorter and compact code, don't over-comment code. Implement only what is asked for and needed. If not sure,
pause and ask back.

# Imports
Follow this order, with a blank line between groups:
1) stdlib (`logging`, `uuid`, `pathlib`, ...)
2) third-party (`flask`, `sqlalchemy`, `marshmallow`, ...)
3) local modules (`blueprint.*`, `dbe.*`, `domain.*`, `service.*`, `vial.*`)

Prefer explicit imports over wildcard imports. Alias long imports only when it improves readability (mostly query 
method usage - find_by_id to find_something_by_id).

# Formatting
Indent: 4 spaces.
Strings: prefer double quotes for new code (existing files may vary; change to double quotes).
Line length: keep lines readable; if you introduce an autoformatter, pick a single line length and apply consistently.

# Types / Annotations
Add type hints for new/modified public functions, especially in `service/` and `dbe/` repository functions.
Prefer `Optional[T]` for nullable columns/values and return types.
Prefer concrete types (`dict[str, Any]`, `list[UUID]`) over bare `Dict`/`List` when editing code that already uses Python 3.9+.

# Naming
Modules/files: `snake_case.py`.
Functions/variables: `snake_case`.
Classes: `PascalCase`.
Enums: `PascalCase` type with `UPPER_SNAKE_CASE` members (see `domain/ordering_type.py`).
DB model classes: singular nouns (`Photo`, `Folder`, ...), table names in `__tablename__` match existing schema.

# API Layer (flask-smorest)
Keep endpoint functions thin: validate/parse inputs, fetch `transaction_session`, call a `service.*` function or `dbe.*` repo function or facade, map to response.
Parse UUIDs explicitly and return `abort(400)` on invalid UUIDs (pattern used in `blueprint/api/*`).
Prefer Marshmallow Schemas for request/response payloads:
- `*_requests.py`: `Schema` definitions + small `@staticmethod` helpers to extract typed values
- `*_responses.py`: `Schema` definitions + `to_resp(...)` mapping functions that return simple dicts
Use `@blueprint.arguments(Schema, location="json")` for JSON bodies and `@blueprint.response(code, Schema)` for responses
Register blueprints in flask_application.py register_blueprints.

# DB Session / Transactions
Request-scoped session is created in `flask_application.create_app()` and stored in `g.transaction_session`
In endpoints/services that need a session, fetch it with `getattr(g, "transaction_session", None)`
Repository functions in `dbe/*` take an explicit `Session` argument.
Avoid creating global sessions; prefer passing the request/session explicitly.

# Error Handling
Use `flask.abort(code)` for client errors (400/404) in the API layer.
Catch narrow exception types for validation (`ValueError`, `KeyError`) as close to parsing as possible.
Prefer `Exception` over `BaseException` in new code.
When logging exceptions, prefer `logger.exception("message")` (keeps traceback) or structured `%s` formatting.