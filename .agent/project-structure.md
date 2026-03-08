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