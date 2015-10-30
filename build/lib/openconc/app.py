#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from openconc.settings import SettingsFrame
from openconc.concordance import ConcordanceFrame
from openconc.files import FileFrame
from openconc import misc
import os


class OpenConc(tk.Frame):

    def __init__(self, root):
        tk.Frame.__init__(self)
        self.root = root
        self.MAX_CORPORA = 10
        # init vars
        self.base_dir = os.path.dirname(os.path.realpath(__file__))
        self.user_dir = os.path.join(self.base_dir, "user_data")
        misc.make_dir(self.user_dir)
        self.corpus = []
        # draw ui
        self.draw_main_ui()
        self.file_frame.add_corpus()
        # binding
        self.root.wm_protocol("WM_DELETE_WINDOW", self.on_exit)
        # run
        self.root.mainloop()

    def on_exit(self):
        self.concordance_frame.store_recent_searches()
        self.root.destroy()

    def set_status(self, update_text, add_timestamp=False):
        if not add_timestamp:
            self.status_bar_text.set(update_text)
        else:
            ts = datetime.now().time().isoformat()
            update_text = "{0} ({1})".format(update_text, ts)
            self.status_bar_text.set(update_text)

    def book_tab_change(self, event):
        tab_index = self.book.index(self.book.select())

    def style_ui(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        style.configure('TFrame', relief="flat")
        style.configure('TButton', background='white', bordercolor="black", borderwidth=1,
                        relief="groove", font='verdana 10', padx="3", pady="3")
        style.configure('Small.TButton', background='white', bordercolor="black", borderwidth=1,
                        relief="groove", font='verdana 9', padx="3", pady="3")
        style.configure('TLabel', font='verdana 10', padx=3, pady=3)
        style.configure('TRadiobuttonsel', relief="flat", font='verdana 10', padx=3, pady=3)
        style.configure('TCheckbutton', relief="flat", font='verdana 10', padx=3, pady=3)
        style.configure('TNotebook', relief="flat", font='verdana 10', padx=3, pady=3)
        style.configure('TNotebook.Tab', relief="flat", font='verdana 10')
        style.configure('TLabel', relief="flat", font='verdana 10', padx=3, pady=3)
        style.configure('TListbox', background='white', relief="flat", font='verdana 10', padx=3,
                        pady=3)
        style.configure('TCombobox', background='white', fieldbackground="white", relief="flat",
                        font='verdana 10', padx=5, pady=5)
        style.configure('Small.TCombobox', background='white', fieldbackground="white",
                        relief="flat", font='verdana 9', padx=5, pady=5)
        style.configure('Search.TCombobox', background='white', fieldbackground="white",
                        relief="flat", font='verdana 12', padx=5, pady=5)
        style.configure('TScrollbar', troughcolor='white', relief="flat", background="white")
        style.configure("StatusLabel.TLabel", font="verdana 10")
        style.configure("TEntry", background="white", font="verdana 10")
        style.configure("Small.TEntry", background="white", font="verdana 9")

    def draw_main_ui(self):
        self.root.title("openConc - a tool for corpus linguists")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="news")
        self.maximize()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.style_ui()
        # --- status bar --- #
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self, textvariable=self.status_var, style="StatusLabel.TLabel")
        self.status_bar.grid(column=0, row=1, sticky="nesw")
        # --- main notebook --- #
        self.book = ttk.Notebook(self)
        self.book.grid(column=0, row=0, sticky="news")
        self.book.bind('<<NotebookTabChanged>>', self.book_tab_change)
        # --- settings --- #
        self.settings_frame = SettingsFrame(self)
        # corpus selection
        self.file_frame = FileFrame(self)
        # --- concordance --- #
        self.concordance_frame = ConcordanceFrame(self)
        misc.pad_children(self, 5, 5)
        # --- add to main book --- #
        self.book.add(self.file_frame, text="Files")
        self.book.add(self.concordance_frame, text="Concordance")
        self.book.add(self.settings_frame, text="Settings")

    def maximize(self):
        toplevel = self.root.winfo_toplevel()
        try:  # Windows
            toplevel.wm_state('zoomed')
        except:  # Linux
            w = self.root.winfo_screenwidth()
            h = self.root.winfo_screenheight() - 60
            geom_string = "%dx%d+0+0" % (w, h)
            toplevel.wm_geometry(geom_string)


