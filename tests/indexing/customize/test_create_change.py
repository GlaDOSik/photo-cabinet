import json
import unittest
from pathlib import Path

from domain.metadata.metadata_id import MetadataId
from indexing.customize.create_change import CreateChange
from indexing.domain.index_change_status import IndexChangeStatus


class TestCreateChange(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        # Get the path to the tests directory
        tests_dir = Path(__file__).parent.parent.parent
        self.data_dir = tests_dir / "data"
        self.input_file = self.data_dir / "exif_json.json"

    def test_check_status_applied(self):
        index = self._get_index()

        metadata_id = MetadataId("EXIF", "IFD0", "Make")
        create_change = CreateChange("OLYMPUS CORPORATION", metadata_id)
        status: IndexChangeStatus = create_change.check_status(index)
        self.assertEqual(status, IndexChangeStatus.APPLIED)

    def test_check_status_diff_value(self):
        index = self._get_index()

        metadata_id = MetadataId("EXIF", "IFD0", "Make")
        create_change = CreateChange("TEST MAKE", metadata_id)
        status: IndexChangeStatus = create_change.check_status(index)
        self.assertEqual(status, IndexChangeStatus.NOT_APPLIED_DIFF_VALUE)

    def test_check_status_not_applied(self):
        index = self._get_index()

        metadata_id = MetadataId("EXIF", "IFD0", "Unmake")
        create_change = CreateChange("TEST MAKE", metadata_id)
        status: IndexChangeStatus = create_change.check_status(index)
        self.assertEqual(status, IndexChangeStatus.NOT_APPLIED)

    def test_check_status_array(self):
        index = self._get_index()

        metadata_id = MetadataId("XMP", None, "TagInArray", "TestArray.0")
        create_change = CreateChange("Value1", metadata_id)
        status: IndexChangeStatus = create_change.check_status(index)
        self.assertEqual(status, IndexChangeStatus.APPLIED)

        metadata_id = MetadataId("XMP", None, "SomeTag", "TestArray.1")
        create_change = CreateChange("Value2", metadata_id)
        status: IndexChangeStatus = create_change.check_status(index)
        self.assertEqual(status, IndexChangeStatus.APPLIED)

    def _get_index(self):
        with open(self.input_file, 'r', encoding='utf-8') as f:
            json_data = f.read()
        return json.loads(json_data)