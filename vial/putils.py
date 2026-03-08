from typing import Dict, List


def coalesce(*values):
    return next((v for v in values if v is not None), None)

def add_if_not_none(d, key, value):
    if value is not None:
        d[key] = value