# Persistence Note: Ensures JSON integrity across application lifecycles
"""
Contact Model: Centralized Dynamic Persistence & Validation Layer
Pure Python standard library (json, csv, os, datetime) with zero external dependencies.
"""
import csv
import json
import os
import shutil
import sys
from datetime import datetime

from .contact_entity import ContactRecord
from ..dsa.edit_distance import edit_distance


class ContactModel:
    """Manages centralized dynamic contact records, persistence, and audit logging."""

    def __init__(self, storage_file_path=None):
        if getattr(sys, 'frozen', False):
            project_base_directory = os.path.dirname(sys.executable)
            bundled_dir = getattr(sys, '_MEIPASS', project_base_directory)
        else:
            project_base_directory = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            bundled_dir = project_base_directory

        if storage_file_path is None:
            self.storage_file_path = os.path.join(project_base_directory, 'contacts.json')
            # If not yet in executable directory but bundled in PyInstaller, copy as initial seed
            if not os.path.exists(self.storage_file_path):
                bundled_file = os.path.join(bundled_dir, 'contacts.json')
                if os.path.exists(bundled_file) and bundled_file != self.storage_file_path:
                    try:
                        shutil.copyfile(bundled_file, self.storage_file_path)
                    except Exception:
                        pass
        else:
            self.storage_file_path = storage_file_path

        self.audit_log_path = os.path.join(project_base_directory, 'audit_log.json')
        self.records = self.load_contacts_from_storage()

    # ------------------------------------------------------------------ Persistence
    def load_contacts_from_storage(self):
        """Loads contacts from JSON storage file, gracefully handling legacy and rich formats."""
        if not os.path.exists(self.storage_file_path):
            return {}

        try:
            with open(self.storage_file_path, mode='r', encoding='utf-8') as storage_file:
                loaded_data = json.load(storage_file)
                if not isinstance(loaded_data, dict):
                    return {}

                loaded_records = {}
                for contact_name, raw_value in loaded_data.items():
                    record = ContactRecord.from_raw(contact_name, raw_value)
                    loaded_records[record.full_name] = record
                return loaded_records
        except (json.JSONDecodeError, OSError):
            return {}

    def save_contacts_to_storage(self):
        """Persists all records into JSON storage file."""
        try:
            serialized_data = {
                contact_name: record.to_dictionary_entry()
                for contact_name, record in self.records.items()
            }
            with open(self.storage_file_path, mode='w', encoding='utf-8') as storage_file:
                json.dump(serialized_data, storage_file, indent=4)
            return True
        except OSError:
            return False

    # ------------------------------------------------------------------ Queries
    def get_all(self):
        """Returns dictionary of name -> phone_number for backward compatibility."""
        return {name: record.phone_number for name, record in self.records.items()}

    def get_all_records(self):
        """Returns list of all ContactRecord instances."""
        return list(self.records.values())

    def get_record(self, contact_name):
        """Returns single ContactRecord instance or None."""
        return self.records.get(contact_name.strip())

    def get_all_departments(self):
        """Dynamically scans all contacts and returns sorted unique department tags."""
        departments = set()
        for record in self.records.values():
            if record.department:
                departments.add(record.department)
        sorted_list = sorted(departments)
        return ["All"] + sorted_list

    # ------------------------------------------------------------------ Mutations
    def validate_contact_information(self, candidate_name, candidate_phone_number, current_name=None):
        """Validates that contact name and phone number conform to data standards."""
        cleaned_name = candidate_name.strip()
        cleaned_number = candidate_phone_number.strip()

        if not cleaned_name:
            return False, "Please enter a contact name."

        if not cleaned_number:
            return False, "Please enter a contact phone number."

        if not cleaned_number.isdigit():
            return False, "Phone number must contain numeric digits only."

        if current_name is None or cleaned_name != current_name:
            if cleaned_name in self.records:
                return False, f'A contact named "{cleaned_name}" already exists.'

        return True, "Valid"

    def check_potential_duplicates(self, candidate_name, candidate_number, excluded_name=None):
        """Uses Levenshtein distance to detect similar names or exact duplicate numbers."""
        cleaned_name = candidate_name.strip().lower()
        cleaned_number = candidate_number.strip()
        warnings = []

        for existing_name, record in self.records.items():
            if excluded_name and existing_name == excluded_name:
                continue

            # Exact phone number match check
            if record.phone_number == cleaned_number:
                warnings.append(f'Phone number "{cleaned_number}" is already used by "{existing_name}".')

            # Fuzzy name similarity check via Levenshtein distance (only for words with length >= 4)
            if len(cleaned_name) >= 4 and len(existing_name) >= 4:
                distance = edit_distance(cleaned_name, existing_name.lower())
                if 0 < distance <= 2:
                    warnings.append(f'Name "{candidate_name}" is very similar to existing contact "{existing_name}".')

        return warnings

    def add_contact(
        self,
        new_contact_name,
        new_contact_phone_number,
        department="General",
        email="",
        office="",
        notes="",
        is_favorite=False
    ):
        """Adds a new contact record with rich fields and records audit log."""
        is_valid, validation_message = self.validate_contact_information(
            new_contact_name, new_contact_phone_number
        )
        if not is_valid:
            return False, validation_message

        record = ContactRecord(
            full_name=new_contact_name,
            phone_number=new_contact_phone_number,
            department=department,
            email=email,
            office=office,
            notes=notes,
            is_favorite=is_favorite
        )
        self.records[record.full_name] = record
        self.save_contacts_to_storage()
        self.log_audit_action("CREATE", record.full_name, f"Department: {record.department}, Phone: {record.phone_number}")
        return True, f'Successfully saved contact "{record.full_name}".'

    def update_contact(
        self,
        old_contact_name,
        new_contact_name,
        new_phone_number,
        department="General",
        email="",
        office="",
        notes="",
        is_favorite=False
    ):
        """Updates an existing contact record with new values."""
        cleaned_old_name = old_contact_name.strip()
        if cleaned_old_name not in self.records:
            return False, f'Contact "{cleaned_old_name}" does not exist.'

        is_valid, validation_message = self.validate_contact_information(
            new_contact_name, new_phone_number, current_name=cleaned_old_name
        )
        if not is_valid:
            return False, validation_message

        existing_record = self.records[cleaned_old_name]
        cleaned_new_name = new_contact_name.strip()

        # Update fields
        existing_record.full_name = cleaned_new_name
        existing_record.phone_number = new_phone_number.strip()
        existing_record.department = department.strip() if department else "General"
        existing_record.email = email.strip() if email else ""
        existing_record.office = office.strip() if office else ""
        existing_record.notes = notes.strip() if notes else ""
        existing_record.is_favorite = bool(is_favorite)

        if cleaned_new_name != cleaned_old_name:
            del self.records[cleaned_old_name]
            self.records[cleaned_new_name] = existing_record

        self.save_contacts_to_storage()
        self.log_audit_action("UPDATE", cleaned_new_name, f"Updated profile for {cleaned_new_name}")
        return True, f'Successfully updated contact "{cleaned_new_name}".'

    def delete_contact(self, target_contact_name):
        """Removes a contact by name and logs audit event."""
        cleaned_target_name = target_contact_name.strip()
        if cleaned_target_name in self.records:
            del self.records[cleaned_target_name]
            self.save_contacts_to_storage()
            self.log_audit_action("DELETE", cleaned_target_name, "Removed from centralized directory")
            return True, f'Successfully deleted contact "{cleaned_target_name}".'
        return False, f'Contact "{cleaned_target_name}" was not found.'

    def toggle_favorite(self, contact_name):
        """Toggles the favorite star state of a contact."""
        cleaned_name = contact_name.strip()
        record = self.records.get(cleaned_name)
        if record:
            record.is_favorite = not record.is_favorite
            self.save_contacts_to_storage()
            action_desc = "Starred as favorite" if record.is_favorite else "Unstarred from favorites"
            self.log_audit_action("STAR", cleaned_name, action_desc)
            return True, record.is_favorite
        return False, False

    def record_call_interaction(self, contact_name):
        """Records call timestamp for interaction tracking."""
        cleaned_name = contact_name.strip()
        record = self.records.get(cleaned_name)
        if record:
            record.last_called = datetime.now().strftime("%Y-%m-%d %I:%M %p")
            self.save_contacts_to_storage()
            self.log_audit_action("CALL", cleaned_name, f"Placed call on {record.last_called}")
            return True, record.last_called
        return False, ""

    # ------------------------------------------------------------------ CSV Export & Import
    def export_to_csv(self, file_path):
        """Exports all directory contacts to a CSV file."""
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                # Header row
                writer.writerow([
                    "Full Name", "Phone Number", "Department",
                    "Email", "Office", "Notes", "Favorite", "Last Called", "Created At"
                ])
                for record in self.records.values():
                    writer.writerow([
                        record.full_name,
                        record.phone_number,
                        record.department,
                        record.email,
                        record.office,
                        record.notes,
                        "Yes" if record.is_favorite else "No",
                        record.last_called,
                        record.created_at
                    ])
            self.log_audit_action("EXPORT", "SYSTEM", f"Exported {len(self.records)} contacts to CSV")
            return True, f"Exported {len(self.records)} contacts to {os.path.basename(file_path)}."
        except OSError as err:
            return False, f"Failed to export CSV: {err}"

    def import_from_csv(self, file_path):
        """Imports contacts in bulk from a CSV file."""
        if not os.path.exists(file_path):
            return False, "File does not exist."

        imported_count = 0
        skipped_count = 0

        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as csv_file:
                reader = csv.reader(csv_file)
                rows = list(reader)

                if not rows:
                    return False, "CSV file is empty."

                # Check if first row is header
                start_index = 0
                first_row = [cell.lower() for cell in rows[0]]
                if "name" in first_row[0] or "full name" in first_row[0]:
                    start_index = 1

                for row in rows[start_index:]:
                    if not row or len(row) < 2:
                        continue

                    name = row[0].strip()
                    number = row[1].strip()

                    if not name or not number or not number.isdigit():
                        skipped_count += 1
                        continue

                    department = row[2].strip() if len(row) > 2 and row[2].strip() else "General"
                    email = row[3].strip() if len(row) > 3 else ""
                    office = row[4].strip() if len(row) > 4 else ""
                    notes = row[5].strip() if len(row) > 5 else ""
                    is_favorite = True if len(row) > 6 and row[6].strip().lower() in ("yes", "true", "1") else False

                    record = ContactRecord(
                        full_name=name,
                        phone_number=number,
                        department=department,
                        email=email,
                        office=office,
                        notes=notes,
                        is_favorite=is_favorite
                    )
                    self.records[name] = record
                    imported_count += 1

            self.save_contacts_to_storage()
            self.log_audit_action("IMPORT", "SYSTEM", f"Imported {imported_count} contacts from CSV (skipped {skipped_count})")
            return True, f"Successfully imported {imported_count} contacts (skipped {skipped_count})."
        except (csv.Error, OSError) as err:
            return False, f"Error reading CSV: {err}"

    # ------------------------------------------------------------------ Audit History Log
    def log_audit_action(self, action_type, contact_name, details):
        """Logs directory changes into audit_log.json for centralized traceability."""
        try:
            audit_events = []
            if os.path.exists(self.audit_log_path):
                with open(self.audit_log_path, mode='r', encoding='utf-8') as log_file:
                    audit_events = json.load(log_file)
                    if not isinstance(audit_events, list):
                        audit_events = []

            event_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M:%S %p"),
                "action": action_type,
                "contact_name": contact_name,
                "details": details
            }
            audit_events.insert(0, event_entry)  # Prepend newest

            # Keep last 100 events
            audit_events = audit_events[:100]

            with open(self.audit_log_path, mode='w', encoding='utf-8') as log_file:
                json.dump(audit_events, log_file, indent=4)
        except OSError:
            pass

    def get_audit_history(self):
        """Returns list of recent audit log entries."""
        if not os.path.exists(self.audit_log_path):
            return []
        try:
            with open(self.audit_log_path, mode='r', encoding='utf-8') as log_file:
                data = json.load(log_file)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []
