---
name: create-api
description: Guide for adding a new API endpoint to this Flask/flask-smorest project. Use when asked to add endpoints, routes, or API features.
---

# API creation guide for photo-cabinet

## File structure

Each API module lives in `blueprint/api/<module>/` and contains:
- `<module>_api.py` — route definitions (thin, no business logic)
- `<module>_requests.py` — marshmallow request schemas + typed extraction helpers
- `<module>_responses.py` — marshmallow response schemas + `to_resp()` helpers

Register new blueprints in `flask_application.py` → `register_blueprints()`.

## Defining a request schema

```python
# blueprint/api/<module>/<module>_requests.py
from typing import Dict
from uuid import UUID
from marshmallow import Schema, fields, validate

class MyRequest(Schema):
    photo_id = fields.Str(required=True, load_only=True)
    type = fields.Str(
        required=True,
        load_only=True,
        validate=validate.OneOf([e.value for e in MyEnum])
    )

    @staticmethod
    def get_photo_id(request: Dict) -> UUID:
        return UUID(request.get("photo_id"))

    @staticmethod
    def get_type(request: Dict) -> "MyEnum":
        return MyEnum(request.get("type"))
```

- Use `load_only=True` for input-only fields.
- Add a `@staticmethod` per field that extracts a typed value — keeps endpoint code clean.
- Parse UUIDs explicitly; let `ValueError` bubble up for `abort(400)`.

## Defining a response schema

```python
# blueprint/api/<module>/<module>_responses.py
from typing import Dict, Optional
from marshmallow import Schema, fields

class ItemSchema(Schema):
    id = fields.Str(required=True)
    name = fields.Str(allow_none=True)

    @staticmethod
    def to_resp(id: str, name: Optional[str]) -> Dict:
        return {"id": id, "name": name}


class MyResponse(Schema):
    status = fields.Str(required=True)
    data = fields.Nested(ItemSchema, allow_none=True)

    @staticmethod
    def to_resp(status: str, data: Optional[Dict] = None) -> Dict:
        return {"status": status, "data": data}
```

- Use `fields.Nested(OtherSchema)` for nested objects.
- Use `fields.List(fields.Nested(ItemSchema))` for lists.
- `to_resp()` returns a plain `dict` — flask-smorest serializes it via the schema.

## Defining an enum

```python
# domain/<name>.py
from enum import Enum

class MyEnum(Enum):
    VALUE_A = "VALUE_A"
    VALUE_B = "VALUE_B"
```

- Save as string in DB: use `mapped_column(String)` and validate with `validate.OneOf(...)` in the schema.
- Reference enum values in marshmallow: `validate.OneOf([e.value for e in MyEnum])`.

## Defining an endpoint

```python
# blueprint/api/<module>/<module>_api.py
from typing import Dict
from flask import g, abort
from flask_smorest import Blueprint

from blueprint.api.<module>.<module>_requests import MyRequest
from blueprint.api.<module>.<module>_responses import MyResponse

my_api = Blueprint("<module>", __name__, url_prefix="/<module>")


@my_api.route("/resource", methods=["POST"])
@my_api.arguments(MyRequest, location="json")
@my_api.response(200, MyResponse)
@my_api.alt_response(400)
@my_api.alt_response(404)
def get_resource(request: Dict):
    try:
        photo_uuid = MyRequest.get_photo_id(request)
    except (ValueError, KeyError):
        abort(400)

    transaction_session = getattr(g, "transaction_session", None)
    photo = find_photo_by_id(transaction_session, photo_uuid)
    if photo is None:
        abort(404)

    result = some_service.do_work(photo)
    return MyResponse.to_resp(result)
```

Rules:
- Decorator order: `@blueprint.route` → `@blueprint.arguments` → `@blueprint.response` → `@blueprint.alt_response(...)`.
- Always fetch session via `getattr(g, "transaction_session", None)`.
- Catch `(ValueError, KeyError)` around UUID/enum parsing → `abort(400)`.
- Call service/facade functions; no raw queries in endpoint functions.
- Return the dict from `to_resp()` directly — flask-smorest handles serialization.

## DB access pattern (dbe)

Query functions live in `dbe/<entity>.py` or `<module>/dbe/<entity>.py`, below the model class:

```python
def find_by_photo_id(session: Session, photo_id: UUID) -> Optional[MyModel]:
    return session.query(MyModel).filter_by(photo_id=photo_id).first()
```

Import with an alias when the name would clash:

```python
from dbe.photo import find_by_id as find_photo_by_id
```

## Checklist for a new endpoint

1. Add request schema + extraction helpers to `<module>_requests.py`
2. Add response schema + `to_resp()` to `<module>_responses.py`
3. Add route function to `<module>_api.py` following the decorator order above
4. If it's a new blueprint, register it in `flask_application.py`
