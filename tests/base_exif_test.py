import json
import unittest
from pathlib import Path


class BaseExifTest(unittest.TestCase):
    """Base class for tests that need to load exif_json.json test data."""

    def setUp(self):
        """Set up test fixtures."""
        tests_dir = Path(__file__).parent
        self.data_dir = tests_dir / "data"

    def get_test_json(self, json_file_name: str):
        """Load and parse JSON test file."""
        input_file = self.data_dir / json_file_name
        with open(input_file, 'r', encoding='utf-8') as f:
            json_data = f.read()
        return json.loads(json_data)

    def get_test_exif_json(self):
        """Load exif_json.json test data."""
        return self.get_test_json("exif_json.json")
