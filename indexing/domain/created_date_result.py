from datetime import datetime
from typing import Optional

from domain.metadata.metadata_id import MetadataId


class CreatedDateResult:
    def __init__(self, created_date: Optional[datetime], metadata_id: Optional[MetadataId]):
        self.created_date: Optional[datetime] = created_date
        self.metadata_id: Optional[MetadataId] = metadata_id