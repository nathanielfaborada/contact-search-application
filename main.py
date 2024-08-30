import tkinter as tk
from tkinter import messagebox

class ContactUserInterface:
    def __init__(self, contact_app):
        self.contact_app = contact_app
        self.result_text = tk.StringVar() 

    def contact_account_form(self):
        for widget in self.contact_app.winfo_children():
            widget.pack_forget()

        self.contact_app._add_label(text="Contact Search", font=('Helvetica', 50), bg='darkgreen', foreground='white',
                                    width=70)

        self.contact_number_entry = self.contact_app._add_entry_with_placeholder("Contact Number", "Enter your contact number")

        self.button = self.contact_app._add_button(text="Search", foreground='white', command=self.contact_search, font=("Helvetica", 30), width=10, bg='forest green')

        self.contact_app._add_label(textvariable=self.result_text, font=('Helvetica', 35), bg='darkgreen',
                                    foreground='white', width=50)

        self.back_button = self.contact_app._add_button(text="back",  foreground='white', command=self.contact_app.menu_choice, font=("Helvetica", 30), width=10, bg='forest green')

    #Edit Distance
    def operation_contact_search(self, s1, s2): 
        len_string1 = len(s1)
        len_string2 = len(s2)
        
        dp = []
        row = 0
        while row <= len_string1:
            dp.append([0] * (len_string2 + 1))
            row += 1
        
        i = 0
        while i < len_string1 + 1:
            dp[i][0] = i
            i += 1

        j = 0
        while j < len_string2 + 1:
            dp[0][j] = j
            j += 1

        i = 1
        while i < len_string1 + 1:
            j = 1
            while j < len_string2 + 1:
                cost = 0 if s1[i - 1] == s2[j - 1] else 1
                print(cost)
                dp[i][j] = min(dp[i - 1][j] + 1,
                               dp[i][j - 1] + 1,  
                               dp[i - 1][j - 1] + cost) 
                j += 1
            i += 1
        
        return dp[len_string1][len_string2]

    def contact_search(self):
        contact_number = self.contact_number_entry.get()
        
        if not contact_number.isdigit():
            messagebox.showinfo("Invalid Input", "Number Only.")
            return
        #name-number
        contact = {
            "Natl": "09950216326262423203",
            "JPul": "023953451623392924183",
            "Jby": "0239451672383829442344",
            "Jt": "091235548075122345",
            "Vnalo": "09121215376663248",
            "K neth":"091207966542342310"
        }

        if contact_number:
            min_dist = float('inf')
            closest_contacts = []

            for name, number in contact.items():
                dist = self.operation_contact_search(contact_number, number)
                if dist < min_dist:
                    min_dist = dist
                    closest_contacts = [(name, number)]
                elif dist == min_dist:
                    closest_contacts.append((name, number))

            if closest_contacts:
                self.result_text.set("Closest Contacts:\n" + "\n".join(
                    [f"Name: {name}    Phone Number: {number}" for name, number in closest_contacts]))


class ShowMessage: 
    def __init__(self, message) -> None:
        self.__message = message

    def __call__(self):
        messagebox.showinfo(title="Acknowledgement", message=self.__message)


class ContactAppBuilder:
    def __init__(self):
        self.contact_app = ContactApp()

    def build_menu_choice(self):
        self.contact_app.menu_choice()

    def build_display(self):
        self.contact_app.display()


class ContactAppDirector:
    def __init__(self, builder):
        self.builder = builder

    def construct(self):
        self.builder.build_menu_choice()
        self.builder.build_display()


class ContactApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.contact_user_interface = ContactUserInterface(self)
        self.__configure_window()

    def __configure_window(self):
        self.frame()
        self.title("Contact App")
        self.geometry('1375x750')
        self.resizable(True, False)
        self.configure(bg="green")

    def frame(self):
        pass

    def _add_entry_with_placeholder(self, placeholder, default_text):
        entry = PlaceholderEntry(self, placeholder, default_text, font=('Helvitica', 50))
        entry.pack(padx=10, pady=2)
        return entry

    def _add_button(self, text, foreground=None, command=None, state=None, font=None, width=None, bg=None, padx=None,
                    pady=None):
        frame = tk.Frame(self, bg="forest green")
        frame.pack(pady=0)

        button = tk.Button(frame, font=font, foreground=foreground, text=text, width=width, command=command,
                           padx=padx, bg=bg, pady=pady, state=state)
        button.pack()
        return button

    def _add_label(self, textvariable=None, text=None, font=None, bg=None, width=None, foreground=None, padx=None):
        label = tk.Label(self, textvariable=textvariable, text=text, bg=bg, width=width, padx=padx, font=font,
                         foreground=foreground)
        label.pack()
        return label

    def menu_choice(self):
        for widget in self.contact_user_interface.contact_app.winfo_children():
            widget.forget()
        self._add_label(text="Dialer Contact", font=('Helvetica', 40), bg='green', width=20).pack(side=tk.LEFT, padx=40)

        button_txt = ["Search", "Close"]
        for text in button_txt:
            new_button = self._add_button(text, foreground='white', font=("Helvetica", 30), width=40, bg='forest green')
            if text == "Search":
                new_button.config(command=self.contact_user_interface.contact_account_form)
            elif text == "Close":
                new_button.config(command=self.destroy)

            new_button.pack(side=tk.LEFT, pady=100, padx=80)

        self._add_button("About This", command=ShowMessage(
            'Practice Application\nBSCS 2-A\nFaborada Nathaniel\n John Paul Bodino '), foreground='white',
                         font=("Helvetica", 30), width=40, bg='forest green').pack(side=tk.LEFT, pady=60, padx=80)

    def display(self):
        self.mainloop()


class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="", default_text="", *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.default_text = default_text
        self.placeholder_shown = True
        self.bind("<FocusIn>", self.focus_in)
        self.bind("<FocusOut>", self.focus_out)
        self.show_placeholder()

    def focus_in(self, _):
        if self.placeholder_shown:
            self.delete("0", "end")
            self.placeholder_shown = False

    def focus_out(self, _):
        if not self.get():
            self.show_placeholder()

    def show_placeholder(self):
        self.insert("0", self.placeholder)
        self.placeholder_shown = True
        self.configure(fg="grey")


if __name__ == "__main__":
    builder = ContactAppBuilder()
    director = ContactAppDirector(builder)
    director.construct()

#Time complexity is Big O of m *  n 
#We create Contact Search because It can in daily life of a person  to search contact from phone
#Therefore the time complexity will be O(m*n) 
# m is the len_string1 then n is len_string2  
