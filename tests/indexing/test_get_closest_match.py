import unittest
from unittest.mock import Mock

from indexing.metadata_indexing_service import _get_closest_match
from indexing.dbe.metadata_indexing_group import MetadataIndexingGroup


class TestGetClosestMatch(unittest.TestCase):
    
    def test_get_closest_match_single_group(self):
        """Test that get_closest_match returns the group when there's only one."""
        group = Mock(spec=MetadataIndexingGroup)
        group.file_path_match = "/path/to/photos"
        
        result = _get_closest_match([group])
        
        self.assertEqual(result, group)
    
    def test_get_closest_match_longest_path(self):
        """Test that get_closest_match returns the group with the longest file_path_match."""
        group1 = Mock(spec=MetadataIndexingGroup)
        group1.file_path_match = "/path"
        
        group2 = Mock(spec=MetadataIndexingGroup)
        group2.file_path_match = "/path/to/photos"
        
        group3 = Mock(spec=MetadataIndexingGroup)
        group3.file_path_match = "/path/to"
        
        result = _get_closest_match([group1, group2, group3])
        
        self.assertEqual(result, group2)
        self.assertEqual(result.file_path_match, "/path/to/photos")
    
    def test_get_closest_match_with_none(self):
        """Test that get_closest_match ignores None file_path_match unless all are None."""
        group1 = Mock(spec=MetadataIndexingGroup)
        group1.file_path_match = None
        
        group2 = Mock(spec=MetadataIndexingGroup)
        group2.file_path_match = "/path/to/photos"
        
        group3 = Mock(spec=MetadataIndexingGroup)
        group3.file_path_match = "/path"
        
        result = _get_closest_match([group1, group2, group3])
        
        self.assertEqual(result, group2)
        self.assertEqual(result.file_path_match, "/path/to/photos")
    
    def test_get_closest_match_all_none(self):
        """Test that get_closest_match returns the first group when all file_path_match are None."""
        group1 = Mock(spec=MetadataIndexingGroup)
        group1.file_path_match = None
        
        group2 = Mock(spec=MetadataIndexingGroup)
        group2.file_path_match = None
        
        group3 = Mock(spec=MetadataIndexingGroup)
        group3.file_path_match = None
        
        result = _get_closest_match([group1, group2, group3])
        
        self.assertEqual(result, group1)
    
    def test_get_closest_match_mixed_lengths(self):
        """Test that get_closest_match correctly selects the longest path among various lengths."""
        group1 = Mock(spec=MetadataIndexingGroup)
        group1.file_path_match = "/a"
        
        group2 = Mock(spec=MetadataIndexingGroup)
        group2.file_path_match = "/a/b/c/d/e"
        
        group3 = Mock(spec=MetadataIndexingGroup)
        group3.file_path_match = "/a/b"
        
        group4 = Mock(spec=MetadataIndexingGroup)
        group4.file_path_match = "/a/b/c"
        
        result = _get_closest_match([group1, group2, group3, group4])
        
        self.assertEqual(result, group2)
        self.assertEqual(result.file_path_match, "/a/b/c/d/e")


if __name__ == '__main__':
    unittest.main()

