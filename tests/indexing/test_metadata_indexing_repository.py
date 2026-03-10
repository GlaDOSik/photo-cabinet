import unittest

from domain.metadata.metadata_id import MetadataId
from tests.base_exif_test import BaseExifTest
from indexing import metadata_indexing_service


class TestMetadataIndexingRepository(BaseExifTest):
    def setUp(self):
        super().setUp()
        self.exif_json = self.get_test_json("2_metadata_db_index.json")
        self.ui_view = self.get_test_json("3_ui_view.json")

    def test_index_to_view(self):
        ordering = [MetadataId("File", None, None),
                    MetadataId("EXIF", None, None),
                    MetadataId("NotExist", None, None),
                    MetadataId("XMP", None, None),
                    MetadataId("EXIF", "IFD0", None),
                    MetadataId("EXIF", "IFD1", None),
                    MetadataId("File", "-", None),
                    MetadataId("File", "System", None),
                    MetadataId("File", "NotExist", None)]
        ui_view = metadata_indexing_service.index_to_ui_view(self.exif_json, ordering)
        self.assertEqual(ui_view, self.ui_view)


if __name__ == '__main__':
    unittest.main()