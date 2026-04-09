import json
import os
import tkinter as tk
from tkinter import messagebox

CONTACTS_FILE = os.path.join(os.path.dirname(__file__), 'contacts.json')

# --- Colors ---
BG           = '#F2F2F7'
CARD_BG      = '#FFFFFF'
DIVIDER      = '#E5E5EA'
TEXT_PRIMARY = '#000000'
TEXT_GREY    = '#8E8E93'
ACCENT       = '#007AFF'
SEARCH_BG    = '#E5E5EA'
AVATAR_COLORS = ['#FF6B6B', '#A855F7', '#3B82F6', '#10B981', '#F59E0B', '#6366F1']

def load_contacts():
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_contacts(contacts):
    with open(CONTACTS_FILE, 'w') as f:
        json.dump(contacts, f, indent=4)


# --- Edit Distance (O(m*n)) ---
def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1,
                           dp[i][j - 1] + 1,
                           dp[i - 1][j - 1] + cost)
    return dp[m][n]


class ContactApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Contacts")
        self.geometry('430x750')
        self.resizable(False, False)
        self.configure(bg=BG)
        self._placeholder_active = True
        self.contacts = load_contacts()
        self._build_ui()

    # ------------------------------------------------------------------ Build

    def _build_ui(self):
        self._build_topbar()
        self._build_list()
        # Set up trace AFTER both topbar and list are fully built
        self.search_var.trace_add('write', self._on_search)

    def _build_topbar(self):
        top = tk.Frame(self, bg=BG, pady=12, padx=14)
        top.pack(fill=tk.X)

        # Search box
        search_box = tk.Frame(top, bg=SEARCH_BG)
        search_box.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=7, ipadx=6)

        tk.Label(search_box, text="  Q", font=('Helvetica', 13),
                 bg=SEARCH_BG, fg=TEXT_GREY).pack(side=tk.LEFT)

        self.search_var = tk.StringVar()
        self._entry = tk.Entry(search_box, textvariable=self.search_var,
                               font=('Helvetica', 13), bd=0, bg=SEARCH_BG,
                               fg=TEXT_GREY, insertbackground=ACCENT, relief='flat')
        self._entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        self._entry.insert(0, "Search Contact")
        self._entry.bind('<FocusIn>',  self._focus_in)
        self._entry.bind('<FocusOut>', self._focus_out)

        # "+" add button
        add_btn = tk.Canvas(top, width=34, height=34, bg=BG, highlightthickness=0)
        add_btn.pack(side=tk.RIGHT, padx=(10, 0))
        add_btn.create_oval(2, 2, 32, 32, outline=ACCENT, width=2)
        add_btn.create_text(17, 17, text='+', fill=ACCENT, font=('Helvetica', 18))
        add_btn.bind('<Button-1>', lambda e: self._open_add_dialog())

    def _build_list(self):
        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(fill=tk.BOTH, expand=True)

        self._canvas = tk.Canvas(wrapper, bg=BG, highlightthickness=0)
        scroll = tk.Scrollbar(wrapper, orient='vertical', command=self._canvas.yview)

        self._list_frame = tk.Frame(self._canvas, bg=BG)
        self._list_frame.bind('<Configure>',
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox('all')))

        self._canvas.create_window((0, 0), window=self._list_frame, anchor='nw')
        self._canvas.configure(yscrollcommand=scroll.set)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._canvas.bind('<MouseWheel>',
            lambda e: self._canvas.yview_scroll(int(-1 * e.delta / 120), 'units'))

        self._render_contacts(self.contacts)

    def _render_contacts(self, contacts):
        for w in self._list_frame.winfo_children():
            w.destroy()

        if not contacts:
            tk.Label(self._list_frame, text="No contacts found",
                     font=('Helvetica', 13), bg=BG, fg=TEXT_GREY).pack(pady=40)
            return

        for i, (name, number) in enumerate(contacts.items()):
            color = AVATAR_COLORS[i % len(AVATAR_COLORS)]
            self._add_row(name, number, color)

    def _add_row(self, name, number, color):
        # Card row
        row = tk.Frame(self._list_frame, bg=CARD_BG, cursor='hand2')
        row.pack(fill=tk.X)

        # Avatar circle
        av = tk.Canvas(row, width=52, height=62, bg=CARD_BG, highlightthickness=0)
        av.pack(side=tk.LEFT, padx=(14, 0))
        av.create_oval(6, 11, 46, 51, fill=color, outline='')
        av.create_text(26, 31, text=name.strip()[0].upper(),
                       fill='white', font=('Helvetica', 16, 'bold'))

        # Name
        name_lbl = tk.Label(row, text=name, font=('Helvetica', 14, 'bold'),
                            bg=CARD_BG, fg=TEXT_PRIMARY, anchor='w', width=10)
        name_lbl.pack(side=tk.LEFT, padx=(10, 6), pady=18)

        # Vertical divider
        sep = tk.Frame(row, bg=DIVIDER, width=1)
        sep.pack(side=tk.LEFT, fill=tk.Y, pady=14)

        # Phone number
        num_lbl = tk.Label(row, text=number, font=('Helvetica', 13),
                           bg=CARD_BG, fg=TEXT_GREY, anchor='w')
        num_lbl.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        # Three dots menu
        dots = tk.Label(row, text='• • •', font=('Helvetica', 10),
                        bg=CARD_BG, fg=TEXT_GREY, cursor='hand2')
        dots.pack(side=tk.RIGHT, padx=12)
        dots.bind('<Button-1>', lambda e, n=name, num=number: self._on_dots(n, num))

        # Thin bottom divider
        tk.Frame(self._list_frame, bg=DIVIDER, height=1).pack(fill=tk.X, padx=14)

        # Click anywhere on row to view info
        for w in (row, av, name_lbl, num_lbl):
            w.bind('<Button-1>', lambda e, n=name, num=number: self._on_contact(n, num))

    # ------------------------------------------------------------------ Events

    def _focus_in(self, _):
        if self._placeholder_active:
            self._entry.delete(0, tk.END)
            self._entry.config(fg=TEXT_PRIMARY)
            self._placeholder_active = False

    def _focus_out(self, _):
        if not self._entry.get():
            self._entry.insert(0, "Search Contact")
            self._entry.config(fg=TEXT_GREY)
            self._placeholder_active = True

    def _on_search(self, *_):
        if self._placeholder_active:
            self._render_contacts(self.contacts)
            return
        query = self.search_var.get().strip()
        if not query:
            self._render_contacts(self.contacts)
            return
        if query.isdigit():
            scored = sorted(self.contacts.items(), key=lambda x: edit_distance(query, x[1]))
            min_d = edit_distance(query, scored[0][1])
            results = {k: v for k, v in scored if edit_distance(query, v) == min_d}
        else:
            q = query.lower()
            results = {k: v for k, v in self.contacts.items() if q in k.lower()}
        self._render_contacts(results)

    def _on_contact(self, name, number):
        messagebox.showinfo("Contact Info", f"Name:   {name}\nNumber: {number}")

    def _on_dots(self, name, number):
        messagebox.askquestion("Options", f"Call {name} at {number}?")

    def _open_add_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("New Contact")
        dialog.geometry('360x320')
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.grab_set()  # block main window while dialog is open

        # Header
        header = tk.Frame(dialog, bg=ACCENT, height=55)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="New Contact", font=('Helvetica', 16, 'bold'),
                 bg=ACCENT, fg='white').pack(side=tk.LEFT, padx=16, pady=14)

        # Form
        form = tk.Frame(dialog, bg=BG, padx=24, pady=20)
        form.pack(fill=tk.BOTH, expand=True)

        def make_field(label_text):
            tk.Label(form, text=label_text, font=('Helvetica', 11),
                     bg=BG, fg=TEXT_GREY, anchor='w').pack(fill=tk.X)
            box = tk.Frame(form, bg=CARD_BG, highlightthickness=1,
                           highlightbackground=DIVIDER)
            box.pack(fill=tk.X, pady=(2, 14))
            entry = tk.Entry(box, font=('Helvetica', 13), bd=0, bg=CARD_BG,
                             fg=TEXT_PRIMARY, insertbackground=ACCENT)
            entry.pack(fill=tk.X, padx=10, pady=8)
            return entry

        name_entry   = make_field("Name")
        number_entry = make_field("Phone Number")

        def save():
            name   = name_entry.get().strip()
            number = number_entry.get().strip()

            if not name:
                messagebox.showwarning("Missing", "Please enter a name.", parent=dialog)
                return
            if not number:
                messagebox.showwarning("Missing", "Please enter a phone number.", parent=dialog)
                return
            if not number.isdigit():
                messagebox.showwarning("Invalid", "Phone number must contain digits only.", parent=dialog)
                return
            if name in self.contacts:
                messagebox.showwarning("Duplicate", f'"{name}" already exists.', parent=dialog)
                return

            self.contacts[name] = number
            save_contacts(self.contacts)
            self._render_contacts(self.contacts)
            dialog.destroy()

        # Buttons
        btn_row = tk.Frame(form, bg=BG)
        btn_row.pack(fill=tk.X)
        tk.Button(btn_row, text="Cancel", font=('Helvetica', 12), bg=DIVIDER,
                  fg=TEXT_PRIMARY, bd=0, relief='flat', padx=16, pady=8,
                  cursor='hand2', command=dialog.destroy).pack(side=tk.LEFT)
        tk.Button(btn_row, text="Save", font=('Helvetica', 12, 'bold'), bg=ACCENT,
                  fg='white', bd=0, relief='flat', padx=16, pady=8,
                  cursor='hand2', activebackground='#005BBB', command=save).pack(side=tk.RIGHT)

    def _show_about(self):
        messagebox.showinfo("About",
            "Practice Application\nBSCS 2-A\n\n"
            "Faborada, Nathaniel F.\nBodino, John Paul P.\n\n"
            "College of Mary Immaculate")

    def display(self):
        self.mainloop()


# --- Builder / Director ---
class ContactAppBuilder:
    def __init__(self):
        self.contact_app = ContactApp()

    def build_menu_choice(self):
        pass  # main screen is the contact list

    def build_display(self):
        self.contact_app.display()


class ContactAppDirector:
    def __init__(self, builder):
        self.builder = builder

    def construct(self):
        self.builder.build_menu_choice()
        self.builder.build_display()


if __name__ == "__main__":
    builder = ContactAppBuilder()
    director = ContactAppDirector(builder)
    director.construct()

# Time complexity: O(m * n)
# m = length of input, n = length of contact number
# We created Contact Search because searching contacts is a common daily task.
