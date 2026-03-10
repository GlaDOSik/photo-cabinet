import time
import uuid
from typing import Callable, Optional

from sqlalchemy.orm import mapped_column, Mapped, Session

from database import Base
from domain.app_data_field import AppDataField

app_data_cache: dict[str, tuple] = {}  # field_name -> (value, timestamp)
app_data_cache_time_sec = 360

class AppData(Base):
    __tablename__ = "app_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    field_name: Mapped[str]
    field_value: Mapped[Optional[str]]

def _cache_get(key: str):
    entry = app_data_cache.get(key)
    if entry and time.time() - entry[1] < app_data_cache_time_sec:
        return entry[0], True
    return None, False

def _cache_set(key: str, value):
    app_data_cache[key] = (value, time.time())

def get_app_data_val(session: Session, app_data_field: AppDataField):
    cached, hit = _cache_get(app_data_field.name)
    if hit:
        return cached

    app_data = session.query(AppData).filter_by(field_name=app_data_field.name).first()
    if app_data is None:
        value = app_data_field.default_value
    elif app_data.field_value is None:
        value = None
    else:
        value = app_data_field.parse(app_data.field_value)

    _cache_set(app_data_field.name, value)
    return value

def set_app_data_value(session: Session, app_data_field: AppDataField, value, on_set: Optional[Callable] = None):
    app_data = session.query(AppData).filter_by(field_name=app_data_field.name).first()
    if app_data is not None:
        app_data.field_value = str(value)
    else:
        app_data = AppData()
        app_data.field_name = app_data_field.name
        app_data.field_value = str(value)
        session.add(app_data)
        session.flush()
    _cache_set(app_data_field.name, value)
    if on_set is not None:
        on_set(app_data_field, value)