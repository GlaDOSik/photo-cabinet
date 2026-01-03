import subprocess

from sqlalchemy.orm import Session
from exiftool.exiftool_command import ExiftoolCommand
from exiftool.exiftool_data_parser import ExiftoolDataParser

## Service for working with Exiftool

## Creates definitions of groups, tags and values from exiftool
def create_metadata_dbe(session: Session):
    xml_data = run_command(ExiftoolCommand.list_supported_metadata())
    parser = ExiftoolDataParser(session)
    parser.parse_metadata_db(xml_data)

def run_command(exiftool_command: ExiftoolCommand) -> str:
    try:
        result = subprocess.run(
            exiftool_command.get_command(),
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise TimeoutError("exiftool tags list timed out")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to get exiftool tags: {e.stderr}")