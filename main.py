# main.py

import pyperclip
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from scraper import run_scraper
from uploader import run_uploader
from threading import Thread, Event
import threading
import os
import json
import tkinter as tk
from tkinter import messagebox
import sys
import json.decoder
import pandas as pd
import subprocess
import webbrowser

CONFIG_FILE = 'config.json'

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class RealEstateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESTAGE")
        self.root.geometry("800x700")

        try:
            self.root.iconbitmap(resource_path('logo.ico'))
        except Exception:
            pass

        self.login_frame = None
        self.main_frame = None

        self.user_config = self.load_or_create_config()

        self.all_ad_ids = self.get_all_ad_ids()

        self.thread_stop_event = Event()

        self.build_ui()

    def load_or_create_config(self):
        config_path = resource_path(CONFIG_FILE)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if 'email' in config and 'password' in config and 'name' in config:
                    return config
                else:
                    raise json.decoder.JSONDecodeError("Missing fields", "", 0)
            except json.decoder.JSONDecodeError:
                messagebox.showerror("Configuration Error", "config.json is corrupted or missing required fields. Please re-enter your credentials.")
                os.remove(config_path)
                return self.show_login_frame()
        else:
            return self.show_login_frame()

    def show_login_frame(self):
        if self.main_frame:
            self.main_frame.pack_forget()

        self.login_frame = ttk.Frame(self.root)
        self.login_frame.pack(expand=True, fill='both', pady=50)

        login_title = ttk.Label(self.login_frame, text="Please Log In", font=('Helvetica', 18, 'bold'))
        login_title.pack(pady=20)

        email_label = ttk.Label(self.login_frame, text="Email:")
        email_label.pack(pady=10, anchor='w')
        self.email_entry = ttk.Entry(self.login_frame, width=40)
        self.email_entry.pack(pady=5)

        password_label = ttk.Label(self.login_frame, text="Password:")
        password_label.pack(pady=10, anchor='w')
        self.password_entry = ttk.Entry(self.login_frame, width=40, show='*')
        self.password_entry.pack(pady=5)

        name_label = ttk.Label(self.login_frame, text="სახელი")
        name_label.pack(pady=10, anchor='w')
        self.name_entry = ttk.Entry(self.login_frame, width=40)
        self.name_entry.pack(pady=5)

        login_button = ttk.Button(self.login_frame, text="Login", command=self.handle_login, style='primary.TButton')
        login_button.pack(pady=20)

        return None

    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        name = self.name_entry.get().strip()

        if not email or not password:
            messagebox.showerror("Input Error", "Please enter both email and password.", parent=self.root)
            return

        config = {
            'email': email,
            'password': password,
            "name": name
        }
        try:
            with open(resource_path(CONFIG_FILE), 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to save configuration: {e}", parent=self.root)
            return

        self.user_config = config

        if self.login_frame:
            self.login_frame.pack_forget()
            self.login_frame.destroy()
            self.login_frame = None
        self.build_main_frame()

    def build_ui(self):
        if self.user_config:
            self.build_main_frame()
        else:
            pass

    def build_main_frame(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(expand=True, fill='both', pady=10)

        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill='x')

        header_label = ttk.Label(
            header_frame,
            text="ESTAGE",
            style='primary.TLabel',
            font=('Helvetica', 24, 'bold')
        )
        header_label.pack(pady=20, side='left')

        user_name = self.user_config.get('name', 'User')
        user_label = ttk.Label(
            header_frame,
            text=f"Logged in as: {user_name}",
            style='secondary.TLabel',
            font=('Helvetica', 14)
        )
        user_label.pack(pady=20, side='right')

        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(expand=True, fill='both', pady=10)

        self.scrape_upload_frame = ttk.Frame(self.notebook)
        self.scrape_only_frame = ttk.Frame(self.notebook)
        self.upload_existing_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.scrape_upload_frame, text='Scrape & Upload')
        self.notebook.add(self.scrape_only_frame, text='Scrape')
        self.notebook.add(self.upload_existing_frame, text='Upload Existing')

        self.url = ttk.StringVar()
        self.agency_price = ttk.StringVar()
        self.comment = ttk.StringVar()
        self.headless_var_scrape = ttk.BooleanVar(value=True)
        self.upload_description_var_scrape = ttk.BooleanVar(value=True)

        self.existing_ad_id = ttk.StringVar()
        self.headless_var_upload = ttk.BooleanVar(value=True)
        self.upload_description_var_upload = ttk.BooleanVar(value=True)
        self.upload_link = ttk.StringVar()

        self.build_scrape_upload_tab()
        self.build_scrape_only_tab()
        self.build_upload_existing_tab()

        change_user_button = ttk.Button(
            self.main_frame,
            text="Change User",
            command=self.change_user,
            style='danger.TButton'
        )
        change_user_button.pack(pady=10)

        open_excel_button = ttk.Button(
            header_frame,
            text="Open Excel",
            command=self.open_excel_file,
            style='info.TButton'
        )
        open_excel_button.pack(pady=20, side='right')

    def build_scrape_upload_tab(self):
        frame = self.scrape_upload_frame

        label_url = ttk.Label(frame, text="Enter URL:")
        label_url.pack(pady=5, anchor='w', padx=20)
        entry_url = ttk.Entry(frame, textvariable=self.url, width=60)
        entry_url.pack(pady=5, fill='x', padx=20)

        label_price = ttk.Label(frame, text="Agency Price:")
        label_price.pack(pady=5, anchor='w', padx=20)
        entry_price = ttk.Entry(frame, textvariable=self.agency_price, width=60)
        entry_price.pack(pady=5, fill='x', padx=20)

        label_comment = ttk.Label(frame, text="Comment:")
        label_comment.pack(pady=5, anchor='w', padx=20)
        entry_comment = ttk.Entry(frame, textvariable=self.comment, width=60)
        entry_comment.pack(pady=5, fill='x', padx=20)

        upload_desc_checkbox = ttk.Checkbutton(
            frame,
            text="Upload Description",
            variable=self.upload_description_var_scrape
        )
        upload_desc_checkbox.pack(pady=5, anchor='w', padx=20)

        checkbox_headless = ttk.Checkbutton(
            frame,
            text="Run in headless mode",
            variable=self.headless_var_scrape
        )
        checkbox_headless.pack(pady=5, anchor='w', padx=20)

        self.progress_scrape_upload = ttk.Progressbar(
            frame,
            mode='indeterminate'
        )
        self.progress_scrape_upload.pack(pady=5, fill='x', padx=20)
        self.progress_scrape_upload.pack_forget()

        self.run_button = ttk.Button(
            frame,
            text="Run",
            command=self.start_scrape_upload,
            style='success.TButton'
        )
        self.run_button.pack(pady=20)

        self.stop_button = ttk.Button(
            frame,
            text="Stop",
            command=self.stop_running_process,
            style='danger.TButton'
        )
        self.stop_button.pack(pady=5)
        self.stop_button.pack_forget()

    def build_scrape_only_tab(self):
        frame = self.scrape_only_frame

        label_url = ttk.Label(frame, text="Enter URL:")
        label_url.pack(pady=5, anchor='w', padx=20)
        entry_url = ttk.Entry(frame, textvariable=self.url, width=60)
        entry_url.pack(pady=5, fill='x', padx=20)

        label_price = ttk.Label(frame, text="Agency Price:")
        label_price.pack(pady=5, anchor='w', padx=20)
        entry_price = ttk.Entry(frame, textvariable=self.agency_price, width=60)
        entry_price.pack(pady=5, fill='x', padx=20)

        label_comment = ttk.Label(frame, text="Comment:")
        label_comment.pack(pady=5, anchor='w', padx=20)
        entry_comment = ttk.Entry(frame, textvariable=self.comment, width=60)
        entry_comment.pack(pady=5, fill='x', padx=20)

        checkbox_headless = ttk.Checkbutton(
            frame,
            text="Run in headless mode",
            variable=self.headless_var_scrape
        )
        checkbox_headless.pack(pady=5, anchor='w', padx=20)

        self.progress_scrape_only = ttk.Progressbar(
            frame,
            mode='indeterminate'
        )
        self.progress_scrape_only.pack(pady=5, fill='x', padx=20)
        self.progress_scrape_only.pack_forget()

        self.run_button_scrape_only = ttk.Button(
            frame,
            text="Scrape",
            command=self.start_scrape_only,
            style='success.TButton'
        )
        self.run_button_scrape_only.pack(pady=20)

        self.stop_button_scrape_only = ttk.Button(
            frame,
            text="Stop",
            command=self.stop_running_process,
            style='danger.TButton'
        )
        self.stop_button_scrape_only.pack(pady=5)
        self.stop_button_scrape_only.pack_forget()

    def build_upload_existing_tab(self):
        frame = self.upload_existing_frame

        label_ad_id = ttk.Label(frame, text="Enter Ad ID:")
        label_ad_id.pack(pady=5, anchor='w', padx=20)
        self.ad_id_entry = ttk.Entry(frame, textvariable=self.existing_ad_id, width=60)
        self.ad_id_entry.pack(pady=5, fill='x', padx=20)
        self.ad_id_entry.bind('<KeyRelease>', self.update_ad_id_autocomplete)

        self.ad_id_listbox = tk.Listbox(frame, height=5)
        self.ad_id_listbox.pack(pady=5, fill='x', padx=20)
        self.ad_id_listbox.bind('<<ListboxSelect>>', self.on_ad_id_select)
        self.ad_id_listbox.pack_forget()

        upload_desc_checkbox = ttk.Checkbutton(
            frame,
            text="Upload Description",
            variable=self.upload_description_var_upload
        )
        upload_desc_checkbox.pack(pady=5, anchor='w', padx=20)

        checkbox_headless = ttk.Checkbutton(
            frame,
            text="Run in headless mode",
            variable=self.headless_var_upload
        )
        checkbox_headless.pack(pady=5, anchor='w', padx=20)

        self.progress_upload_existing = ttk.Progressbar(
            frame,
            mode='indeterminate'
        )
        self.progress_upload_existing.pack(pady=5, fill='x', padx=20)
        self.progress_upload_existing.pack_forget()

        self.run_button_upload_existing = ttk.Button(
            frame,
            text="Upload",
            command=self.start_upload_existing,
            style='success.TButton'
        )
        self.run_button_upload_existing.pack(pady=20)

        self.stop_button_upload_existing = ttk.Button(
            frame,
            text="Stop",
            command=self.stop_running_process,
            style='danger.TButton'
        )
        self.stop_button_upload_existing.pack(pady=5)
        self.stop_button_upload_existing.pack_forget()

        self.final_url_label = ttk.Label(frame, textvariable=self.upload_link, foreground="blue", cursor="hand2", wraplength=700)
        self.final_url_label.pack(pady=10, padx=20)
        self.final_url_label.bind("<Button-1>", self.open_url)

        copy_button = ttk.Button(
            frame,
            text="Copy URL",
            command=self.copy_url,
            state='disabled',
            style='info.TButton'
        )
        copy_button.pack(pady=5)
        self.copy_button = copy_button

    def start_scrape_upload(self):
        if not self.validate_scrape_upload_inputs():
            return
        self.run_button.config(state='disabled')
        self.stop_button.pack(pady=5)
        threading.Thread(target=self.run_scrape_upload, daemon=True).start()

    def run_scrape_upload(self):
        try:
            self.progress_scrape_upload.pack(pady=5, fill='x', padx=20)
            self.progress_scrape_upload.start()

            headless = self.headless_var_scrape.get()
            upload_description = self.upload_description_var_scrape.get()
            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            ad_id = run_scraper(
                self.url.get(),
                self.agency_price.get(),
                comment=self.comment.get(),
                headless=headless,
                stop_event=self.thread_stop_event
            )
            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            if not ad_id:
                self.show_error("Scraping failed. Check the URL and try again.")
                return

            data_folder = os.path.join("data", ad_id)
            json_file_path = os.path.join(data_folder, f"{ad_id}.json")
            if not os.path.exists(json_file_path):
                self.show_error("Scraped data file not found.")
                return

            with open(json_file_path, "r", encoding='utf-8') as jf:
                scraped_data = json.load(jf)

            excel_data = {
                "Ad ID": scraped_data.get("ad_id", ""),
                "Ad Title": scraped_data.get("ad_title", ""),
                "Location": scraped_data.get("location", ""),
                "Number": scraped_data.get("number", ""),
                "Owner Price": scraped_data.get("owner_price", ""),
                "Agency Price": scraped_data.get("agency_price", ""),
                "Phone Number": scraped_data.get("phone_number", ""),
                "Name": scraped_data.get("name", ""),
                "Description": scraped_data.get("description", ""),
                "Comment": scraped_data.get("comment", ""),
                "Property Details": json.dumps(scraped_data.get("property_details", {}), ensure_ascii=False),
                "Additional Info": json.dumps(scraped_data.get("additional_info", {}), ensure_ascii=False),
                "Breadcrumbs": json.dumps(scraped_data.get("breadcrumbs", {}), ensure_ascii=False),
                "Features": json.dumps(scraped_data.get("features", {}), ensure_ascii=False),
                "Final URL": ""
            }

            excel_file = 'scraped_data.xlsx'
            if not os.path.exists(excel_file):
                df = pd.DataFrame([excel_data])
                df.to_excel(excel_file, index=False)
            else:
                df = pd.read_excel(excel_file)
                df = pd.concat([df, pd.DataFrame([excel_data])], ignore_index=True)
                df.to_excel(excel_file, index=False)

            user_info = self.user_config

            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            final_url = run_uploader(
                username=user_info['email'],
                password=user_info['password'],
                phone_number=scraped_data.get("phone_number", ""),
                ad_id=ad_id,
                enter_description=upload_description,
                headless=headless,
                stop_event=self.thread_stop_event
            )

            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            if final_url:
                self.show_info("Process completed successfully.")
                self.upload_link.set(f"Upload Successful!\nFinal URL: {final_url}")
                self.copy_button.config(state='normal')
            else:
                self.show_error("Upload failed. Please check the logs for more details.")

            self.all_ad_ids = self.get_all_ad_ids()
        except Exception as e:
            self.show_error(f"An error occurred: {e}")
        finally:
            self.progress_scrape_upload.stop()
            self.progress_scrape_upload.pack_forget()
            self.run_button.config(state='normal')
            self.stop_button.pack_forget()
            self.thread_stop_event.clear()

    def start_scrape_only(self):
        if not self.validate_scrape_upload_inputs():
            return
        self.run_button_scrape_only.config(state='disabled')
        self.stop_button_scrape_only.pack(pady=5)
        threading.Thread(target=self.run_scrape_only, daemon=True).start()

    def run_scrape_only(self):
        try:
            self.progress_scrape_only.pack(pady=5, fill='x', padx=20)
            self.progress_scrape_only.start()

            headless = self.headless_var_scrape.get()
            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            ad_id = run_scraper(
                self.url.get(),
                self.agency_price.get(),
                comment=self.comment.get(),
                headless=headless,
                stop_event=self.thread_stop_event
            )
            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            if not ad_id:
                self.show_error("Scraping failed. Check the URL and try again.")
                return

            data_folder = os.path.join("data", ad_id)
            json_file_path = os.path.join(data_folder, f"{ad_id}.json")
            if not os.path.exists(json_file_path):
                self.show_error("Scraped data file not found.")
                return

            with open(json_file_path, "r", encoding='utf-8') as jf:
                scraped_data = json.load(jf)

            excel_data = {
                "Ad ID": scraped_data.get("ad_id", ""),
                "Ad Title": scraped_data.get("ad_title", ""),
                "Location": scraped_data.get("location", ""),
                "Number": scraped_data.get("number", ""),
                "Owner Price": scraped_data.get("owner_price", ""),
                "Agency Price": scraped_data.get("agency_price", ""),
                "Phone Number": scraped_data.get("phone_number", ""),
                "Name": scraped_data.get("name", ""),
                "Description": scraped_data.get("description", ""),
                "Comment": scraped_data.get("comment", ""),
                "Property Details": json.dumps(scraped_data.get("property_details", {}), ensure_ascii=False),
                "Additional Info": json.dumps(scraped_data.get("additional_info", {}), ensure_ascii=False),
                "Breadcrumbs": json.dumps(scraped_data.get("breadcrumbs", {}), ensure_ascii=False),
                "Features": json.dumps(scraped_data.get("features", {}), ensure_ascii=False),
                "Final URL": ""
            }

            excel_file = 'scraped_data.xlsx'
            if not os.path.exists(excel_file):
                df = pd.DataFrame([excel_data])
                df.to_excel(excel_file, index=False)
            else:
                df = pd.read_excel(excel_file)
                df = pd.concat([df, pd.DataFrame([excel_data])], ignore_index=True)
                df.to_excel(excel_file, index=False)

            self.show_info("Scraping completed successfully and data saved to Excel.")
        except Exception as e:
            self.show_error(f"An error occurred: {e}")
        finally:
            self.progress_scrape_only.stop()
            self.progress_scrape_only.pack_forget()
            self.run_button_scrape_only.config(state='normal')
            self.stop_button_scrape_only.pack_forget()
            self.thread_stop_event.clear()

    def start_upload_existing(self):
        if not self.validate_upload_existing_inputs():
            return
        self.run_button_upload_existing.config(state='disabled')
        self.stop_button_upload_existing.pack(pady=5)
        ad_id = self.existing_ad_id.get()
        threading.Thread(target=self.run_upload_existing, args=(ad_id,), daemon=True).start()

    def run_upload_existing(self, ad_id):
        try:
            self.progress_upload_existing.pack(pady=5, fill='x', padx=20)
            self.progress_upload_existing.start()

            headless = self.headless_var_upload.get()
            upload_description = self.upload_description_var_upload.get()
            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            with open(os.path.join("data", ad_id, f"{ad_id}.json"), 'r', encoding='utf-8') as jf:
                scraped_data = json.load(jf)
            user_info = self.user_config

            final_url = run_uploader(
                username=user_info['email'],
                password=user_info['password'],
                phone_number=scraped_data.get("phone_number", ""),
                ad_id=ad_id,
                enter_description=upload_description,
                headless=headless,
                stop_event=self.thread_stop_event
            )

            if self.thread_stop_event.is_set():
                self.show_info("Process was stopped.")
                return

            if final_url:
                self.upload_link.set(f"Upload Successful!\nFinal URL: {final_url}")
                self.copy_button.config(state='normal')
                self.show_info("Upload completed successfully.")
            else:
                self.show_error("Upload failed. Please check the logs for more details.")
        except Exception as e:
            self.show_error(f"An error occurred: {e}")
        finally:
            self.progress_upload_existing.stop()
            self.progress_upload_existing.pack_forget()
            self.run_button_upload_existing.config(state='normal')
            self.stop_button_upload_existing.pack_forget()
            self.thread_stop_event.clear()

    def validate_scrape_upload_inputs(self):
        if not self.url.get() or not self.agency_price.get():
            messagebox.showerror("Input Error", "Please enter both URL and agency price.")
            return False
        return True

    def validate_upload_existing_inputs(self):
        if not self.existing_ad_id.get():
            messagebox.showerror("Input Error", "Please enter an Ad ID.")
            return False
        return True

    def update_ad_id_autocomplete(self, event):
        typed = self.existing_ad_id.get()
        data = []
        if typed == '':
            data = self.all_ad_ids
        else:
            data = [ad_id for ad_id in self.all_ad_ids if typed.lower() in ad_id.lower()]
        if data:
            self.update_ad_id_listbox(data)
            self.ad_id_listbox.pack(pady=5, fill='x', padx=20)
        else:
            self.ad_id_listbox.pack_forget()

    def update_ad_id_listbox(self, data):
        self.ad_id_listbox.delete(0, tk.END)
        for item in data:
            self.ad_id_listbox.insert(tk.END, item)

    def on_ad_id_select(self, event):
        selected_indices = self.ad_id_listbox.curselection()
        if selected_indices:
            index = selected_indices[0]
            selected_ad_id = self.ad_id_listbox.get(index)
            self.existing_ad_id.set(selected_ad_id)
            self.ad_id_listbox.pack_forget()

    def get_all_ad_ids(self):
        data_folder = resource_path('data')
        if not os.path.exists(data_folder):
            return []
        return [name for name in os.listdir(data_folder) if os.path.isdir(os.path.join(data_folder, name))]

    def change_user(self):
        confirm = messagebox.askyesno("Change User", "Are you sure you want to change the user?")
        if confirm:
            config_path = resource_path(CONFIG_FILE)
            if os.path.exists(config_path):
                try:
                    os.remove(config_path)
                except Exception as e:
                    messagebox.showerror("File Error", f"Failed to delete config.json: {e}")
                    return
            if self.main_frame:
                self.main_frame.pack_forget()
                self.main_frame.destroy()
                self.main_frame = None
            self.show_login_frame()

    def show_error(self, message):
        self.root.after(0, lambda: messagebox.showerror("Error", message))

    def show_info(self, message):
        self.root.after(0, lambda: messagebox.showinfo("Success", message))

    def open_url(self, event):
        url = self.upload_link.get().split("Final URL: ")[-1]
        if url:
            webbrowser.open(url)

    def copy_url(self):
        url = self.upload_link.get().split("Final URL: ")[-1]
        if url:
            pyperclip.copy(url)
            messagebox.showinfo("Copied", "URL has been copied to clipboard.")

    def open_excel_file(self):
        excel_file = 'scraped_data.xlsx'
        excel_path = resource_path(excel_file)
        if not os.path.exists(excel_path):
            self.show_error("Excel file does not exist.")
            return
        try:
            if sys.platform.startswith('darwin'):
                subprocess.call(('open', excel_path))
            elif os.name == 'nt':
                os.startfile(excel_path)
            elif os.name == 'posix':
                subprocess.call(('xdg-open', excel_path))
        except Exception as e:
            self.show_error(f"Failed to open Excel file: {e}")

    def stop_running_process(self):
        self.thread_stop_event.set()

if __name__ == "__main__":
    app = ttk.Window(themename="flatly")
    RealEstateApp(app)
    app.mainloop()
