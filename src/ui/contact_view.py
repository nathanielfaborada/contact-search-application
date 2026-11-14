# Responsive Threshold: Dynamic 680px breakpoint for layout adaptation
# Accessibility Note: High-contrast focus rings on interactive elements
# Ergonomics Note: Minimum 44px touch targets on primary controls
"""
Contact View: Responsive User-Centric Phonebook Interface
Dynamically adapts between Desktop (>=680px) and Mobile (<680px) without manual toggles.
Clean, intuitive, fully clickable cards, universal scrolling, and robust dialogs.
"""
import tkinter as tk
from tkinter import filedialog, messagebox

from .common.colors import (
    BG,
    CARD_BG,
    CARD_HOVER,
    CARD_SELECTED,
    DIVIDER,
    BORDER,
    TEXT_PRIMARY,
    TEXT_GREY,
    ACCENT,
    ACCENT_HOVER,
    SEARCH_BG,
    BADGE_BG,
    SUCCESS,
    SUCCESS_HOVER,
    DANGER,
    AVATAR_COLORS
)
from .shared.helpers import get_avatar_initial


class ContactView(tk.Tk):
    """Clean, user-friendly phonebook interface that automatically adapts to screen size."""

    def __init__(self):
        super().__init__()
        self.title("Contacts")
        self.geometry('860x640')
        self.minsize(360, 480)
        self.configure(bg=BG)

        # Dynamic layout mode based on screen width
        self.current_layout_mode = "desktop"  # "desktop" if width >= 680 else "mobile"
        self.mobile_active_screen = "list"     # "list" or "detail"

        self._placeholder_active = True
        self._current_records = []
        self._selected_record = None
        self._current_search_query = ""
        self._active_department = "All"
        self._only_favorites = False

        # Controller callbacks
        self.on_search_callback = None
        self.on_department_callback = None
        self.on_toggle_favorites_filter = None
        self.on_select_callback = None
        self.on_toggle_star_callback = None
        self.on_add_callback = None
        self.on_edit_callback = None
        self.on_delete_callback = None
        self.on_call_callback = None
        self.on_copy_callback = None
        self.on_export_csv_callback = None
        self.on_import_csv_callback = None

        self._build_scaffolding()
        self.bind('<Configure>', self._handle_window_resize)
        self._bind_shortcuts()
        self._bind_mousewheel_scrolling()

    def set_controller_callbacks(self, **callbacks):
        """Wires controller event listeners to view actions, supporting both naming conventions."""
        for hook_name, func in callbacks.items():
            setattr(self, hook_name, func)
            if not hook_name.endswith('_callback'):
                setattr(self, f"{hook_name}_callback", func)
            else:
                setattr(self, hook_name[:-9], func)

    # ------------------------------------------------------------------ Responsive Scaffolding
    def _build_scaffolding(self):
        """Constructs clean user-friendly header and viewport container."""
        # Top Navigation Bar
        self.top_bar = tk.Frame(self, bg=CARD_BG, height=58, highlightthickness=1, highlightbackground=DIVIDER)
        self.top_bar.pack(fill=tk.X)
        self.top_bar.pack_propagate(False)

        # Left Branding
        self.brand_frame = tk.Frame(self.top_bar, bg=CARD_BG)
        self.brand_frame.pack(side=tk.LEFT, padx=16, pady=10)

        self.title_label = tk.Label(
            self.brand_frame,
            text="Phonebook",
            font=('Helvetica', 15, 'bold'),
            bg=CARD_BG,
            fg=TEXT_PRIMARY
        )
        self.title_label.pack(side=tk.LEFT)

        self.counter_badge = tk.Label(
            self.brand_frame,
            text="0 contacts",
            font=('Helvetica', 10),
            bg=BADGE_BG,
            fg=TEXT_GREY,
            padx=8,
            pady=2
        )
        self.counter_badge.pack(side=tk.LEFT, padx=(10, 0))

        # Right Action Toolbar
        self.toolbar_frame = tk.Frame(self.top_bar, bg=CARD_BG)
        self.toolbar_frame.pack(side=tk.RIGHT, padx=16, pady=10)

        # "+ Add Contact" Primary Button (44px min touch target)
        self.add_btn = tk.Button(
            self.toolbar_frame,
            text="+ Add Contact",
            font=('Helvetica', 10, 'bold'),
            bg=ACCENT,
            fg='white',
            bd=0,
            relief='flat',
            padx=14,
            pady=7,
            cursor='hand2',
            activebackground=ACCENT_HOVER,
            command=self.open_add_dialog
        )
        self.add_btn.pack(side=tk.LEFT)

        # Master Content Viewport
        self.viewport = tk.Frame(self, bg=BG)
        self.viewport.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

    def _handle_window_resize(self, event):
        """Dynamically detects window/screen width and reflows layout seamlessly."""
        if event.widget != self:
            return

        new_mode = "desktop" if event.width >= 680 else "mobile"
        if new_mode != self.current_layout_mode:
            self.current_layout_mode = new_mode
            self.rebuild_layout_containers()

    def _bind_shortcuts(self):
        """Registers keyboard shortcuts."""
        self.bind('<Control-f>', lambda e: self._focus_search_entry())
        self.bind('/', lambda e: self._focus_search_entry())
        self.bind('<Control-n>', lambda e: self.open_add_dialog())
        self.bind('<Escape>', lambda e: self._handle_escape_press())

    def _bind_mousewheel_scrolling(self):
        """Binds mouse wheel scrolling globally with adaptive canvas detection."""
        def _on_mousewheel(event):
            delta = 0
            if event.delta:
                delta = int(-1 * (event.delta / 120))
            elif event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1

            if delta == 0:
                return

            # Check if active cursor widget is inside a specific Canvas (e.g. dialog canvas)
            target_canvas = None
            widget = event.widget
            while widget is not None:
                if isinstance(widget, tk.Canvas):
                    target_canvas = widget
                    break
                widget = getattr(widget, 'master', None)

            if target_canvas and target_canvas.winfo_exists():
                try:
                    target_canvas.yview_scroll(delta, 'units')
                    return
                except Exception:
                    pass

            if hasattr(self, '_canvas') and self._canvas.winfo_exists():
                try:
                    self._canvas.yview_scroll(delta, 'units')
                except Exception:
                    pass

        # Bind Windows, macOS, and Linux scroll events globally
        self.bind_all('<MouseWheel>', _on_mousewheel)
        self.bind_all('<Button-4>', _on_mousewheel)
        self.bind_all('<Button-5>', _on_mousewheel)

    def _focus_search_entry(self):
        if hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
            self.search_entry.focus_set()
            if self._placeholder_active:
                self._focus_in(None)
            return 'break'

    def _handle_escape_press(self):
        if self.current_layout_mode == "mobile" and self.mobile_active_screen == "detail":
            self.show_mobile_list_screen()
        elif hasattr(self, 'search_entry') and self.search_entry.winfo_exists():
            self._clear_search()

    # ------------------------------------------------------------------ Container Builders
    def rebuild_layout_containers(self):
        """Reflows workspace according to active screen size (Desktop Dual-Pane vs Mobile)."""
        for child in self.viewport.winfo_children():
            child.destroy()

        if self.current_layout_mode == "desktop":
            # Desktop: Dual Pane
            self.left_pane = tk.Frame(self.viewport, bg=BG, width=390)
            self.left_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
            self.left_pane.pack_propagate(False)

            self.right_pane = tk.Frame(self.viewport, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
            self.right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

            self._build_search_and_filters(parent=self.left_pane)
            self._build_scrollable_list(parent=self.left_pane)
            self._build_csv_footer(parent=self.left_pane)
            self._refresh_current_view()

        else:
            # Mobile: Single Screen
            self.mobile_container = tk.Frame(self.viewport, bg=BG)
            self.mobile_container.pack(fill=tk.BOTH, expand=True)

            if self.mobile_active_screen == "detail" and self._selected_record:
                self._render_mobile_detail_screen()
            else:
                self._render_mobile_list_screen()

    # ------------------------------------------------------------------ Search & Filter Bar
    def _build_search_and_filters(self, parent):
        """Builds clean search bar and dynamic department pills."""
        search_card = tk.Frame(parent, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
        search_card.pack(fill=tk.X, pady=(0, 6))

        search_inner = tk.Frame(search_card, bg=CARD_BG, padx=8, pady=6)
        search_inner.pack(fill=tk.X)

        tk.Label(search_inner, text="Q", font=('Helvetica', 11, 'bold'), bg=CARD_BG, fg=TEXT_GREY).pack(side=tk.LEFT, padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_inner,
            textvariable=self.search_var,
            font=('Helvetica', 11),
            bd=0,
            bg=CARD_BG,
            fg=TEXT_GREY,
            insertbackground=ACCENT,
            relief='flat'
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        if self._current_search_query:
            self.search_entry.insert(0, self._current_search_query)
            self.search_entry.config(fg=TEXT_PRIMARY)
            self._placeholder_active = False
        else:
            self.search_entry.insert(0, "Search name, number, tag...")
            self._placeholder_active = True

        self.search_entry.bind('<FocusIn>', self._focus_in)
        self.search_entry.bind('<FocusOut>', self._focus_out)
        self.search_var.trace_add('write', self._handle_search_change)

        self.clear_btn = tk.Label(search_inner, text="x", font=('Helvetica', 10, 'bold'), bg=CARD_BG, fg=TEXT_GREY, cursor='hand2')
        self.clear_btn.bind('<Button-1>', lambda e: self._clear_search())
        if self._current_search_query:
            self.clear_btn.pack(side=tk.RIGHT)

        # Dynamic Department Filter Chips
        self.chips_frame = tk.Frame(parent, bg=BG)
        self.chips_frame.pack(fill=tk.X, pady=(0, 6))
        self._render_department_chips(parent_frame=self.chips_frame)

    def _render_department_chips(self, parent_frame):
        """Renders dynamic clickable filter pills for All, Favorites, and Department tags."""
        for child in parent_frame.winfo_children():
            child.destroy()

        chips_scroll = tk.Frame(parent_frame, bg=BG)
        chips_scroll.pack(fill=tk.X)

        # Starred Filter Pill
        fav_bg = ACCENT if self._only_favorites else CARD_BG
        fav_fg = 'white' if self._only_favorites else TEXT_PRIMARY
        fav_pill = tk.Label(
            chips_scroll,
            text="* Starred",
            font=('Helvetica', 9, 'bold'),
            bg=fav_bg,
            fg=fav_fg,
            padx=8,
            pady=3,
            cursor='hand2',
            highlightthickness=1,
            highlightbackground=ACCENT if self._only_favorites else DIVIDER
        )
        fav_pill.pack(side=tk.LEFT, padx=(0, 4))
        fav_pill.bind('<Button-1>', lambda e: self._toggle_favorites_filter())

        # Department Pills
        departments = getattr(self, '_available_departments', ["All"])
        for dept in departments:
            is_active = (dept == self._active_department and not self._only_favorites)
            chip_bg = ACCENT if is_active else CARD_BG
            chip_fg = 'white' if is_active else TEXT_PRIMARY
            border_color = ACCENT if is_active else DIVIDER

            pill = tk.Label(
                chips_scroll,
                text=dept,
                font=('Helvetica', 9, 'bold' if is_active else 'normal'),
                bg=chip_bg,
                fg=chip_fg,
                padx=8,
                pady=3,
                cursor='hand2',
                highlightthickness=1,
                highlightbackground=border_color
            )
            pill.pack(side=tk.LEFT, padx=(0, 4))
            pill.bind('<Button-1>', lambda e, d=dept: self._select_department_tag(d))

    def _build_scrollable_list(self, parent):
        """Constructs scrollable frame for contact cards."""
        list_wrapper = tk.Frame(parent, bg=BG)
        list_wrapper.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(list_wrapper, bg=BG, highlightthickness=0)
        self._scrollbar = tk.Scrollbar(list_wrapper, orient='vertical', command=self._canvas.yview)

        self._list_frame = tk.Frame(self._canvas, bg=BG)
        self._list_frame.bind(
            '<Configure>',
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox('all')) if hasattr(self, '_canvas') and self._canvas.winfo_exists() else None
        )

        self._canvas_window = self._canvas.create_window((0, 0), window=self._list_frame, anchor='nw')
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_parent_resize(event):
            if event.widget == parent and hasattr(self, '_canvas') and self._canvas.winfo_exists():
                self._canvas.itemconfig(self._canvas_window, width=max(event.width - 18, 200))

        parent.bind('<Configure>', _on_parent_resize)

    def _build_csv_footer(self, parent):
        """Builds clean, subtle backup/restore actions at the bottom."""
        footer = tk.Frame(parent, bg=BG, pady=4)
        footer.pack(fill=tk.X)

        tk.Button(
            footer,
            text="Export CSV",
            font=('Helvetica', 8),
            bg=CARD_BG,
            fg=TEXT_GREY,
            bd=0,
            relief='flat',
            padx=8,
            pady=3,
            cursor='hand2',
            command=self._handle_export_csv
        ).pack(side=tk.LEFT)

        tk.Button(
            footer,
            text="Import CSV",
            font=('Helvetica', 8),
            bg=CARD_BG,
            fg=TEXT_GREY,
            bd=0,
            relief='flat',
            padx=8,
            pady=3,
            cursor='hand2',
            command=self._handle_import_csv
        ).pack(side=tk.LEFT, padx=(6, 0))

    # ------------------------------------------------------------------ Mobile View
    def _render_mobile_list_screen(self):
        """Full-screen mobile contacts directory."""
        self.mobile_active_screen = "list"
        for child in self.mobile_container.winfo_children():
            child.destroy()

        self._build_search_and_filters(parent=self.mobile_container)
        self._build_scrollable_list(parent=self.mobile_container)
        self._build_csv_footer(parent=self.mobile_container)
        self._render_directory_cards()

    def _render_mobile_detail_screen(self):
        """Full-screen mobile contact details with back button."""
        self.mobile_active_screen = "detail"
        for child in self.mobile_container.winfo_children():
            child.destroy()

        nav_bar = tk.Frame(self.mobile_container, bg=CARD_BG, height=44, highlightthickness=1, highlightbackground=DIVIDER)
        nav_bar.pack(fill=tk.X, pady=(0, 6))
        nav_bar.pack_propagate(False)

        tk.Button(
            nav_bar,
            text="< Contacts",
            font=('Helvetica', 10, 'bold'),
            bg=CARD_BG,
            fg=ACCENT,
            bd=0,
            relief='flat',
            padx=10,
            pady=6,
            cursor='hand2',
            command=self.show_mobile_list_screen
        ).pack(side=tk.LEFT)

        detail_card = tk.Frame(self.mobile_container, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER)
        detail_card.pack(fill=tk.BOTH, expand=True)

        self._render_contact_dossier(parent=detail_card, record=self._selected_record)

    def show_mobile_list_screen(self):
        self.mobile_active_screen = "list"
        self._render_mobile_list_screen()

    def show_mobile_detail_screen(self, record):
        self._selected_record = record
        self._render_mobile_detail_screen()

    # ------------------------------------------------------------------ Rendering Data
    def update_directory_view(
        self,
        records_list,
        total_count,
        selected_record=None,
        search_query="",
        active_department="All",
        only_favorites=False,
        available_departments=None
    ):
        """Receives filtered state and refreshes presentation."""
        self._current_records = records_list
        self._selected_record = selected_record
        self._current_search_query = search_query
        self._active_department = active_department
        self._only_favorites = only_favorites
        self._available_departments = available_departments if available_departments else ["All"]

        # Update counter badge
        count_text = f"{total_count} contacts" if total_count != 1 else "1 contact"
        self.counter_badge.config(text=count_text)

        self._refresh_current_view()

    def _refresh_current_view(self):
        """Refreshes visible containers based on active mode."""
        if self.current_layout_mode == "desktop":
            if hasattr(self, 'chips_frame') and self.chips_frame.winfo_exists():
                self._render_department_chips(parent_frame=self.chips_frame)
            self._render_directory_cards()
            self._render_desktop_detail_pane()
        else:
            if self.mobile_active_screen == "detail" and self._selected_record:
                self._render_mobile_detail_screen()
            else:
                self._render_mobile_list_screen()

    def _render_directory_cards(self):
        """Renders contact card items into list."""
        if not hasattr(self, '_list_frame') or not self._list_frame.winfo_exists():
            return

        for child in self._list_frame.winfo_children():
            child.destroy()

        if not self._current_records:
            empty_box = tk.Frame(self._list_frame, bg=CARD_BG, highlightthickness=1, highlightbackground=DIVIDER, pady=28)
            empty_box.pack(fill=tk.X, pady=6)
            tk.Label(empty_box, text="No contacts found", font=('Helvetica', 11, 'bold'), bg=CARD_BG, fg=TEXT_PRIMARY).pack()
            tk.Label(empty_box, text="Try typing a different name or number", font=('Helvetica', 9), bg=CARD_BG, fg=TEXT_GREY).pack(pady=(4, 0))
            return

        for index, record in enumerate(self._current_records):
            avatar_color = AVATAR_COLORS[index % len(AVATAR_COLORS)]
            is_selected = (self._selected_record and self._selected_record.full_name == record.full_name)
            self._render_single_card(record, avatar_color, is_selected)

        self._list_frame.update_idletasks()
        if hasattr(self, '_canvas') and self._canvas.winfo_exists():
            self._canvas.configure(scrollregion=self._canvas.bbox('all'))

    def _render_single_card(self, record, avatar_color, is_selected):
        """Renders an individual clean contact card with 100% surface clickability."""
        card_bg = CARD_SELECTED if is_selected and self.current_layout_mode == "desktop" else CARD_BG
        border_color = ACCENT if is_selected and self.current_layout_mode == "desktop" else DIVIDER

        card = tk.Frame(self._list_frame, bg=card_bg, highlightthickness=1, highlightbackground=border_color, cursor='hand2')
        card.pack(fill=tk.X, pady=2)

        inner = tk.Frame(card, bg=card_bg, padx=10, pady=7)
        inner.pack(fill=tk.X)

        # Avatar circle
        av = tk.Canvas(inner, width=38, height=38, bg=card_bg, highlightthickness=0)
        av.pack(side=tk.LEFT, padx=(0, 10))
        av.create_oval(2, 2, 36, 36, fill=avatar_color, outline='')
        av_txt = av.create_text(19, 19, text=get_avatar_initial(record.full_name), fill='white', font=('Helvetica', 12, 'bold'))

        # Name and Number Column
        info_col = tk.Frame(inner, bg=card_bg)
        info_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        name_row = tk.Frame(info_col, bg=card_bg)
        name_row.pack(fill=tk.X)

        name_lbl = tk.Label(name_row, text=record.full_name, font=('Helvetica', 11, 'bold'), bg=card_bg, fg=TEXT_PRIMARY, anchor='w')
        name_lbl.pack(side=tk.LEFT)

        dept_badge = None
        if record.department and record.department != "General":
            dept_badge = tk.Label(
                name_row,
                text=record.department,
                font=('Helvetica', 8),
                bg=BADGE_BG,
                fg=TEXT_GREY,
                padx=5,
                pady=1
            )
            dept_badge.pack(side=tk.LEFT, padx=(6, 0))

        num_lbl = tk.Label(info_col, text=record.phone_number, font=('Helvetica', 10), bg=card_bg, fg=TEXT_GREY, anchor='w')
        num_lbl.pack(fill=tk.X, pady=(1, 0))

        # Star toggle button (Excluded from card select so user can star without re-routing)
        star_char = "[*]" if record.is_favorite else "[o]"
        star_fg = '#FF9500' if record.is_favorite else TEXT_GREY
        star_btn = tk.Label(inner, text=star_char, font=('Helvetica', 10, 'bold'), bg=card_bg, fg=star_fg, cursor='hand2')
        star_btn.pack(side=tk.RIGHT, padx=(6, 0))
        star_btn.bind('<Button-1>', lambda e, n=record.full_name: self._handle_star_click(n))

        # Chevron arrow
        chevron = tk.Label(inner, text=">", font=('Helvetica', 10, 'bold'), bg=card_bg, fg=ACCENT if is_selected else TEXT_GREY)
        chevron.pack(side=tk.RIGHT, padx=(4, 0))

        # Tap / Click handler
        def on_card_click(_event):
            if self.current_layout_mode == "mobile":
                self.show_mobile_detail_screen(record)
            else:
                callback = self.on_select_callback or getattr(self, 'on_select', None)
                if callback:
                    callback(record.full_name)

        # Bind EVERY child element on the card to ensure 100% click reliability
        clickable_widgets = [card, inner, av, info_col, name_row, name_lbl, num_lbl, chevron]
        if dept_badge:
            clickable_widgets.append(dept_badge)

        for w in clickable_widgets:
            w.bind('<Button-1>', on_card_click)
            w.config(cursor='hand2')

        # Also bind canvas internal elements
        av.tag_bind('all', '<Button-1>', on_card_click)

    # ------------------------------------------------------------------ Contact Profile Details
    def _render_desktop_detail_pane(self):
        """Renders contact profile in desktop right pane with full scroll support."""
        if not hasattr(self, 'right_pane') or not self.right_pane.winfo_exists():
            return

        for child in self.right_pane.winfo_children():
            child.destroy()

        if not self._selected_record:
            ph = tk.Frame(self.right_pane, bg=CARD_BG)
            ph.place(relx=0.5, rely=0.5, anchor='center')

            tk.Label(ph, text="No contact selected", font=('Helvetica', 13, 'bold'), bg=CARD_BG, fg=TEXT_PRIMARY).pack()
            tk.Label(ph, text="Select a contact to view information and actions.", font=('Helvetica', 10), bg=CARD_BG, fg=TEXT_GREY).pack(pady=(4, 0))
            return

        detail_canvas = tk.Canvas(self.right_pane, bg=CARD_BG, highlightthickness=0)
        detail_scroll = tk.Scrollbar(self.right_pane, orient='vertical', command=detail_canvas.yview)

        detail_inner = tk.Frame(detail_canvas, bg=CARD_BG)
        detail_inner.bind(
            '<Configure>',
            lambda e: detail_canvas.configure(scrollregion=detail_canvas.bbox('all')) if detail_canvas.winfo_exists() else None
        )
        d_win = detail_canvas.create_window((0, 0), window=detail_inner, anchor='nw')
        detail_canvas.configure(yscrollcommand=detail_scroll.set)

        detail_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        detail_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_right_pane_resize(e):
            if e.widget == self.right_pane and detail_canvas.winfo_exists():
                detail_canvas.itemconfig(d_win, width=max(e.width - 18, 200))

        self.right_pane.bind('<Configure>', _on_right_pane_resize)

        self._render_contact_dossier(parent=detail_inner, record=self._selected_record)
        detail_inner.update_idletasks()
        if detail_canvas.winfo_exists():
            detail_canvas.configure(scrollregion=detail_canvas.bbox('all'))

    def _render_contact_dossier(self, parent, record):
        """Renders clean, user-friendly contact profile without developer clutter."""
        content = tk.Frame(parent, bg=CARD_BG, padx=24, pady=22)
        content.pack(fill=tk.BOTH, expand=True)

        # Header profile
        hdr_row = tk.Frame(content, bg=CARD_BG)
        hdr_row.pack(fill=tk.X, pady=(0, 16))

        color_idx = abs(hash(record.full_name)) % len(AVATAR_COLORS)
        av_color = AVATAR_COLORS[color_idx]

        av = tk.Canvas(hdr_row, width=64, height=64, bg=CARD_BG, highlightthickness=0)
        av.pack(side=tk.LEFT, padx=(0, 16))
        av.create_oval(2, 2, 62, 62, fill=av_color, outline='')
        av.create_text(32, 32, text=get_avatar_initial(record.full_name), fill='white', font=('Helvetica', 20, 'bold'))

        info_col = tk.Frame(hdr_row, bg=CARD_BG)
        info_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        name_box = tk.Frame(info_col, bg=CARD_BG)
        name_box.pack(fill=tk.X)
        tk.Label(name_box, text=record.full_name, font=('Helvetica', 16, 'bold'), bg=CARD_BG, fg=TEXT_PRIMARY, anchor='w').pack(side=tk.LEFT)

        star_tag = tk.Label(
            name_box,
            text="* Starred" if record.is_favorite else "[Favorite]",
            font=('Helvetica', 9, 'bold'),
            bg=CARD_BG,
            fg='#FF9500' if record.is_favorite else TEXT_GREY,
            cursor='hand2'
        )
        star_tag.pack(side=tk.LEFT, padx=(8, 0))
        star_tag.bind('<Button-1>', lambda e: self._handle_star_click(record.full_name))

        tk.Label(info_col, text=record.phone_number, font=('Helvetica', 12, 'bold'), bg=CARD_BG, fg=ACCENT, anchor='w').pack(fill=tk.X, pady=(2, 2))

        if record.department:
            tk.Label(info_col, text=f"Group: {record.department}", font=('Helvetica', 9), bg=CARD_BG, fg=TEXT_GREY, anchor='w').pack(fill=tk.X)

        # Action Buttons (Call, Copy, Edit, Delete)
        actions = tk.Frame(content, bg=CARD_BG)
        actions.pack(fill=tk.X, pady=(0, 18))

        # Big Call Button (Green)
        def _invoke_call():
            callback = self.on_call_callback or getattr(self, 'on_call', None)
            if callback:
                callback(record.full_name, record.phone_number)

        tk.Button(
            actions,
            text="Call Contact",
            font=('Helvetica', 10, 'bold'),
            bg=SUCCESS,
            fg='white',
            bd=0,
            relief='flat',
            padx=16,
            pady=8,
            cursor='hand2',
            activebackground=SUCCESS_HOVER,
            command=_invoke_call
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Copy Button
        tk.Button(
            actions,
            text="Copy Number",
            font=('Helvetica', 10),
            bg=DIVIDER,
            fg=TEXT_PRIMARY,
            bd=0,
            relief='flat',
            padx=12,
            pady=8,
            cursor='hand2',
            command=lambda: self._handle_copy_number(record.phone_number)
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Edit Button
        tk.Button(
            actions,
            text="Edit",
            font=('Helvetica', 10),
            bg=DIVIDER,
            fg=TEXT_PRIMARY,
            bd=0,
            relief='flat',
            padx=12,
            pady=8,
            cursor='hand2',
            command=lambda: self.open_edit_dialog(record)
        ).pack(side=tk.LEFT, padx=(0, 8))

        # Delete Button
        def _invoke_delete():
            callback = self.on_delete_callback or getattr(self, 'on_delete', None)
            if callback:
                callback(record.full_name)

        tk.Button(
            actions,
            text="Delete",
            font=('Helvetica', 10),
            bg=CARD_BG,
            fg=DANGER,
            bd=1,
            relief='solid',
            padx=12,
            pady=7,
            cursor='hand2',
            command=_invoke_delete
        ).pack(side=tk.LEFT)

        # Contact Details Card (Only shows fields that exist)
        details_box = tk.Frame(content, bg=BG, highlightthickness=1, highlightbackground=DIVIDER, padx=14, pady=12)
        details_box.pack(fill=tk.X)

        tk.Label(details_box, text="Contact Information", font=('Helvetica', 10, 'bold'), bg=BG, fg=TEXT_PRIMARY, anchor='w').pack(fill=tk.X, pady=(0, 6))

        def add_field_row(label_text, val_text):
            if val_text:
                r = tk.Frame(details_box, bg=BG)
                r.pack(fill=tk.X, pady=2)
                tk.Label(r, text=label_text, font=('Helvetica', 9), bg=BG, fg=TEXT_GREY, width=14, anchor='w').pack(side=tk.LEFT)
                tk.Label(r, text=val_text, font=('Helvetica', 9, 'bold'), bg=BG, fg=TEXT_PRIMARY, anchor='w').pack(side=tk.LEFT)

        add_field_row("Email:", record.email)
        add_field_row("Office / Room:", record.office)
        add_field_row("Notes:", record.notes)
        add_field_row("Last Called:", record.last_called)

        if not any([record.email, record.office, record.notes, record.last_called]):
            tk.Label(details_box, text="No additional notes recorded for this contact.", font=('Helvetica', 9), bg=BG, fg=TEXT_GREY, anchor='w').pack(fill=tk.X)

    # ------------------------------------------------------------------ Dialogs
    def open_add_dialog(self):
        """Displays modal to add new contact."""
        self._open_form_dialog(title="New Contact", record=None, is_edit=False)

    def open_edit_dialog(self, record):
        """Displays modal to edit contact."""
        self._open_form_dialog(title=f"Edit Contact - {record.full_name}", record=record, is_edit=True)

    def _open_form_dialog(self, title, record, is_edit):
        """Builds clean add/edit contact form modal with bottom-pinned action buttons."""
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry('420x520')
        dialog.minsize(380, 460)
        dialog.configure(bg=BG)
        dialog.transient(self)

        def close_dialog():
            try:
                dialog.grab_release()
            except Exception:
                pass
            dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        try:
            dialog.grab_set()
        except Exception:
            pass

        hdr = tk.Frame(dialog, bg=ACCENT, height=48)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title, font=('Helvetica', 12, 'bold'), bg=ACCENT, fg='white').pack(side=tk.LEFT, padx=16, pady=12)

        # PIN BUTTONS AT THE BOTTOM FIRST so they are ALWAYS visible and never cut off!
        btn_bar = tk.Frame(dialog, bg=BG, padx=20, pady=14)
        btn_bar.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Button(
            btn_bar,
            text="Cancel",
            font=('Helvetica', 10),
            bg=DIVIDER,
            fg=TEXT_PRIMARY,
            bd=0,
            relief='flat',
            padx=16,
            pady=8,
            cursor='hand2',
            command=close_dialog
        ).pack(side=tk.LEFT)

        # Form Scrollable Canvas / Frame
        form_wrapper = tk.Frame(dialog, bg=BG)
        form_wrapper.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 0))

        form_canvas = tk.Canvas(form_wrapper, bg=BG, highlightthickness=0)
        form_scroll = tk.Scrollbar(form_wrapper, orient='vertical', command=form_canvas.yview)

        form = tk.Frame(form_canvas, bg=BG)
        form.bind(
            '<Configure>',
            lambda e: form_canvas.configure(scrollregion=form_canvas.bbox('all')) if form_canvas.winfo_exists() else None
        )
        canvas_win = form_canvas.create_window((0, 0), window=form, anchor='nw')
        form_canvas.configure(yscrollcommand=form_scroll.set)

        form_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        form_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_dialog_configure(event):
            if event.widget == dialog and form_canvas.winfo_exists():
                form_canvas.itemconfig(canvas_win, width=max(event.width - 55, 200))

        dialog.bind('<Configure>', _on_dialog_configure)

        def make_input(label_text, default_val=""):
            tk.Label(form, text=label_text, font=('Helvetica', 9, 'bold'), bg=BG, fg=TEXT_GREY, anchor='w').pack(fill=tk.X)
            box = tk.Frame(form, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
            box.pack(fill=tk.X, pady=(1, 6))
            entry = tk.Entry(box, font=('Helvetica', 11), bd=0, bg=CARD_BG, fg=TEXT_PRIMARY, insertbackground=ACCENT)
            entry.pack(fill=tk.X, padx=8, pady=5)
            if default_val:
                entry.insert(0, str(default_val))
            return entry

        name_in = make_input("Name *", record.full_name if record else "")
        phone_in = make_input("Phone Number *", record.phone_number if record else "")
        dept_in = make_input("Group / Tag (e.g. Faculty, Student)", record.department if record else "General")
        email_in = make_input("Email (Optional)", record.email if record else "")
        office_in = make_input("Office / Room (Optional)", record.office if record else "")
        notes_in = make_input("Notes (Optional)", record.notes if record else "")

        fav_var = tk.BooleanVar(value=record.is_favorite if record else False)
        tk.Checkbutton(
            form,
            text="Add to Favorites",
            variable=fav_var,
            font=('Helvetica', 9),
            bg=BG,
            fg=TEXT_PRIMARY,
            activebackground=BG,
            selectcolor=CARD_BG
        ).pack(anchor='w', pady=(2, 6))

        # Focus first field immediately
        name_in.focus_set()

        def submit():
            name = name_in.get().strip()
            phone = phone_in.get().strip()
            dept = dept_in.get().strip()
            email = email_in.get().strip()
            office = office_in.get().strip()
            notes = notes_in.get().strip()
            is_fav = fav_var.get()

            if is_edit:
                callback = self.on_edit_callback or getattr(self, 'on_edit', None)
                if callback:
                    success, msg = callback(
                        old_name=record.full_name,
                        new_name=name,
                        new_number=phone,
                        department=dept,
                        email=email,
                        office=office,
                        notes=notes,
                        is_favorite=is_fav,
                        parent_dialog=dialog
                    )
                    if not success:
                        messagebox.showwarning("Notice", msg, parent=dialog)
                        return
                    close_dialog()
                    self.show_info("Updated", f'"{name}" updated.')
            else:
                callback = self.on_add_callback or getattr(self, 'on_add', None)
                if callback:
                    success, msg = callback(
                        name=name,
                        number=phone,
                        department=dept,
                        email=email,
                        office=office,
                        notes=notes,
                        is_favorite=is_fav,
                        parent_dialog=dialog
                    )
                    if not success:
                        messagebox.showwarning("Notice", msg, parent=dialog)
                        return
                    close_dialog()
                    self.show_info("Saved", f'"{name}" added to contacts.')

        # Save Button (Pinned at bottom)
        tk.Button(
            btn_bar,
            text="Save Contact",
            font=('Helvetica', 10, 'bold'),
            bg=ACCENT,
            fg='white',
            bd=0,
            relief='flat',
            padx=18,
            pady=8,
            cursor='hand2',
            activebackground=ACCENT_HOVER,
            command=submit
        ).pack(side=tk.RIGHT)

    # ------------------------------------------------------------------ Event Handlers
    def _focus_in(self, _event):
        if self._placeholder_active:
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=TEXT_PRIMARY)
            self._placeholder_active = False

    def _focus_out(self, _event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search name, number, tag...")
            self.search_entry.config(fg=TEXT_GREY)
            self._placeholder_active = True
            if hasattr(self, 'clear_btn'):
                self.clear_btn.pack_forget()

    def _clear_search(self):
        self.search_entry.delete(0, tk.END)
        self._focus_out(None)
        if self.on_search_callback:
            self.on_search_callback("")

    def _handle_search_change(self, *_args):
        if self._placeholder_active:
            query = ""
            if hasattr(self, 'clear_btn'):
                self.clear_btn.pack_forget()
        else:
            query = self.search_var.get().strip()
            if hasattr(self, 'clear_btn'):
                if query:
                    self.clear_btn.pack(side=tk.RIGHT, padx=(4, 0))
                else:
                    self.clear_btn.pack_forget()

        if self.on_search_callback:
            self.on_search_callback(query)

    def _select_department_tag(self, dept_name):
        self._only_favorites = False
        if self.on_department_callback:
            self.on_department_callback(dept_name)

    def _toggle_favorites_filter(self):
        if self.on_toggle_favorites_filter:
            self.on_toggle_favorites_filter()

    def _handle_star_click(self, contact_name):
        if self.on_toggle_star_callback:
            self.on_toggle_star_callback(contact_name)

    def _handle_copy_number(self, phone_number):
        self.clipboard_clear()
        self.clipboard_append(phone_number)
        messagebox.showinfo("Copied", f'"{phone_number}" copied to clipboard!', parent=self)

    def _handle_export_csv(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Contacts to CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path and self.on_export_csv_callback:
            self.on_export_csv_callback(path)

    def _handle_import_csv(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Import Contacts from CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if path and self.on_import_csv_callback:
            self.on_import_csv_callback(path)

    def show_info(self, title, message):
        messagebox.showinfo(title, message, parent=self)

    def ask_confirmation(self, title, question, parent=None):
        target_parent = parent if (parent and parent.winfo_exists()) else self
        had_grab = False
        try:
            if target_parent and target_parent != self:
                try:
                    target_parent.grab_release()
                    had_grab = True
                except Exception:
                    pass
            result = messagebox.askyesno(title, question, parent=target_parent)
        finally:
            if had_grab and target_parent and target_parent.winfo_exists():
                try:
                    target_parent.grab_set()
                except Exception:
                    pass
        return result
