"""
Contact Search Application
Desktop application utilizing Edit Distance (Levenshtein Distance) algorithm to find matching contacts.

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
from src.index import main


if __name__ == "__main__":
    main()
