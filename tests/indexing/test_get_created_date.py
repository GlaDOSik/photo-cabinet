import unittest
from datetime import datetime, timedelta

from domain.metadata import metadata_defined
from domain.metadata.metadata_id import MetadataId
from indexing.domain.searched_tags_result import SearchedTagsResult
from indexing.metadata_indexing_service import get_created_date


class TestGetCreatedDate(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.result = SearchedTagsResult()

    def test_exif_datetime_original_with_timezone(self):
        """Test EXIF DateTimeOriginal with timezone offset."""
        # Add DateTimeOriginal with date and time
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["2025:09:24 23:15:15"]
        
        # Add timezone offset
        self.result.searched_values[metadata_defined.EXIF_OFFSET_TIME_ORIG.get_key()] = ["+02:00"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2025)
        self.assertEqual(result.month, 9)
        self.assertEqual(result.day, 24)
        self.assertEqual(result.hour, 23)
        self.assertEqual(result.minute, 15)
        self.assertEqual(result.second, 15)
        self.assertIsNotNone(result.tzinfo)
        self.assertEqual(result.tzinfo.utcoffset(None), timedelta(hours=2))

    def test_exif_datetime_original_without_timezone(self):
        """Test EXIF DateTimeOriginal without timezone offset."""
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["2020:08:09 19:31:06"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2020)
        self.assertEqual(result.month, 8)
        self.assertEqual(result.day, 9)
        self.assertEqual(result.hour, 19)
        self.assertEqual(result.minute, 31)
        self.assertEqual(result.second, 6)
        self.assertIsNone(result.tzinfo)

    def test_exif_create_date_with_timezone(self):
        """Test EXIF CreateDate with timezone offset."""
        self.result.searched_tags.append(metadata_defined.EXIF_CREATE_DATE)
        self.result.searched_values[metadata_defined.EXIF_CREATE_DATE.get_key()] = ["2025:09:24 23:15:15"]
        
        # Add timezone offset
        self.result.searched_values[metadata_defined.EXIF_OFFSET_TIME_DIGIT.get_key()] = ["-05:00"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.tzinfo.utcoffset(None), timedelta(hours=-5))

    def test_exif_create_date_without_timezone(self):
        """Test EXIF CreateDate without timezone offset."""
        self.result.searched_tags.append(metadata_defined.EXIF_CREATE_DATE)
        self.result.searched_values[metadata_defined.EXIF_CREATE_DATE.get_key()] = ["2020:08:09 19:31:06"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertIsNone(result.tzinfo)

    def test_exif_datetime_original_with_timezone_already_present(self):
        """Test EXIF DateTimeOriginal that already has timezone info."""
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["2025:09:24 23:15:15+02:00"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.tzinfo)
        # Should not try to enhance with offset since it already has timezone

    def test_iptc_date_created_with_time(self):
        """Test IPTC DateCreated combined with TimeCreated."""
        self.result.searched_tags.append(metadata_defined.IPTC_DATE_CREATED)
        self.result.searched_values[metadata_defined.IPTC_DATE_CREATED.get_key()] = ["2020:08:09"]
        self.result.searched_values[metadata_defined.IPTC_TIME_CREATED.get_key()] = ["11:12:41+02:00"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2020)
        self.assertEqual(result.month, 8)
        self.assertEqual(result.day, 9)
        self.assertEqual(result.hour, 11)
        self.assertEqual(result.minute, 12)
        self.assertEqual(result.second, 41)
        self.assertIsNotNone(result.tzinfo)
        self.assertEqual(result.tzinfo.utcoffset(None), timedelta(hours=2))

    def test_iptc_date_created_with_time_no_timezone(self):
        """Test IPTC DateCreated combined with TimeCreated without timezone."""
        self.result.searched_tags.append(metadata_defined.IPTC_DATE_CREATED)
        self.result.searched_values[metadata_defined.IPTC_DATE_CREATED.get_key()] = ["2020:08:09"]
        self.result.searched_values[metadata_defined.IPTC_TIME_CREATED.get_key()] = ["11:12:41"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2020)
        self.assertEqual(result.month, 8)
        self.assertEqual(result.day, 9)
        self.assertEqual(result.hour, 11)
        self.assertEqual(result.minute, 12)
        self.assertEqual(result.second, 41)
        self.assertIsNone(result.tzinfo)

    def test_iptc_date_created_without_time(self):
        """Test IPTC DateCreated without TimeCreated - should skip."""
        self.result.searched_tags.append(metadata_defined.IPTC_DATE_CREATED)
        self.result.searched_values[metadata_defined.IPTC_DATE_CREATED.get_key()] = ["2020:08:09"]
        # No IPTC_TIME_CREATED
        
        result = get_created_date(self.result)
        
        # Should return None because time is missing
        self.assertIsNone(result)

    def test_date_only_format(self):
        """Test date-only format (YYYY:mm:dd)."""
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["2020:08:09"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2020)
        self.assertEqual(result.month, 8)
        self.assertEqual(result.day, 9)
        self.assertEqual(result.hour, 0)
        self.assertEqual(result.minute, 0)
        self.assertEqual(result.second, 0)

    def test_empty_result(self):
        """Test with empty result - should return None."""
        result = get_created_date(self.result)
        self.assertIsNone(result)

    def test_no_parseable_date(self):
        """Test with unparseable date value."""
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["invalid-date"]
        
        result = get_created_date(self.result)
        
        # Should skip unparseable dates and return None
        self.assertIsNone(result)

    def test_multiple_values_uses_first(self):
        """Test that when multiple values exist, the first one is used."""
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["2020:08:09 19:31:06", "2021:09:10 20:32:07"]
        
        result = get_created_date(self.result)
        
        # get_value returns the first value when multiple exist
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2020)

    def test_none_value_skipped(self):
        """Test that None values are skipped."""
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = [None]
        
        result = get_created_date(self.result)
        
        # get_value returns None (first element), which causes continue
        self.assertIsNone(result)

    def test_missing_key_skipped(self):
        """Test that missing keys are skipped."""
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        # Don't add the key to searched_values
        
        result = get_created_date(self.result)
        
        # get_value returns None when key doesn't exist
        self.assertIsNone(result)

    def test_first_valid_date_returned(self):
        """Test that the first valid date in the list is returned."""
        # Add multiple tags, first one invalid, second one valid
        invalid_id = MetadataId("EXIF", None, "InvalidTag")
        self.result.searched_tags.append(invalid_id)
        self.result.searched_values[invalid_id.get_key()] = ["invalid-date"]
        
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["2020:08:09 19:31:06"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 2020)

    def test_timezone_enhancement_only_when_needed(self):
        """Test that timezone is only added when datetime is naive."""
        # DateTimeOriginal with timezone already present
        self.result.searched_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        self.result.searched_values[metadata_defined.EXIF_DATE_TIME_ORIGINAL.get_key()] = ["2025:09:24 23:15:15+02:00"]
        # Even if offset is provided, it shouldn't override existing timezone
        self.result.searched_values[metadata_defined.EXIF_OFFSET_TIME_ORIG.get_key()] = ["-05:00"]
        
        result = get_created_date(self.result)
        
        self.assertIsNotNone(result)
        # Should keep the original timezone from the datetime string
        self.assertEqual(result.tzinfo.utcoffset(None), timedelta(hours=2))


if __name__ == '__main__':
    unittest.main()

