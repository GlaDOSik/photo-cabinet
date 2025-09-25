from sqlalchemy import Table, Column, ForeignKey

from database import Base

photo_x_tag_table = Table(
    "association_photo_x_tag",
    Base.metadata,
    Column("photo_id", ForeignKey("photo.id"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id"), primary_key=True),
)
