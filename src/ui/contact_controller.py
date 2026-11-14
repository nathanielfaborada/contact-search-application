# Search Filter: Whitespace trimming and case-insensitive normalization
# State Controller: Synchronizes DSA ranking engine with View presentation
"""
Contact Controller: Centralized Dynamic MVC Orchestrator
Coordinates features between ContactModel, EditDistance DSA, and ContactView.
"""
from ..data.contact_model import ContactModel
from ..dsa.edit_distance import search_and_rank_records
from .contact_view import ContactView


class ContactController:
    """Manages application state, multi-criteria filtering, and user interactions."""

    def __init__(self, model_instance, view_instance):
        self.contact_model = model_instance
        self.contact_view = view_instance

        self.selected_contact_name = None
        self.current_search_query = ""
        self.active_department = "All"
        self.only_favorites = False

        # Wire view callback hooks with both standard and suffix naming
        self.contact_view.set_controller_callbacks(
            on_search=self.handle_search,
            on_search_callback=self.handle_search,
            on_department=self.handle_department_filter,
            on_department_callback=self.handle_department_filter,
            on_toggle_favorites_filter=self.handle_toggle_favorites_filter,
            on_select=self.handle_select_contact,
            on_select_callback=self.handle_select_contact,
            on_toggle_star=self.handle_toggle_star,
            on_toggle_star_callback=self.handle_toggle_star,
            on_add=self.handle_add_contact,
            on_add_callback=self.handle_add_contact,
            on_edit=self.handle_edit_contact,
            on_edit_callback=self.handle_edit_contact,
            on_delete=self.handle_delete_contact,
            on_delete_callback=self.handle_delete_contact,
            on_call=self.handle_call_contact,
            on_call_callback=self.handle_call_contact,
            on_export_csv=self.handle_export_csv,
            on_export_csv_callback=self.handle_export_csv,
            on_import_csv=self.handle_import_csv,
            on_import_csv_callback=self.handle_import_csv
        )

        # Initialize layout and content
        self.contact_view.rebuild_layout_containers()
        self.refresh_interface()

    def refresh_interface(self):
        """Re-evaluates filters, executes DSA rankings, and syncs View state."""
        all_records = self.contact_model.get_all_records()
        total_count = len(all_records)
        departments = self.contact_model.get_all_departments()

        # Run DSA search & ranking engine
        filtered_records, _distance_scores = search_and_rank_records(
            records_list=all_records,
            query_string=self.current_search_query,
            active_department=self.active_department,
            only_favorites=self.only_favorites
        )

        # Check if currently selected contact exists in filtered results
        selected_record = self.contact_model.get_record(self.selected_contact_name) if self.selected_contact_name else None
        if not selected_record and filtered_records:
            selected_record = filtered_records[0]
            self.selected_contact_name = selected_record.full_name

        self.contact_view.update_directory_view(
            records_list=filtered_records,
            total_count=total_count,
            selected_record=selected_record,
            search_query=self.current_search_query,
            active_department=self.active_department,
            only_favorites=self.only_favorites,
            available_departments=departments
        )

    # ------------------------------------------------------------------ Event Handlers
    def handle_search(self, search_query_string):
        """Processes live search input."""
        self.current_search_query = search_query_string.strip()
        self.refresh_interface()

    def handle_department_filter(self, department_name):
        """Filters directory by department tag."""
        self.active_department = department_name
        self.only_favorites = False
        self.refresh_interface()

    def handle_toggle_favorites_filter(self):
        """Toggles favorites only filter mode."""
        self.only_favorites = not self.only_favorites
        self.refresh_interface()

    def handle_select_contact(self, contact_name):
        """Sets active contact record and re-renders profile details."""
        self.selected_contact_name = contact_name
        self.refresh_interface()

    def handle_toggle_star(self, contact_name):
        """Toggles favorite star state for a specific contact."""
        _success, _is_fav = self.contact_model.toggle_favorite(contact_name)
        self.refresh_interface()

    def handle_add_contact(
        self,
        name,
        number,
        department="General",
        email="",
        office="",
        notes="",
        is_favorite=False,
        parent_dialog=None
    ):
        """Validates, checks for duplicates, and creates a new contact."""
        duplicate_warnings = self.contact_model.check_potential_duplicates(name, number)
        if duplicate_warnings:
            warning_text = "\n".join(f"- {w}" for w in duplicate_warnings)
            proceed = self.contact_view.ask_confirmation(
                "Potential Duplicate",
                f"Notice potential similarities:\n\n{warning_text}\n\nDo you still want to proceed and save?",
                parent=parent_dialog
            )
            if not proceed:
                return False, "Add cancelled by user."

        success, message = self.contact_model.add_contact(
            new_contact_name=name,
            new_contact_phone_number=number,
            department=department,
            email=email,
            office=office,
            notes=notes,
            is_favorite=is_favorite
        )
        if success:
            self.selected_contact_name = name
            self.refresh_interface()
        return success, message

    def handle_edit_contact(
        self,
        old_name,
        new_name,
        new_number,
        department="General",
        email="",
        office="",
        notes="",
        is_favorite=False,
        parent_dialog=None
    ):
        """Validates and updates an existing contact."""
        duplicate_warnings = self.contact_model.check_potential_duplicates(new_name, new_number, excluded_name=old_name)
        if duplicate_warnings:
            warning_text = "\n".join(f"- {w}" for w in duplicate_warnings)
            proceed = self.contact_view.ask_confirmation(
                "Potential Duplicate",
                f"Notice potential similarities:\n\n{warning_text}\n\nDo you still want to proceed and save?",
                parent=parent_dialog
            )
            if not proceed:
                return False, "Update cancelled by user."

        success, message = self.contact_model.update_contact(
            old_contact_name=old_name,
            new_contact_name=new_name,
            new_phone_number=new_number,
            department=department,
            email=email,
            office=office,
            notes=notes,
            is_favorite=is_favorite
        )
        if success:
            self.selected_contact_name = new_name
            self.refresh_interface()
        return success, message

    def handle_delete_contact(self, contact_name):
        """Prompts confirmation and removes contact from directory."""
        confirmed = self.contact_view.ask_confirmation(
            "Delete Contact",
            f'Are you sure you want to delete "{contact_name}"?'
        )
        if not confirmed:
            return

        success, message = self.contact_model.delete_contact(contact_name)
        if success:
            if self.selected_contact_name == contact_name:
                self.selected_contact_name = None
            self.refresh_interface()
            self.contact_view.show_info("Deleted", message)
        else:
            self.contact_view.show_info("Error", message)

    def handle_call_contact(self, contact_name, phone_number):
        """Simulates placing a call and records timestamp."""
        self.contact_model.record_call_interaction(contact_name)
        self.refresh_interface()
        self.contact_view.show_info(
            "Calling",
            f"Calling {contact_name}\nat {phone_number}..."
        )

    def handle_export_csv(self, file_path):
        """Exports directory to a CSV file."""
        success, message = self.contact_model.export_to_csv(file_path)
        if success:
            self.contact_view.show_info("Export Complete", message)
        else:
            self.contact_view.show_info("Export Error", message)

    def handle_import_csv(self, file_path):
        """Imports contacts in bulk from a CSV file."""
        success, message = self.contact_model.import_from_csv(file_path)
        if success:
            self.refresh_interface()
            self.contact_view.show_info("Import Complete", message)
        else:
            self.contact_view.show_info("Import Error", message)
