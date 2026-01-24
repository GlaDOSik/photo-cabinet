from typing import Dict, Optional

from marshmallow import Schema, fields, validate


class Metadata(Schema):
    g0 = fields.Str(required=True)
    g1 = fields.Str(required=False)
    tags = fields.Dict(required=True)

    @staticmethod
    def to_resp(g0: str, g1: Optional[str], tags: Dict):
        data = {"g0": g0, "tags": tags}
        if g1 is not None:
            data["g1"] = g1
        return data


class PhotoMetadataIndex(Schema):
    metadata = fields.Nested(Metadata, many=True, required=True)

    @staticmethod
    def to_resp(metadata_json: Dict) -> Dict:
        metadata_list = []
        
        for g0, g0_data in metadata_json.items():
            if not isinstance(g0_data, dict):
                continue
                
            # Create Metadata for "tags" if they exist
            if "tags" in g0_data:
                tags = g0_data["tags"]
                if isinstance(tags, dict):
                    metadata_list.append(Metadata.to_resp(g0, None, tags))
            
            # Create Metadata for each key in "g1" dict
            if "g1" in g0_data:
                g1_dict = g0_data["g1"]
                if isinstance(g1_dict, dict):
                    for g1_key, g1_tags in g1_dict.items():
                        if isinstance(g1_tags, dict):
                            metadata_list.append(Metadata.to_resp(g0, g1_key, g1_tags))
        
        return {"metadata": metadata_list}