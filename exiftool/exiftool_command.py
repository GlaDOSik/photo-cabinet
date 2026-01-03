from typing import List
import subprocess


EXIFTOOL_CMD = "exiftool"
# output as JSON
EXIFTOOL_JSON_OPT = "-j"
# tags grouped by group
EXIFTOOL_GROUP_OPT = "-g0:1"
# structured output instead of flattened
EXIFTOOL_STRUCT_OPT = "-struct"
# output internal tables - groups, tags, enums
EXIFTOOL_XML_OPT = "-listx"
# with -listx, output flags (parent struct, isList)
EXIFTOOL_FLAGS_OPT = "-f"


class ExiftoolCommand:
    def __init__(self):
        self.options: List[str] = []
        self.tag_allow: List[str] = []
        self.tag_deny: List[str] = []
        self.file_path = None

    def with_option(self, option: str):
        self.options.append(option)
        return self

    def exclude_tag(self, g0: str, g1: str, tag_name: str):
        tag_name = "All" if tag_name is None else tag_name
        parts = [v for v in (g0, g1, tag_name) if v is not None]
        self.tag_deny.append("--" + ":".join(parts))
        return self

    def include_tag(self, g0: str, g1: str, tag_name: str):
        tag_name = "All" if tag_name is None else tag_name
        parts = [v for v in (g0, g1, tag_name) if v is not None]
        self.tag_allow.append("-" + ":".join(parts))
        return self

    def with_file(self, file_path: str):
        self.file_path = file_path
        return self

    def get_command(self) -> List[str]:
        command = [EXIFTOOL_CMD]
        if len(self.options) > 0:
            command.extend(self.options)
        if len(self.tag_allow) > 0:
            command.extend(self.tag_allow)
        if len(self.tag_deny) > 0:
            command.extend(self.tag_deny)
        if self.file_path:
            command.append(self.file_path)

        return command

    @staticmethod
    def read_all(file_path: str) -> "ExiftoolCommand":
        return (ExiftoolCommand().
                with_option(EXIFTOOL_JSON_OPT)
                .with_option(EXIFTOOL_GROUP_OPT)
                .with_option(EXIFTOOL_STRUCT_OPT)
                .with_file(file_path))

    @staticmethod
    def list_supported_metadata():
        return ExiftoolCommand().with_option(EXIFTOOL_XML_OPT).with_option(EXIFTOOL_FLAGS_OPT)