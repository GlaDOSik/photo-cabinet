import copy
import unittest

from domain.metadata.metadata_id import MetadataId
from indexing.customize.create_change import CreateChange
from indexing.domain.index_change_status import IndexChangeValidationStatus
from tests.base_exif_test import BaseExifTest


class TestCreateChange(BaseExifTest):

    def setUp(self):
        super().setUp()
        self.index = self.get_test_json("2_metadata_db_index.json")

    # --- validate ---

    def test_validate_created(self):
        """Tag exists in index with the expected value → CREATED."""
        metadata_id = MetadataId("EXIF", "IFD0", "Make")
        status = CreateChange("NIKON CORPORATION", metadata_id).validate(self.index)
        self.assertEqual(IndexChangeValidationStatus.CREATED, status)

    def test_validate_diff_value(self):
        """Tag exists but with a different value → EXISTS_DIFF_VALUE."""
        metadata_id = MetadataId("EXIF", "IFD0", "Make")
        status = CreateChange("OTHER BRAND", metadata_id).validate(self.index)
        self.assertEqual(IndexChangeValidationStatus.EXISTS_DIFF_VALUE, status)

    def test_validate_not_created(self):
        """Tag does not exist in index → NOT_CREATED."""
        metadata_id = MetadataId("EXIF", "IFD0", "NonExistentTag")
        status = CreateChange("anything", metadata_id).validate(self.index)
        self.assertEqual(IndexChangeValidationStatus.NOT_CREATED, status)

    # --- execute_on_index ---

    def test_execute_replace_existing(self):
        """Replacing an existing tag updates the value under its name@id key."""
        index = copy.deepcopy(self.index)
        metadata_id = MetadataId("EXIF", "IFD0", "Make")
        CreateChange("NEW BRAND", metadata_id).execute_on_index(index)
        self.assertEqual("NEW BRAND", index["EXIF"]["g1"]["IFD0"]["Make@271"])

    def test_execute_add_new_tag(self):
        """Adding a tag that doesn't exist creates it under the name@id key."""
        index = copy.deepcopy(self.index)
        metadata_id = MetadataId("EXIF", "IFD0", "CustomTag", metadata_id="9999")
        CreateChange("CustomValue", metadata_id).execute_on_index(index)
        self.assertEqual("CustomValue", index["EXIF"]["g1"]["IFD0"]["CustomTag@9999"])


if __name__ == "__main__":
    unittest.main()
