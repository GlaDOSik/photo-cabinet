import json
import unittest
from pathlib import Path
from unittest.mock import Mock

from domain.metadata.metadata_id import MetadataId
from indexing.metadata_indexing_service import search_tag_value_by_tags


class TestSearchTagValueByTags(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        # Get the path to the tests directory
        tests_dir = Path(__file__).parent.parent
        self.data_dir = tests_dir / "data"
        self.test_data_file = self.data_dir / "metadata_indexing_service_test_data.json"
        
        # Load test data
        with open(self.test_data_file, 'r', encoding='utf-8') as f:
            self.test_data = json.load(f)
        
        # Create photo with metadata index using Mock
        self.metadata_index = Mock(exif_json=self.test_data)
        self.photo = Mock(metadata_index=self.metadata_index)

    def test_simple_tag_in_tags(self):
        """Test searching for a tag directly in tags section."""
        metadata_id = MetadataId("EXIF", None, "ExposureTime")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        self.assertEqual(result.searched_tags[0], metadata_id)
        self.assertEqual(result.get_value(metadata_id), "1/5000")
        self.assertEqual(result.get_all_values(metadata_id), ["1/5000"])

    def test_tag_with_g1_specified(self):
        """Test searching for a tag when g1 is specified."""
        metadata_id = MetadataId("EXIF", "IFD0", "Software")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        self.assertEqual(result.get_value(metadata_id), "Adobe Lightroom 8.5.1 (Macintosh)")
        self.assertEqual(result.get_all_values(metadata_id), ["Adobe Lightroom 8.5.1 (Macintosh)"])

    def test_tag_without_g1_searches_tags_first(self):
        """Test that when g1 is not specified, it searches tags first."""
        # FNumber is in EXIF.tags, so it should be found there (not in g1)
        metadata_id = MetadataId("EXIF", None, "FNumber")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        self.assertEqual(result.get_value(metadata_id), 2.8)
        self.assertEqual(result.get_all_values(metadata_id), [2.8])

    def test_tag_without_g1_falls_back_to_g1(self):
        """Test that when tag is not in tags, it searches in g1 sections."""
        # ModifyDate is only in IFD0, not in tags
        metadata_id = MetadataId("EXIF", None, "ModifyDate")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        self.assertEqual(result.get_value(metadata_id), "2025:09:15 01:18:06")
        self.assertEqual(result.get_all_values(metadata_id), ["2025:09:15 01:18:06"])

    def test_tag_with_path(self):
        """Test searching for a tag within a specific path structure."""
        # Group is inside Look structure in XMP.g1.XMP-crs.Look
        metadata_id = MetadataId("XMP", "XMP-crs", "Group", path="Look")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        self.assertEqual(result.get_value(metadata_id), "Modern")
        self.assertEqual(result.get_all_values(metadata_id), ["Modern"])

    def test_tag_in_array_multiple_values(self):
        """Test searching for a tag in an array structure that appears multiple times."""
        # FullMaskSize appears in multiple CorrectionMasks items
        metadata_id = MetadataId("XMP", "XMP-crs", "FullMaskSize", path="CorrectionMasks")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        all_values = result.get_all_values(metadata_id)
        self.assertEqual(len(all_values), 2)
        self.assertIn("2886,1920", all_values)
        self.assertIn("120,120", all_values)
        # get_value should return first value
        self.assertIn(result.get_value(metadata_id), ["2886,1920", "120,120"])

    def test_tag_in_nested_array_structure(self):
        """Test searching for a tag in nested array structures."""
        # InputDigest is in CorrectionMasks array items
        metadata_id = MetadataId("XMP", "XMP-crs", "InputDigest", path="CorrectionMasks")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        all_values = result.get_all_values(metadata_id)
        self.assertEqual(len(all_values), 2)
        self.assertIn("96078B9E52C1B0F9371C24297D99E90F", all_values)
        self.assertIn("dsfsdgdgds", all_values)

    def test_tag_with_path_in_nested_structure(self):
        """Test searching for a tag with path in a nested structure."""
        # ConvertToGrayscale is in Look.Parameters structure
        metadata_id = MetadataId("XMP", "XMP-crs", "ConvertToGrayscale", path="Look")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        # Should find it recursively within Look structure (in Parameters sub-structure)
        self.assertEqual(result.get_value(metadata_id), False)
        self.assertEqual(result.get_all_values(metadata_id), [False])

    def test_tag_with_nested_path(self):
        """Test searching for a tag using nested path specification (e.g., Look.Parameters)."""
        # ConvertToGrayscale is in Look.Parameters structure - use nested path
        metadata_id = MetadataId("XMP", "XMP-crs", "ConvertToGrayscale", path="Look.Parameters")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 1)
        # Should find it in Look.Parameters structure
        self.assertEqual(result.get_value(metadata_id), False)
        self.assertEqual(result.get_all_values(metadata_id), [False])
        
        # Also test that Group can be found with single-level path
        metadata_id_group = MetadataId("XMP", "XMP-crs", "Group", path="Look")
        result_group = search_tag_value_by_tags(self.photo, [metadata_id_group])
        self.assertEqual(result_group.get_value(metadata_id_group), "Modern")

    def test_multiple_tags_search(self):
        """Test searching for multiple tags at once."""
        metadata_ids = [
            MetadataId("EXIF", None, "ExposureTime"),
            MetadataId("EXIF", "IFD0", "Software"),
            MetadataId("XMP", "XMP-crs", "Group", path="Look")
        ]
        result = search_tag_value_by_tags(self.photo, metadata_ids)
        
        self.assertEqual(len(result.searched_tags), 3)
        self.assertEqual(result.get_value(metadata_ids[0]), "1/5000")
        self.assertEqual(result.get_value(metadata_ids[1]), "Adobe Lightroom 8.5.1 (Macintosh)")
        self.assertEqual(result.get_value(metadata_ids[2]), "Modern")

    def test_nonexistent_tag(self):
        """Test searching for a tag that doesn't exist."""
        metadata_id = MetadataId("EXIF", None, "NonExistentTag")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 0)
        self.assertEqual(result.get_value(metadata_id), None)
        self.assertEqual(result.get_all_values(metadata_id), [])

    def test_nonexistent_group(self):
        """Test searching in a group that doesn't exist."""
        metadata_id = MetadataId("NonExistentGroup", None, "SomeTag")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 0)
        self.assertEqual(result.get_value(metadata_id), None)

    def test_get_single_value_with_one_match(self):
        """Test get_single_value when only one value exists."""
        metadata_id = MetadataId("EXIF", None, "ExposureTime")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(result.get_single_value(metadata_id), "1/5000")

    def test_get_single_value_with_multiple_matches(self):
        """Test get_single_value raises error when multiple values exist."""
        metadata_id = MetadataId("XMP", "XMP-crs", "FullMaskSize", path="CorrectionMasks")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        with self.assertRaises(ValueError) as context:
            result.get_single_value(metadata_id)
        self.assertIn("Multiple values found", str(context.exception))

    def test_tag_with_path_no_path_structure(self):
        """Test searching with path when the path structure doesn't exist."""
        metadata_id = MetadataId("EXIF", None, "ExposureTime", path="NonExistentPath")
        result = search_tag_value_by_tags(self.photo, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 0)
        self.assertEqual(result.get_value(metadata_id), None)

    def test_photo_without_metadata_index(self):
        """Test that searching in photo without metadata_index returns empty result."""
        photo_without_index = Mock(metadata_index=None)
        metadata_id = MetadataId("EXIF", None, "ExposureTime")
        result = search_tag_value_by_tags(photo_without_index, [metadata_id])
        
        self.assertEqual(len(result.searched_tags), 0)
        self.assertEqual(result.get_value(metadata_id), None)


if __name__ == '__main__':
    unittest.main()
