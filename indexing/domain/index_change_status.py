from enum import Enum


class IndexChangeValidationStatus(Enum):
    CREATED = "CREATED"
    NOT_CREATED = "NOT_CREATED"
    EXISTS_DIFF_VALUE = "EXISTS_DIFF_VALUE"
    INCORRECT_TAG_PATH = "INCORRECT_TAG_PATH"