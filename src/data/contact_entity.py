# Entity Note: Validates data consistency for all stored contacts
"""
Contact Entity Definition
Defines the ContactRecord domain entity using pure Python standard library.
"""
from datetime import datetime


class ContactRecord:
    """Represents an individual contact person with rich dynamic fields."""

    def __init__(
        self,
        full_name,
        phone_number,
        department="General",
        email="",
        office="",
        notes="",
        is_favorite=False,
        last_called="",
        created_at=None
    ):
        self.full_name = full_name.strip()
        self.phone_number = phone_number.strip()
        self.department = department.strip() if department else "General"
        self.email = email.strip() if email else ""
        self.office = office.strip() if office else ""
        self.notes = notes.strip() if notes else ""
        self.is_favorite = bool(is_favorite)
        self.last_called = last_called.strip() if last_called else ""
        self.created_at = created_at if created_at else datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dictionary_entry(self):
        """Converts contact record into serialized dictionary structure."""
        return {
            "phone_number": self.phone_number,
            "department": self.department,
            "email": self.email,
            "office": self.office,
            "notes": self.notes,
            "is_favorite": self.is_favorite,
            "last_called": self.last_called,
            "created_at": self.created_at
        }

    @classmethod
    def from_raw(cls, contact_name, raw_data):
        """Instantiates ContactRecord from either legacy string or rich dictionary format."""
        if isinstance(raw_data, str):
            # Legacy format support: {"Name": "09123456789"}
            return cls(
                full_name=contact_name,
                phone_number=raw_data
            )
        elif isinstance(raw_data, dict):
            # Rich format support
            return cls(
                full_name=contact_name,
                phone_number=raw_data.get("phone_number", ""),
                department=raw_data.get("department", "General"),
                email=raw_data.get("email", ""),
                office=raw_data.get("office", ""),
                notes=raw_data.get("notes", ""),
                is_favorite=raw_data.get("is_favorite", False),
                last_called=raw_data.get("last_called", ""),
                created_at=raw_data.get("created_at", "")
            )
        return cls(full_name=contact_name, phone_number=str(raw_data))

    def __repr__(self):
        return (
            f"ContactRecord(full_name='{self.full_name}', phone_number='{self.phone_number}', "
            f"department='{self.department}', is_favorite={self.is_favorite})"
        )
