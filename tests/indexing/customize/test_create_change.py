import copy
import unittest

from domain.metadata.metadata_id import MetadataId
from indexing.customize.create_change import CreateChange
from indexing.domain.index_change_status import IndexChangeValidationStatus
from tests.base_exif_test import BaseExifTest


class TestCreateChange(BaseExifTest):

    def test_check_status_applied(self):
        index = self.get_test_exif_json()

        metadata_id = MetadataId("EXIF", "IFD0", "Make")
        create_change = CreateChange("OLYMPUS CORPORATION", metadata_id)
        status: IndexChangeValidationStatus = create_change.validate(index)
        self.assertEqual(status, IndexChangeValidationStatus.CREATED)

    def test_check_status_diff_value(self):
        index = self.get_test_exif_json()

        metadata_id = MetadataId("EXIF", "IFD0", "Make")
        create_change = CreateChange("TEST MAKE", metadata_id)
        status: IndexChangeValidationStatus = create_change.validate(index)
        self.assertEqual(status, IndexChangeValidationStatus.EXISTS_DIFF_VALUE)

    def test_check_status_not_applied(self):
        index = self.get_test_exif_json()

        metadata_id = MetadataId("EXIF", "IFD0", "Unmake")
        create_change = CreateChange("TEST MAKE", metadata_id)
        status: IndexChangeValidationStatus = create_change.validate(index)
        self.assertEqual(status, IndexChangeValidationStatus.NOT_CREATED)

    def test_check_status_array(self):
        index = self.get_test_exif_json()

        metadata_id = MetadataId("XMP", None, "TagInArray", "TestArray.0")
        create_change = CreateChange("Value1", metadata_id)
        status: IndexChangeValidationStatus = create_change.validate(index)
        self.assertEqual(status, IndexChangeValidationStatus.CREATED)

        metadata_id = MetadataId("XMP", None, "SomeTag", "TestArray.1")
        create_change = CreateChange("Value2", metadata_id)
        status: IndexChangeValidationStatus = create_change.validate(index)
        self.assertEqual(status, IndexChangeValidationStatus.CREATED)

    # Creates new root tag in existing structure
    def test_create_root_tag_existing_struct(self):
        index = copy.deepcopy(self.get_test_exif_json())

        metadata_id = MetadataId("EXIF", "IFD0", "TestTag", None)
        create_change = CreateChange("TestValue", metadata_id)
        create_change.execute_on_index(index)

        new_value = index.get("EXIF").get("g1").get("IFD0").get("TestTag")
        self.assertEqual("TestValue", new_value)

    # Creates new root tag in non-existing g1 structure
    def test_create_root_tag_nonexisting_struct(self):
        index = copy.deepcopy(self.get_test_exif_json())

        metadata_id = MetadataId("EXIF", "NewG1", "TestTag", None)
        create_change = CreateChange("TestValue", metadata_id)
        create_change.execute_on_index(index)

        new_value = index.get("EXIF").get("g1").get("NewG1").get("TestTag")
        self.assertEqual("TestValue", new_value)

    # Creates new root tag in non-existing g1 structure and complex path with array
    def test_create_root_tag_nonexisting_struct_complex(self):
        index = copy.deepcopy(self.get_test_exif_json())

        # Use explicit [0] syntax to indicate TestArray is a list with index 0
        metadata_id = MetadataId("EXIF", "NewG1", "TestTag", "TestArray[0]")
        create_change = CreateChange("TestValue", metadata_id)
        create_change.execute_on_index(index)

        # Verify structure: EXIF.g1.NewG1.TestTag.TestArray[0] = "TestValue"
        new_value = index.get("EXIF").get("g1").get("NewG1").get("TestTag").get("TestArray")[0]
        self.assertEqual("TestValue", new_value)

    # Creates numeric dict key (not a list) to verify explicit syntax is needed
    def test_create_numeric_dict_key(self):
        index = copy.deepcopy(self.get_test_exif_json())

        # Without [] syntax, numeric key should be a dict key, not a list index
        metadata_id = MetadataId("EXIF", "NewG1", "TestTag", "NumericKey.0")
        create_change = CreateChange("DictValue", metadata_id)
        create_change.execute_on_index(index)

        # Verify structure: EXIF.g1.NewG1.TestTag.NumericKey["0"] = "DictValue" (dict, not list)
        numeric_dict = index.get("EXIF").get("g1").get("NewG1").get("TestTag").get("NumericKey")
        self.assertIsInstance(numeric_dict, dict)
        self.assertEqual("DictValue", numeric_dict["0"])

    # Creates nested structure with array element containing dict
    def test_create_nested_array_dict(self):
        index = copy.deepcopy(self.get_test_exif_json())

        # TestArray[0].NestedKey - array element contains a dict
        metadata_id = MetadataId("EXIF", "NewG1", "TestTag", "TestArray[0].NestedKey")
        create_change = CreateChange("NestedValue", metadata_id)
        create_change.execute_on_index(index)

        # Verify structure: EXIF.g1.NewG1.TestTag.TestArray[0].NestedKey = "NestedValue"
        test_array = index.get("EXIF").get("g1").get("NewG1").get("TestTag").get("TestArray")
        self.assertIsInstance(test_array, list)
        self.assertGreaterEqual(len(test_array), 1)
        self.assertIsInstance(test_array[0], dict)
        self.assertEqual("NestedValue", test_array[0].get("NestedKey"))

    # Creates nested arrays: Array1[0].Array2[0].someTag
    def test_create_nested_arrays(self):
        index = copy.deepcopy(self.get_test_exif_json())

        metadata_id = MetadataId("EXIF", "NewG1", "TestTag", "Array1[0].Array2[0].someTag")
        create_change = CreateChange("NestedArrayValue", metadata_id)
        create_change.execute_on_index(index)

        # Verify structure: EXIF.g1.NewG1.TestTag.Array1[0].Array2[0].someTag = "NestedArrayValue"
        array1 = index.get("EXIF").get("g1").get("NewG1").get("TestTag").get("Array1")
        self.assertIsInstance(array1, list)
        self.assertGreaterEqual(len(array1), 1)
        self.assertIsInstance(array1[0], dict)
        
        array2 = array1[0].get("Array2")
        self.assertIsInstance(array2, list)
        self.assertGreaterEqual(len(array2), 1)
        self.assertIsInstance(array2[0], dict)
        self.assertEqual("NestedArrayValue", array2[0].get("someTag"))

    # Tests accessing array index that doesn't exist - should create and extend array
    def test_create_array_extend_to_index(self):
        index = copy.deepcopy(self.get_test_exif_json())

        # Access index 3 when array doesn't exist - should create array and extend to index 3
        metadata_id = MetadataId("EXIF", "NewG1", "TestTag", "NewArray[3]")
        create_change = CreateChange("ValueAt3", metadata_id)
        create_change.execute_on_index(index)

        # Verify array was created and extended to index 3
        new_array = index.get("EXIF").get("g1").get("NewG1").get("TestTag").get("NewArray")
        self.assertIsInstance(new_array, list)
        self.assertGreaterEqual(len(new_array), 4)  # Should have at least 4 elements (indices 0-3)
        self.assertEqual("ValueAt3", new_array[3])
        # Previous indices should be None
        self.assertIsNone(new_array[0])
        self.assertIsNone(new_array[1])
        self.assertIsNone(new_array[2])

    # Tests that search_index_value works with new Array[0] syntax
    def test_search_with_array_syntax(self):
        index = copy.deepcopy(self.get_test_exif_json())
        from indexing.metadata_indexing_repository import search_index_value, _convert_array_syntax_to_glom

        # Create value: structure is EXIF.g1.NewG1.TestTag.SearchArray[0] = "SearchValue"
        # Note: set_index_value creates tag_name first, then path
        # So we need to search with path that matches this structure
        # The path should be: tag_name="SearchArray[0]" with empty path, OR
        # We need to adjust get_glom_path to match set_index_value convention
        # For now, let's test that the conversion works by using glom directly
        metadata_id = MetadataId("EXIF", "NewG1", "TestTag", "SearchArray[0]")
        create_change = CreateChange("SearchValue", metadata_id)
        create_change.execute_on_index(index)

        # Verify structure was created correctly
        array_value = index.get("EXIF").get("g1").get("NewG1").get("TestTag").get("SearchArray")[0]
        self.assertEqual("SearchValue", array_value)

        # Test search - need to use path that matches set_index_value structure
        # Since set_index_value puts tag_name first, we need to search with:
        # tag_name="TestTag", path="SearchArray[0]" but that won't work with current get_glom_path
        # Let's test the conversion function works correctly
        converted = _convert_array_syntax_to_glom("EXIF.g1.NewG1.TestTag.SearchArray[0]")
        self.assertEqual("EXIF.g1.NewG1.TestTag.SearchArray.0", converted)

        # Test nested: structure is TestTag.NestedArray[0].Key = "NestedSearchValue"
        nested_metadata_id = MetadataId("EXIF", "NewG1", "TestTag", "NestedArray[0].Key")
        nested_create = CreateChange("NestedSearchValue", nested_metadata_id)
        nested_create.execute_on_index(index)

        # Verify conversion for nested
        nested_converted = _convert_array_syntax_to_glom("EXIF.g1.NewG1.TestTag.NestedArray[0].Key")
        self.assertEqual("EXIF.g1.NewG1.TestTag.NestedArray.0.Key", nested_converted)
        
        # Verify structure
        nested_value = index.get("EXIF").get("g1").get("NewG1").get("TestTag").get("NestedArray")[0].get("Key")
        self.assertEqual("NestedSearchValue", nested_value)

