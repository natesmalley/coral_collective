"""
Unit tests for version utility functions
"""

import pytest
from coral_collective.utils.version_utils import (
    parse_version,
    get_version_info,
    check_version_compatibility,
    format_version_string,
    bump_version,
)


class TestParseVersion:
    """Test version parsing functionality."""
    
    def test_parse_basic_version(self):
        """Test parsing basic version string."""
        assert parse_version("1.2.3") == (1, 2, 3)
        assert parse_version("0.0.1") == (0, 0, 1)
        assert parse_version("10.20.30") == (10, 20, 30)
    
    def test_parse_version_with_prefix(self):
        """Test parsing version with 'v' prefix."""
        assert parse_version("v1.2.3") == (1, 2, 3)
        assert parse_version("v0.0.1") == (0, 0, 1)
    
    def test_parse_invalid_version(self):
        """Test parsing invalid version raises error."""
        with pytest.raises(ValueError):
            parse_version("not-a-version")
        with pytest.raises(ValueError):
            parse_version("1.2")
        with pytest.raises(ValueError):
            parse_version("a.b.c")


class TestGetVersionInfo:
    """Test version info retrieval."""
    
    def test_get_version_info_structure(self):
        """Test that version info has expected structure."""
        info = get_version_info()
        
        assert 'version' in info
        assert 'major' in info
        assert 'minor' in info
        assert 'patch' in info
        assert 'version_tuple' in info
        assert 'version_string' in info
    
    def test_get_version_info_types(self):
        """Test that version info has correct types."""
        info = get_version_info()
        
        assert isinstance(info['version'], str)
        assert isinstance(info['major'], int)
        assert isinstance(info['minor'], int)
        assert isinstance(info['patch'], int)
        assert isinstance(info['version_tuple'], tuple)
        assert isinstance(info['version_string'], str)


class TestCheckVersionCompatibility:
    """Test version compatibility checking."""
    
    def test_exact_match(self):
        """Test exact version match."""
        assert check_version_compatibility("1.0.0", "1.0.0") is True
    
    def test_major_version_higher(self):
        """Test higher major version is compatible."""
        assert check_version_compatibility("1.0.0", "2.0.0") is True
        assert check_version_compatibility("2.0.0", "1.0.0") is False
    
    def test_minor_version_higher(self):
        """Test higher minor version is compatible."""
        assert check_version_compatibility("1.0.0", "1.1.0") is True
        assert check_version_compatibility("1.1.0", "1.0.0") is False
    
    def test_patch_version_higher(self):
        """Test higher patch version is compatible."""
        assert check_version_compatibility("1.0.0", "1.0.1") is True
        assert check_version_compatibility("1.0.1", "1.0.0") is False
    
    def test_with_v_prefix(self):
        """Test compatibility with 'v' prefix."""
        assert check_version_compatibility("v1.0.0", "v1.0.1") is True
        assert check_version_compatibility("v1.0.1", "v1.0.0") is False


class TestFormatVersionString:
    """Test version string formatting."""
    
    def test_basic_format(self):
        """Test basic version formatting."""
        assert format_version_string(1, 2, 3) == "v1.2.3"
        assert format_version_string(0, 0, 1) == "v0.0.1"
    
    def test_format_without_prefix(self):
        """Test formatting without prefix."""
        assert format_version_string(1, 2, 3, prefix="") == "1.2.3"
    
    def test_format_custom_prefix(self):
        """Test formatting with custom prefix."""
        assert format_version_string(1, 2, 3, prefix="version-") == "version-1.2.3"


class TestBumpVersion:
    """Test version bumping functionality."""
    
    def test_bump_patch(self):
        """Test patch version bump."""
        assert bump_version("1.2.3", "patch") == "1.2.4"
        assert bump_version("v1.2.3", "patch") == "v1.2.4"
        assert bump_version("1.2.9", "patch") == "1.2.10"
    
    def test_bump_minor(self):
        """Test minor version bump."""
        assert bump_version("1.2.3", "minor") == "1.3.0"
        assert bump_version("v1.2.3", "minor") == "v1.3.0"
        assert bump_version("1.9.9", "minor") == "1.10.0"
    
    def test_bump_major(self):
        """Test major version bump."""
        assert bump_version("1.2.3", "major") == "2.0.0"
        assert bump_version("v1.2.3", "major") == "v2.0.0"
        assert bump_version("9.9.9", "major") == "10.0.0"
    
    def test_bump_invalid_type(self):
        """Test invalid bump type raises error."""
        with pytest.raises(ValueError):
            bump_version("1.2.3", "invalid")
    
    def test_bump_preserves_prefix(self):
        """Test that bump preserves version prefix."""
        assert bump_version("v1.2.3", "patch").startswith("v")
        assert not bump_version("1.2.3", "patch").startswith("v")