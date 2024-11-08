# main.py

import tkinter as tk
from tkinter import messagebox, ttk
from scraper import run_scraper
from uploader import run_uploader
import threading
import os
import json

# Path to the users.json file
USERS_FILE = 'users.json'

class RealEstateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESTAGE UPLOADER")
        self.root.geometry("600x600")
        self.root.configure(bg='#f0f0f0')

        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 12))
        self.style.configure('TButton', font=('Arial', 12))
        self.style.configure('TEntry', font=('Arial', 12))
        self.style.configure('TCombobox', font=('Arial', 12))
        self.style.configure('Header.TLabel', font=('Arial', 18, 'bold'))

        # Load users from JSON
        self.users = self.load_users()

        # Header label
        self.header_label = ttk.Label(root, text="ESTAGE UPLOADER", style='Header.TLabel')
        self.header_label.pack(pady=10)

        # Notebook (Tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')

        # Tab frames
        self.scrape_upload_frame = ttk.Frame(self.notebook)
        self.upload_existing_frame = ttk.Frame(self.notebook)
        self.user_management_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scrape_upload_frame, text='Scrape & Upload')
        self.notebook.add(self.upload_existing_frame, text='Upload Existing')
        self.notebook.add(self.user_management_frame, text='User Management')

        # Initialize variables
        self.selected_user = tk.StringVar()
        self.url = tk.StringVar()
        self.agency_price = tk.StringVar()
        self.ad_id = ''
        self.headless_var = tk.BooleanVar()
        self.existing_ad_id = tk.StringVar()

        # Build the tabs
        self.build_scrape_upload_tab()
        self.build_upload_existing_tab()
        self.build_user_management_tab()

    def load_users(self):
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        else:
            return {}

    def save_users(self):
        with open(USERS_FILE, 'w') as f:
            json.dump(self.users, f, indent=4)

    def build_scrape_upload_tab(self):
        frame = self.scrape_upload_frame

        # User selection
        label_user = ttk.Label(frame, text="Select User:")
        label_user.pack(pady=5)
        self.user_combobox = ttk.Combobox(frame, values=list(self.users.keys()), state="readonly", textvariable=self.selected_user)
        self.user_combobox.pack(pady=5)

        # URL input
        label_url = ttk.Label(frame, text="Enter URL:")
        label_url.pack(pady=5)
        entry_url = ttk.Entry(frame, textvariable=self.url, width=50)
        entry_url.pack(pady=5)

        # Agency Price input
        label_price = ttk.Label(frame, text="Agency Price:")
        label_price.pack(pady=5)
        entry_price = ttk.Entry(frame, textvariable=self.agency_price, width=20)
        entry_price.pack(pady=5)

        # Headless mode checkbox
        checkbox_headless = ttk.Checkbutton(frame, text="Run in headless mode", variable=self.headless_var)
        checkbox_headless.pack(pady=5)

        # Run button
        run_button = ttk.Button(frame, text="Run", command=self.start_scrape_upload)
        run_button.pack(pady=20)

    def build_upload_existing_tab(self):
        frame = self.upload_existing_frame

        # User selection
        label_user = ttk.Label(frame, text="Select User:")
        label_user.pack(pady=5)
        self.user_combobox_existing = ttk.Combobox(frame, values=list(self.users.keys()), state="readonly", textvariable=self.selected_user)
        self.user_combobox_existing.pack(pady=5)

        # Ad ID selection with Combobox
        label_ad_id = ttk.Label(frame, text="Select Ad ID:")
        label_ad_id.pack(pady=5)
        self.ad_id_combobox = ttk.Combobox(frame, textvariable=self.existing_ad_id, state="readonly")
        self.ad_id_combobox.pack(pady=5)
        self.populate_ad_id_combobox()

        # Headless mode checkbox
        checkbox_headless = ttk.Checkbutton(frame, text="Run in headless mode", variable=self.headless_var)
        checkbox_headless.pack(pady=5)

        # Run button
        run_button = ttk.Button(frame, text="Upload", command=self.start_upload_existing)
        run_button.pack(pady=20)

    def build_user_management_tab(self):
        frame = self.user_management_frame

        # Add User Section
        add_user_label = ttk.Label(frame, text="Add New User", font=('Arial', 14, 'bold'))
        add_user_label.pack(pady=10)

        # New user details
        self.new_user_key = tk.StringVar()
        self.new_username = tk.StringVar()
        self.new_password = tk.StringVar()
        self.new_phone_number = tk.StringVar()

        label_user_key = ttk.Label(frame, text="User Key:")
        label_user_key.pack(pady=5)
        entry_user_key = ttk.Entry(frame, textvariable=self.new_user_key)
        entry_user_key.pack(pady=5)

        label_username = ttk.Label(frame, text="Username:")
        label_username.pack(pady=5)
        entry_username = ttk.Entry(frame, textvariable=self.new_username)
        entry_username.pack(pady=5)

        label_password = ttk.Label(frame, text="Password:")
        label_password.pack(pady=5)
        entry_password = ttk.Entry(frame, textvariable=self.new_password, show='*')
        entry_password.pack(pady=5)

        label_phone_number = ttk.Label(frame, text="Phone Number:")
        label_phone_number.pack(pady=5)
        entry_phone_number = ttk.Entry(frame, textvariable=self.new_phone_number)
        entry_phone_number.pack(pady=5)

        # Add User Button
        add_user_button = ttk.Button(frame, text="Add User", command=self.add_user)
        add_user_button.pack(pady=10)

        # Separator
        separator = ttk.Separator(frame, orient='horizontal')
        separator.pack(fill='x', pady=20)

        # Delete User Section
        delete_user_label = ttk.Label(frame, text="Delete User", font=('Arial', 14, 'bold'))
        delete_user_label.pack(pady=10)

        # User selection for deletion
        label_select_user = ttk.Label(frame, text="Select User to Delete:")
        label_select_user.pack(pady=5)
        self.delete_user_combobox = ttk.Combobox(frame, values=list(self.users.keys()), state="readonly")
        self.delete_user_combobox.pack(pady=5)

        # Delete User Button
        delete_user_button = ttk.Button(frame, text="Delete User", command=self.delete_user)
        delete_user_button.pack(pady=10)

    def start_scrape_upload(self):
        if not self.validate_user_selection():
            return
        if not self.url.get() or not self.agency_price.get():
            messagebox.showerror("Input Error", "Please enter both URL and agency price.")
            return
        threading.Thread(target=self.run_scrape_upload).start()

    def run_scrape_upload(self):
        try:
            headless = self.headless_var.get()
            # Run the scraper
            self.ad_id = run_scraper(self.url.get(), self.agency_price.get(), headless=headless)
            if not self.ad_id:
                messagebox.showerror("Error", "Scraping failed. Check the URL and try again.")
                return
            # After scraping, run the uploader
            user_info = self.users[self.selected_user.get()]
            run_uploader(
                username=user_info['username'],
                password=user_info['password'],
                phone_number=user_info['phone_number'],
                ad_id=self.ad_id,
                enter_description=True,
                headless=headless
            )
            messagebox.showinfo("Success", "Process completed successfully.")
            # Refresh the ad ID combobox in case a new ad ID was added
            self.populate_ad_id_combobox()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def start_upload_existing(self):
        if not self.validate_user_selection():
            return
        ad_id = self.existing_ad_id.get()
        if not ad_id:
            messagebox.showerror("Input Error", "Please select an Ad ID.")
            return
        threading.Thread(target=self.run_upload_existing, args=(ad_id,)).start()

    def run_upload_existing(self, ad_id):
        try:
            headless = self.headless_var.get()
            # Run the uploader
            user_info = self.users[self.selected_user.get()]
            run_uploader(
                username=user_info['username'],
                password=user_info['password'],
                phone_number=user_info['phone_number'],
                ad_id=ad_id,
                enter_description=True,
                headless=headless
            )
            messagebox.showinfo("Success", "Upload completed successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def validate_user_selection(self):
        if not self.selected_user.get():
            messagebox.showerror("User Selection", "Please select a user.")
            return False
        return True

    def populate_ad_id_combobox(self):
        ad_ids = self.get_all_ad_ids()
        self.ad_id_combobox['values'] = ad_ids

    def get_all_ad_ids(self):
        data_folder = 'data'
        if not os.path.exists(data_folder):
            return []
        return [name for name in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, name))]

    def add_user(self):
        user_key = self.new_user_key.get().strip()
        username = self.new_username.get().strip()
        password = self.new_password.get().strip()
        phone_number = self.new_phone_number.get().strip()

        if not user_key or not username or not password or not phone_number:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        if user_key in self.users:
            messagebox.showerror("Error", "User key already exists.")
            return

        self.users[user_key] = {
            'username': username,
            'password': password,
            'phone_number': phone_number
        }
        self.save_users()
        messagebox.showinfo("Success", "User added successfully.")
        self.update_user_comboboxes()
        # Clear input fields
        self.new_user_key.set('')
        self.new_username.set('')
        self.new_password.set('')
        self.new_phone_number.set('')

    def delete_user(self):
        user_key = self.delete_user_combobox.get()
        if not user_key:
            messagebox.showerror("Input Error", "Please select a user to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete user '{user_key}'?")
        if confirm:
            del self.users[user_key]
            self.save_users()
            messagebox.showinfo("Success", "User deleted successfully.")
            self.update_user_comboboxes()

    def update_user_comboboxes(self):
        # Update user selection comboboxes in all tabs
        user_keys = list(self.users.keys())
        self.user_combobox['values'] = user_keys
        self.user_combobox_existing['values'] = user_keys
        self.delete_user_combobox['values'] = user_keys

# Initialize and run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = RealEstateApp(root)
    root.mainloop()
