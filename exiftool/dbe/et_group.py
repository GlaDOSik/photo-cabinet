from uuid import UUID, uuid4
from sqlalchemy.orm import Mapped, mapped_column, Session
from database import Base


class ExifToolGroup(Base):
    __tablename__ = "exif_group"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    namespace: Mapped[str]
    g0: Mapped[str]
    g1: Mapped[str]
    g2: Mapped[str]

    user_created: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)

def find_by_namespace(session: Session, namespace: str):
    return session.query(ExifToolGroup).filter_by(namespace=namespace).first()

def find_all(session: Session):
    return session.query(ExifToolGroup).filter_by(deleted=False).filter_by(user_created=False).all()
