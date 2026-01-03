import json
import unittest
from pathlib import Path

from indexing.metadata_indexing_service import _parse_metadata_index


class TestParseMetadataIndex(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Get the path to the tests directory
        tests_dir = Path(__file__).parent.parent
        self.data_dir = tests_dir / "data"
        self.input_file = self.data_dir / "photo_metadata.json"
        self.expected_output_file = self.data_dir / "photo_metadata_transformed_v4.json"
    
    def test_parse_metadata_index(self):
        """Test that parse_metadata_index correctly transforms the input JSON to v4 format."""
        # Read input JSON file
        with open(self.input_file, 'r', encoding='utf-8') as f:
            input_json = f.read()
        
        # Read expected output JSON file
        with open(self.expected_output_file, 'r', encoding='utf-8') as f:
            expected_output = json.load(f)
        
        # Parse the metadata index
        result = _parse_metadata_index(input_json)
        
        # Verify the result is a dict (v4 format)
        self.assertIsInstance(result, dict)
        
        # Compare the entire structure
        self.assertEqual(result, expected_output,
                        "Result should match expected v4 output structure")


if __name__ == '__main__':
    unittest.main()

