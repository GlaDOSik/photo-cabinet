import unittest
from datetime import timedelta

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
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2025:09:24 23:15:15"
        )
        
        # Add timezone offset
        self.result.add_result(
            metadata_defined.EXIF_OFFSET_TIME_ORIG,
            metadata_defined.EXIF_OFFSET_TIME_ORIG,
            "+02:00"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.year, 2025)
        self.assertEqual(created_date.month, 9)
        self.assertEqual(created_date.day, 24)
        self.assertEqual(created_date.hour, 23)
        self.assertEqual(created_date.minute, 15)
        self.assertEqual(created_date.second, 15)
        self.assertIsNotNone(created_date.tzinfo)
        self.assertEqual(created_date.tzinfo.utcoffset(None), timedelta(hours=2))

    def test_exif_datetime_original_without_timezone(self):
        """Test EXIF DateTimeOriginal without timezone offset."""
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2020:08:09 19:31:06"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.year, 2020)
        self.assertEqual(created_date.month, 8)
        self.assertEqual(created_date.day, 9)
        self.assertEqual(created_date.hour, 19)
        self.assertEqual(created_date.minute, 31)
        self.assertEqual(created_date.second, 6)
        self.assertIsNone(created_date.tzinfo)

    def test_exif_create_date_with_timezone(self):
        """Test EXIF CreateDate with timezone offset."""
        self.result.add_result(
            metadata_defined.EXIF_CREATE_DATE,
            metadata_defined.EXIF_CREATE_DATE,
            "2025:09:24 23:15:15"
        )
        
        # Add timezone offset
        self.result.add_result(
            metadata_defined.EXIF_OFFSET_TIME_DIGIT,
            metadata_defined.EXIF_OFFSET_TIME_DIGIT,
            "-05:00"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.tzinfo.utcoffset(None), timedelta(hours=-5))

    def test_exif_create_date_without_timezone(self):
        """Test EXIF CreateDate without timezone offset."""
        self.result.add_result(
            metadata_defined.EXIF_CREATE_DATE,
            metadata_defined.EXIF_CREATE_DATE,
            "2020:08:09 19:31:06"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertIsNone(created_date.tzinfo)

    def test_exif_datetime_original_with_timezone_already_present(self):
        """Test EXIF DateTimeOriginal that already has timezone info."""
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2025:09:24 23:15:15+02:00"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertIsNotNone(created_date.tzinfo)
        # Should not try to enhance with offset since it already has timezone

    def test_iptc_date_created_with_time(self):
        """Test IPTC DateCreated combined with TimeCreated."""
        self.result.add_result(
            metadata_defined.IPTC_DATE_CREATED,
            metadata_defined.IPTC_DATE_CREATED,
            "2020:08:09"
        )
        self.result.add_result(
            metadata_defined.IPTC_TIME_CREATED,
            metadata_defined.IPTC_TIME_CREATED,
            "11:12:41+02:00"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.year, 2020)
        self.assertEqual(created_date.month, 8)
        self.assertEqual(created_date.day, 9)
        self.assertEqual(created_date.hour, 11)
        self.assertEqual(created_date.minute, 12)
        self.assertEqual(created_date.second, 41)
        self.assertIsNotNone(created_date.tzinfo)
        self.assertEqual(created_date.tzinfo.utcoffset(None), timedelta(hours=2))

    def test_iptc_date_created_with_time_no_timezone(self):
        """Test IPTC DateCreated combined with TimeCreated without timezone."""
        self.result.add_result(
            metadata_defined.IPTC_DATE_CREATED,
            metadata_defined.IPTC_DATE_CREATED,
            "2020:08:09"
        )
        self.result.add_result(
            metadata_defined.IPTC_TIME_CREATED,
            metadata_defined.IPTC_TIME_CREATED,
            "11:12:41"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.year, 2020)
        self.assertEqual(created_date.month, 8)
        self.assertEqual(created_date.day, 9)
        self.assertEqual(created_date.hour, 11)
        self.assertEqual(created_date.minute, 12)
        self.assertEqual(created_date.second, 41)
        self.assertIsNone(created_date.tzinfo)

    def test_iptc_date_created_without_time(self):
        """Test IPTC DateCreated without TimeCreated - should skip."""
        self.result.add_result(
            metadata_defined.IPTC_DATE_CREATED,
            metadata_defined.IPTC_DATE_CREATED,
            "2020:08:09"
        )
        # No IPTC_TIME_CREATED
        
        result = get_created_date(self.result)
        
        # Should return None because time is missing
        self.assertIsNone(result.created_date)

    def test_date_only_format(self):
        """Test date-only format (YYYY:mm:dd)."""
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2020:08:09"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.year, 2020)
        self.assertEqual(created_date.month, 8)
        self.assertEqual(created_date.day, 9)
        self.assertEqual(created_date.hour, 0)
        self.assertEqual(created_date.minute, 0)
        self.assertEqual(created_date.second, 0)

    def test_empty_result(self):
        """Test with empty result - should return None."""
        result = get_created_date(self.result)
        self.assertIsNone(result.created_date)

    def test_no_parseable_date(self):
        """Test with unparseable date value."""
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "invalid-date"
        )
        
        result = get_created_date(self.result)
        
        # Should skip unparseable dates and return None
        self.assertIsNone(result.created_date)

    def test_multiple_values_uses_first(self):
        """Test that when multiple values exist, the first one is used."""
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2020:08:09 19:31:06"
        )
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2021:09:10 20:32:07"
        )
        
        result = get_created_date(self.result)
        
        # get_value returns the first value when multiple exist
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.year, 2020)

    def test_none_value_skipped(self):
        """Test that None values are skipped."""
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            None
        )
        
        result = get_created_date(self.result)
        
        # get_value returns None (first element), which causes continue
        self.assertIsNone(result.created_date)

    def test_missing_key_skipped(self):
        """Test that missing keys are skipped."""
        self.result.requested_tags.append(metadata_defined.EXIF_DATE_TIME_ORIGINAL)
        
        result = get_created_date(self.result)
        
        # get_value returns None when key doesn't exist
        self.assertIsNone(result.created_date)

    def test_first_valid_date_returned(self):
        """Test that the first valid date in the list is returned."""
        # Add multiple tags, first one invalid, second one valid
        invalid_id = MetadataId("EXIF", None, "InvalidTag")
        self.result.add_result(
            invalid_id,
            invalid_id,
            "invalid-date"
        )
        
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2020:08:09 19:31:06"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        self.assertEqual(created_date.year, 2020)

    def test_timezone_enhancement_only_when_needed(self):
        """Test that timezone is only added when datetime is naive."""
        # DateTimeOriginal with timezone already present
        self.result.add_result(
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            metadata_defined.EXIF_DATE_TIME_ORIGINAL,
            "2025:09:24 23:15:15+02:00"
        )
        # Even if offset is provided, it shouldn't override existing timezone
        self.result.add_result(
            metadata_defined.EXIF_OFFSET_TIME_ORIG,
            metadata_defined.EXIF_OFFSET_TIME_ORIG,
            "-05:00"
        )
        
        result = get_created_date(self.result)
        
        created_date = result.created_date
        self.assertIsNotNone(created_date)
        # Should keep the original timezone from the datetime string
        self.assertEqual(created_date.tzinfo.utcoffset(None), timedelta(hours=2))


if __name__ == '__main__':
    unittest.main()

