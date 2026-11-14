# System Design Document: Contact Search Application

> **Project**: Contact Search Application  
> **Authors**: Nathaniel F. Faborada & John Paul P. Bodino (College of Mary Immaculate - BSCS 2-A)  
> **Architecture Pattern**: Model-View-Controller (MVC) with Dedicated DSA Processing Engine  
> **Runtime Environment**: Python 3 (Native Standard Library) + Tkinter GUI  

---

## 1. High-Level Architectural Overview

The Contact Search Application uses a decoupled Model-View-Controller (MVC) architecture with a standalone Data Structures and Algorithms (DSA) processing engine. The system enforces strict separation of concerns:

- **Frontend / Presentation Layer (`src/ui/`)**: Handles rendering, window lifecycle, layout frames, and user input events via Tkinter.
- **Controller / Orchestration Layer (`src/ui/contact_controller.py`)**: Intercepts user gestures, executes query routing, delegates validation to the Model, and triggers algorithmic filtering.
- **DSA Processing Engine (`src/dsa/`)**: Houses algorithmic logic including Levenshtein Distance (Dynamic Programming) with zero UI or persistence dependencies.
- **Backend / Data Layer (`src/data/`)**: Enforces data integrity rules, encapsulates contact entities, and handles disk persistence to `contacts.json`.

```mermaid
flowchart TD
    User(["Desktop User"]) -->|"Interacts with UI"| View["Presentation Layer (ContactView)"]
    View -->|"Dispatches Events"| Controller["Controller Layer (ContactController)"]
    
    subgraph Core Logic & Processing
        Controller -->|"Query Routing"| DSA["DSA Engine (edit_distance.py)"]
        Controller -->|"Read / Write Operations"| Model["Model Layer (ContactModel)"]
        Model -->|"Instantiates"| Entity["ContactRecord Entity"]
    end
    
    DSA -->|"Ranked Matches"| Controller
    Model -->|"Direct IO"| Storage[("JSON Storage (contacts.json)")]
    Controller -->|"Updates State"| View
```

---

## 2. Model-View-Controller (MVC) Class Architecture

The object-oriented design is organized into distinct classes with explicit boundaries:

```mermaid
classDiagram
    class ContactRecord {
        +str full_name
        +str phone_number
        +to_dictionary_entry() dict
    }

    class ContactModel {
        +str storage_file_path
        +dict contact_directory
        +load_contacts_from_storage() dict
        +save_contacts_to_storage() bool
        +validate_contact_information(candidate_name, candidate_phone_number) tuple
        +add_contact(new_contact_name, new_contact_phone_number) tuple
        +get_all() dict
        +get_all_records() list
        +find_contact_by_name(target_contact_name) ContactRecord
        +delete_contact(target_contact_name) tuple
    }

    class ContactView {
        +StringVar search_var
        +Entry _entry
        +Canvas _canvas
        +Frame _list_frame
        +set_controller_callbacks(on_search, on_add, on_contact_click, on_dots_click) void
        +render_contacts(contacts) void
        +open_add_dialog() void
        +show_info(title, message) void
        +ask_confirmation(title, question) bool
    }

    class ContactController {
        +ContactModel contact_model
        +ContactView contact_view
        +refresh_contact_list() void
        +handle_search(search_query_string) void
        +handle_add_contact(contact_name, phone_number) tuple
        +handle_contact_click(contact_name, phone_number) void
        +handle_options_click(contact_name, phone_number) void
    }

    ContactController --> ContactModel : Coordinates
    ContactController --> ContactView : Controls
    ContactModel --> ContactRecord : Creates
```

### Component Roles & Boundary Matrix

| Component | File Path | Scope & Permitted Actions | Strictly Prohibited Scope |
| :--- | :--- | :--- | :--- |
| **ContactRecord** | `src/data/contact_entity.py` | Encapsulates single contact data fields and formatting. | Cannot read disk, call UI, or execute search algorithms. |
| **ContactModel** | `src/data/contact_model.py` | File I/O (`contacts.json`), validation, CRUD operations. | Banned from importing Tkinter or managing UI widgets. |
| **EditDistance DSA** | `src/dsa/edit_distance.py` | Levenshtein matrix calculations, closest match scoring. | Pure mathematical computation; no state retention or I/O. |
| **ContactView** | `src/ui/contact_view.py` | Tkinter widgets, event bindings, card layouts. | Banned from altering `contacts.json` or computing distances directly. |
| **ContactController** | `src/ui/contact_controller.py` | Orchestrates data flow between View, Model, and DSA. | Does not construct visual widgets or read raw disk files. |

---

## 3. Data Structures & Algorithms (DSA) Engine

### Levenshtein Distance (Edit Distance)
The core searching feature computes the minimum single-character edit operations required to convert a search query string `s1` into a stored contact number `s2`.

#### 1. Operations Allowed:
- **Insertion**: Adding a character (`cost = 1`)
- **Deletion**: Removing a character (`cost = 1`)
- **Substitution**: Replacing one character with another (`cost = 1` if different, `cost = 0` if identical)

#### 2. Dynamic Programming Recurrence Relation:
For a 2D matrix `dp[i][j]` representing the edit distance between prefix `s1[0..i-1]` and `s2[0..j-1]`:

$$\text{dp}[i][j] = \begin{cases} 
i & \text{if } j = 0 \\
j & \text{if } i = 0 \\
\text{dp}[i-1][j-1] & \text{if } s1[i-1] == s2[j-1] \\
1 + \min(\text{dp}[i-1][j], \text{dp}[i][j-1], \text{dp}[i-1][j-1]) & \text{otherwise}
\end{cases}$$

#### 3. Complexity Analysis:
- **Time Complexity**: **O(m * n)** per comparison, where:
  - `m` = length of the input search query string
  - `n` = length of the stored contact phone number
- **Total Search Time**: **O(k * m * n)**, where `k` is the total number of contacts stored in `contacts.json`.
- **Space Complexity**: **O(m * n)** for the Dynamic Programming matrix table.

```mermaid
flowchart TD
    Query["Search Query String (m digits)"] --> Compare["Compare with Contact Number (n digits)"]
    Compare --> Matrix["Initialize (m+1) x (n+1) Matrix"]
    Matrix --> DP["Compute Min Edits: Del, Ins, Sub"]
    DP --> Score["Return Edit Distance Score"]
    Score --> Filter["Group Contacts by Min Score"]
    Filter --> Display["Display Closest Matching Records"]
```

#### 4. Algorithmic Roadmap for Future Expansion:
The `src/dsa/` directory is architected to allow adding further algorithms without breaking the UI or Model:
- **Trie (Prefix Tree)**: For instant O(L) prefix lookup on contact names.
- **Fuzzy Wuzzy / Jaro-Winkler**: For typo-tolerant alphanumeric name search.
- **Soundex / Metaphone**: For phonetic search (e.g. finding "Nathan" when searching "Nathen").

---

## 4. Runtime Sequence Workflows

### Workflow A: Real-Time Phone Number Search

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant View as ContactView
    participant Controller as ContactController
    participant DSA as edit_distance.py
    participant Model as ContactModel

    User->>View: Types number query into search box (e.g., "0912")
    View->>Controller: handle_search("0912")
    Controller->>Model: get_all()
    Model-->>Controller: Return all contacts directory
    Controller->>DSA: find_closest_contacts("0912", contacts)
    loop For each contact in directory
        DSA->>DSA: edit_distance("0912", contact_phone)
    end
    DSA-->>Controller: Return min-distance matched records
    Controller->>View: render_contacts(matching_results)
    View-->>User: Displays sorted matching contact cards
```

---

### Workflow B: Adding a New Contact

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant View as ContactView
    participant Controller as ContactController
    participant Model as ContactModel
    participant Disk as contacts.json

    User->>View: Clicks "+" button and fills modal form
    User->>View: Clicks "Save"
    View->>Controller: handle_add_contact(name, phone_number)
    Controller->>Model: add_contact(name, phone_number)
    Model->>Model: validate_contact_information(name, phone_number)
    alt Validation Failed (Empty, non-digits, or duplicate)
        Model-->>Controller: Return (False, error_message)
        Controller-->>View: Show warning dialog
        View-->>User: Display error dialog
    else Validation Succeeded
        Model->>Disk: json.dump(contact_directory)
        Disk-->>Model: Success
        Model-->>Controller: Return (True, "Saved successfully")
        Controller->>Controller: refresh_contact_list()
        Controller->>View: render_contacts(updated_directory)
        View-->>User: Close modal and display updated list
    end
```

---

## 5. Data Persistence & Storage Contract

### Storage Format (`contacts.json`)
The application uses a key-value JSON schema stored locally in the project root:

```json
{
    "Natl": "09950216326",
    "JPul": "02395345162",
    "Jby": "02394516723",
    "Jt": "09123554807",
    "Vnalo": "09121215376",
    "K neth": "09120796654",
    "Faborada, Nathaniel F.": "09123456789"
}
```

### Data Validation Invariants:
1. **Name Integrity**: Must not be empty or whitespace only. Must be unique within the directory.
2. **Phone Number Integrity**: Must not be empty, must consist exclusively of decimal digits (`0-9`).
3. **Atomic Persistence**: Every mutation (`add_contact`, `delete_contact`) immediately executes a flush to `contacts.json`.

---

## 6. Design System & Ergonomics Standards

All graphical interface tokens strictly align with the project design system in `.agents/design-system/`:

### Color Palette (iOS Light Card Theme)
- **Canvas (`BG`)**: `#F2F2F7` (Neutral light canvas)
- **Card Surface (`CARD_BG`)**: `#FFFFFF` (Elevated card background)
- **Dividers (`DIVIDER` / `SEARCH_BG`)**: `#E5E5EA` (Subtle structural borders)
- **Primary Text (`TEXT_PRIMARY`)**: `#000000` (High contrast text, WCAG AAA compliant)
- **Muted Text (`TEXT_GREY`)**: `#8E8E93` (Secondary metadata text)
- **Accent Color (`ACCENT`)**: `#007AFF` (iOS system blue for primary actions)
- **Accent Active (`ACCENT_HOVER`)**: `#005BBB` (Pressed interaction state)

### Accessibility & Touch Target Enforcement
- **Minimum Interactive Size**: 44x44px touch targets on all interactive controls (Add button, Three Dots menu button, Row selection).
- **Zero Decorative Emojis**: Replaced with clean SVG/Canvas primitives and typography.
- **Anti-Slop Ban**: Absolute ban on em dashes and en dashes across all user-facing dialogs, labels, and documentation.

---

## 7. File Directory Map

```text
contact-search-application/
├── docs/
│   └── SYSTEM-DESIGN.md                # This comprehensive system design manual
├── src/
│   ├── data/                           # Persistence & Domain Entities
│   │   ├── __init__.py
│   │   ├── contact_entity.py           # ContactRecord entity class
│   │   └── contact_model.py            # ContactModel JSON repository & validation
│   ├── dsa/                            # Algorithmic Computation Engines
│   │   ├── __init__.py
│   │   └── edit_distance.py            # Levenshtein distance & ranking logic
│   ├── ui/                             # Visual Presentation & Controllers
│   │   ├── __init__.py
│   │   ├── common/
│   │   │   ├── __init__.py
│   │   │   └── colors.py               # Design tokens (iOS Light Card Theme)
│   │   ├── shared/
│   │   │   ├── __init__.py
│   │   │   └── helpers.py              # Formatting & avatar initial extractors
│   │   ├── contact_view.py             # Tkinter desktop layout & widgets
│   │   └── contact_controller.py       # MVC orchestrator & query dispatcher
│   └── index.py                        # Internal application factory entrypoint
├── main.py                             # Project root launcher
├── contacts.json                       # Contact records database file
├── README.md                           # Project introduction & overview
└── .gitignore                          # Clean repository ignores
```
