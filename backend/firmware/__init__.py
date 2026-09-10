"""
ARIS Firmware & Board Profiles Package.
"""

from .board_profiles import BoardProfile, CANONICAL_BOARD_PROFILES, get_board_profile, list_board_profiles

__all__ = [
    "BoardProfile",
    "CANONICAL_BOARD_PROFILES",
    "get_board_profile",
    "list_board_profiles"
]
