"""
Mobile Kivy View: Native Touch-Centric Phonebook Interface for Android APK
Reuses ContactModel and Levenshtein edit distance DSA engine.
"""
from ..data.contact_model import ContactModel
from ..dsa.edit_distance import search_and_rank_records


def run_mobile_app():
    """Entrypoint to launch the Kivy mobile touch interface on Android."""
    try:
        from kivy.app import App
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.textinput import TextInput
        from kivy.uix.label import Label
        from kivy.uix.button import Button
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout
    except ImportError:
        print("Kivy is required for mobile Android execution.")
        return

    class PhonebookMobileApp(App):
        def build(self):
            self.title = "Phonebook"
            self.model = ContactModel()
            self.root_layout = BoxLayout(orientation='vertical', padding=10, spacing=8)

            # Top branding
            header = Label(text="Phonebook Directory", size_hint_y=None, height=40, font_size=20, bold=True)
            self.root_layout.add_widget(header)

            # Search bar
            self.search_input = TextInput(
                hint_text="Search name or number...",
                multiline=False,
                size_hint_y=None,
                height=48,
                font_size=16
            )
            self.search_input.bind(text=self.on_search)
            self.root_layout.add_widget(self.search_input)

            # Scrollable contact list
            self.scroll_view = ScrollView()
            self.contacts_grid = GridLayout(cols=1, spacing=6, size_hint_y=None)
            self.contacts_grid.bind(minimum_height=self.contacts_grid.setter('height'))
            self.scroll_view.add_widget(self.contacts_grid)
            self.root_layout.add_widget(self.scroll_view)

            self.refresh_list()
            return self.root_layout

        def on_search(self, instance, query):
            self.refresh_list(query.strip())

        def refresh_list(self, query=""):
            self.contacts_grid.clear_widgets()
            records = self.model.get_all_records()
            filtered, _ = search_and_rank_records(records, query_string=query)

            for rec in filtered:
                card = BoxLayout(orientation='horizontal', size_hint_y=None, height=64, padding=8, spacing=8)
                info = BoxLayout(orientation='vertical')
                name_lbl = Label(text=rec.full_name, font_size=16, bold=True, halign='left')
                name_lbl.bind(size=name_lbl.setter('text_size'))
                num_lbl = Label(text=rec.phone_number, font_size=14, halign='left')
                num_lbl.bind(size=num_lbl.setter('text_size'))
                info.add_widget(name_lbl)
                info.add_widget(num_lbl)

                call_btn = Button(text="Call", size_hint_x=None, width=80)
                call_btn.bind(on_press=lambda inst, n=rec.full_name: self.model.record_call_interaction(n))

                card.add_widget(info)
                card.add_widget(call_btn)
                self.contacts_grid.add_widget(card)

    PhonebookMobileApp().run()
