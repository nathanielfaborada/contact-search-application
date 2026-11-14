# Helper Note: Generates single-character uppercase initials
"""
Shared UI Utilities and Formatter Functions
"""

def get_avatar_initial(name: str) -> str:
    """Extracts first character of contact name for avatar circle display."""
    clean = name.strip()
    return clean[0].upper() if clean else "?"


def format_phone_display(number: str) -> str:
    """Formats phone number string cleanly for list presentation."""
    clean = number.strip()
    return clean
