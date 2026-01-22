"""
Version utility functions for CoralCollective

Provides version parsing, comparison, and formatting utilities.
"""

from typing import Any, Dict, Optional, Tuple
import re


def parse_version(version_string: str) -> Tuple[int, int, int]:
    """
    Parse a version string into major, minor, patch components.

    Args:
        version_string: Version string in format "X.Y.Z" or "vX.Y.Z"

    Returns:
        Tuple of (major, minor, patch) integers

    Raises:
        ValueError: If version string is invalid
    """
    # Remove 'v' prefix if present
    version = version_string.lstrip("v")

    # Match semantic version pattern
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid version string: {version_string}")

    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def get_version_info() -> Dict[str, Any]:
    """
    Get detailed version information about CoralCollective.

    Returns:
        Dictionary containing version details
    """
    from coral_collective import __version__

    major, minor, patch = parse_version(__version__)

    return {
        "version": __version__,
        "major": major,
        "minor": minor,
        "patch": patch,
        "version_tuple": (major, minor, patch),
        "version_string": format_version_string(major, minor, patch),
    }


def check_version_compatibility(
    required_version: str, current_version: Optional[str] = None
) -> bool:
    """
    Check if current version meets minimum requirements.

    Args:
        required_version: Minimum required version string
        current_version: Current version (uses package version if None)

    Returns:
        True if current version >= required version
    """
    if current_version is None:
        from coral_collective import __version__

        current_version = __version__

    try:
        req_major, req_minor, req_patch = parse_version(required_version)
        cur_major, cur_minor, cur_patch = parse_version(current_version)

        # Compare versions
        if cur_major > req_major:
            return True
        elif cur_major < req_major:
            return False

        # Major versions equal, check minor
        if cur_minor > req_minor:
            return True
        elif cur_minor < req_minor:
            return False

        # Major and minor equal, check patch
        return cur_patch >= req_patch

    except ValueError:
        return False


def format_version_string(major: int, minor: int, patch: int, prefix: str = "v") -> str:
    """
    Format version components into a standard version string.

    Args:
        major: Major version number
        minor: Minor version number
        patch: Patch version number
        prefix: Version prefix (default "v")

    Returns:
        Formatted version string
    """
    return f"{prefix}{major}.{minor}.{patch}"


def bump_version(version_string: str, bump_type: str = "patch") -> str:
    """
    Bump a version string according to semantic versioning.

    Args:
        version_string: Current version string
        bump_type: Type of bump ("major", "minor", or "patch")

    Returns:
        New version string after bump

    Raises:
        ValueError: If bump_type is invalid
    """
    major, minor, patch = parse_version(version_string)

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    # Preserve 'v' prefix if present in original
    prefix = "v" if version_string.startswith("v") else ""
    return format_version_string(major, minor, patch, prefix)
