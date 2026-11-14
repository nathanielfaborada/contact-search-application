# Entrypoint: Pure Python standard library bootstrap
"""
Contact Search Application
Desktop and Mobile application utilizing Edit Distance (Levenshtein Distance) algorithm to find matching contacts.

Authors:
- Faborada, Nathaniel F.
- Bodino, John Paul P.
College of Mary Immaculate - BSCS 2-A

Architecture: Model-View-Controller (MVC)
- Model: src/data/contact_model.py
- View: src/ui/contact_view.py
- Controller: src/ui/contact_controller.py
- DSA: src/dsa/edit_distance.py (Time Complexity: O(m * n))
"""
import sys

from src.data.contact_model import ContactModel
from src.ui.contact_view import ContactView
from src.ui.contact_controller import ContactController


def main():
    """Initializes and runs the centralized contact search phonebook application."""
    try:
        import tkinter as tk
        has_tkinter = True
    except ImportError:
        has_tkinter = False

    if has_tkinter:
        contact_model = ContactModel()
        contact_view = ContactView()
        _contact_controller = ContactController(contact_model, contact_view)
        contact_view.mainloop()
    else:
        # Running on Android / headless mobile environment
        from src.ui.mobile_kivy_view import run_mobile_app
        run_mobile_app()


if __name__ == "__main__":
    main()
