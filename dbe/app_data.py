import uuid
from typing import Optional

from sqlalchemy.orm import mapped_column, Mapped, Session

from database import Base
from domain.app_data_field import AppDataField


class AppData(Base):
    __tablename__ = "app_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    field_name: Mapped[str]
    field_value: Mapped[Optional[str]]

def get_app_data_val(session: Session, app_data_field: AppDataField):
    app_data = session.query(AppData).filter_by(field_name=app_data_field.name).first()
    if app_data is None:
        return app_data_field.default_value
    if app_data.field_value is None:
        return None
    return app_data_field.parse(app_data.field_value)

def set_app_data_value(session: Session, app_data_field: AppDataField, value):
    app_data = session.query(AppData).filter_by(field_name=app_data_field.name).first()
    if app_data is not None:
        app_data.field_value = str(value)
    else:
        app_data = AppData()
        app_data.field_name = app_data_field.name
        app_data.field_value = str(value)
        session.add(app_data)
        session.flush()