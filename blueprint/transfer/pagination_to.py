from typing import Dict

from marshmallow import Schema, fields, validate

class PaginationRequest(Schema):
    page = fields.Int(load_default=1)

    @staticmethod
    def get_page(request: Dict) -> int:
        return request.get("page")


class PaginationResponse(Schema):
    page = fields.Int(required=True)
    total = fields.Int(required=True, metadata={"description": "Total number of items"})
    has_prev_page = fields.Bool(required=True)
    has_next_page = fields.Bool(required=True)
    page_count = fields.Int(required=True)

    @staticmethod
    def to_resp(page: int, total_items: int, page_count: int, has_next_page: bool):
        has_prev_page: bool = page > 1
        return {"page": page, "total": total_items, "page_count": page_count,
                "has_prev_page": has_prev_page, "has_next_page": has_next_page}


