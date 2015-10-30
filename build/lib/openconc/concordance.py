import tkinter as tk
from tkinter import ttk
import os
import re
from openconc import misc


def conc_worker():
    pass


def worker_search_files():
    pass


def search_in_file(f, o):
    handler = open(f, "r")
    f_text = handler.read()
    conc = []
    if bool(o['IgnorePOSTags']) == True:
        pos_delim = o['POSTagDelimiter']
        pos_tag = "[A-Z]{2,}[A-Z$0-9+*]*?"
        tag_str = "{0}{1}".format(pos_delim, pos_tag)
        f_text = re.sub(r"{0}\s".format(tag_str), r"", f_text)
    if bool(o['IgnoreXMLTags']) == True:
        f_text = re.sub(r"<[^>]+>", r"", f_text)
        f_text = re.sub(r"&lt;[^&]+&gt;", r"", f_text)
    handler.close()
    matches = re.finditer(o['RegExPattern'], f_text)
    if matches:
        for m in matches:
            s = m.start()
            e = m.end()
            c = {}
            c['Key'] = m.group(0)
            if o['ContextUnit'] == "Characters":
                c['Right'] = f_text[e:e + int(o['ContextRight'])]
                c['Right'] = c['Right'].replace(
                    "\n", " ").replace("\t", " ").strip()
                c['Right'] = re.sub("\s+", " ", c['Right'])
                c['Left'] = f_text[s - int(o['ContextLeft']):s]
                c['Left'] = c['Left'].replace(
                    "\n", " ").replace("\t", " ").strip()
                c['Left'] = re.sub("\s+", " ", c['Left'])
            else:
                # assume that each word = 30 characters long , to be reasonably
                # safe
                l_char = int(o['ContextLeft']) * 20
                r_char = int(o['ContextRight']) * 20
                c['Right'] = misc.tokenize_str(f_text[e:e + r_char],
                                                   o['WordCharsRegex'])
                c['Left'] = misc.tokenize_str(f_text[s - l_char:s],
                                                  o['WordCharsRegex'])
                c['Left'] = " ".join(c['Left'][-int(o['ContextRight']):])
                c['Right'] = " ".join(c['Right'][0:int(o['ContextRight'])])

            c['Filename'] = os.path.basename(f)
            conc.append(c)
    return conc


def get_concordance_from_files(files, o):
    if bool(o['CaseSensitive']) == True:
        flags = re.UNICODE | re.IGNORECASE
    else:
        flags = re.UNICODE
    if bool(o['IsRegEx']):
        conc = []
    for f in files:
        conc += search_in_file(f, o)
    return conc


class ConcordanceFrame(tk.Frame):

    def __init__(self, parent,  *args, **kwargs):
        tk.Frame.__init__(self)
        self.parent = parent
        self.draw_ui()
        self.load_recent_searches()

    def yview(self, *args):
        self.index_text.yview(*args)
        self.line_text.yview(*args)
        for key, m_text in self.meta_text.items():
            m_text.yview(*args)

    def draw_ui(self):
        settings = self.parent.settings_frame  # just for shorter refs
        self.book = ttk.Notebook(self)
        self.book.grid(column=0, row=0, sticky="news")
        self.rowconfigure(0, weight=1)  # conc tabs
        self.rowconfigure(1, weight=1)  # search frame
        # SEARCH frame
        self.search_frame = ttk.Frame(self)
        self.search_frame.grid(row=1, column=0, sticky="news")
        self.search_frame.rowconfigure(0, weight=1)
        self.search_frame.rowconfigure(1, weight=1)
        self.search_frame.columnconfigure(8, weight=1)
        # row 0
        tk.Label(self.search_frame, text="Search text", font="verdana 12").grid(column=0, row=0,
                                                                                sticky="nw")
        self.search_var = tk.StringVar()
        self.search_combo = ttk.Combobox(self.search_frame, textvariable=self.search_var,
                                         style="Search.TCombobox")
        self.search_combo.grid(row=0, column=1, sticky="news", columnspan=10)
        # row 1
        tk.Label(self.search_frame, text="Context left", font="verdana 10").grid(column=0, row=1,
                                                                                 sticky="nw")
        tk.Label(self.search_frame, text="Context right", font="verdana 10").grid(column=2, row=1,
                                                                                  sticky="nw")
        tk.Label(self.search_frame, text="Unit", font="verdana 10").grid(column=4, row=1,
                                                                         sticky="nw")
        self.left_entry = ttk.Entry(self.search_frame, width=5,
                                    textvariable=settings.concordance['ContextLeft'])
        self.right_entry = ttk.Entry(self.search_frame, width=5,
                                     textvariable=settings.concordance['ContextRight'])
        self.left_entry.grid(row=1, column=1, sticky="news")
        self.right_entry.grid(row=1, column=3, sticky="news")
        self.unit_combo = ttk.Combobox(self.search_frame,
                                       textvariable=settings.concordance[
                                           'ContextUnit'],
                                       values=["Characters", "Words"], state="readonly")
        self.unit_combo["width"] = 8
        self.unit_combo.grid(row=1, column=5, sticky="news")

        self.case_check = ttk.Checkbutton(
            self.search_frame, text="Case sensitive", variable=settings.concordance['Case'])
        self.case_check.grid(row=1, column=6)

        self.regex_check = ttk.Checkbutton(
            self.search_frame, text="Regular expression", variable=settings.concordance['IsRegEx'])
        self.regex_check.grid(row=1, column=7)

        # ALL tab
        self.all_frame = ttk.Frame(self)
        self.book.add(self.all_frame, text="All corpora")
        # row 0 RESULTS
        self.results_frame = ttk.Frame(self.all_frame)
        self.results_frame.grid(row=0, column=0, sticky="news")
        self.ybar = ttk.Scrollbar(self.results_frame, command=self.yview)
        self.ybar.grid(row=0, column=2, sticky="news")
        self.line_xbar = ttk.Scrollbar(self.results_frame, orient="horizontal")
        self.line_xbar.grid(row=1, column=1, sticky="news")
        self.line_text = tk.Text(self.results_frame, wrap="none", height=30,
                                 yscrollcommand=self.ybar.set,
                                 xscrollcommand=self.line_xbar.set, width=100)
        self.line_text.grid(row=0, column=1, sticky="nesw")
        self.line_xbar.config(command=self.line_text.xview)
        self.index_text = tk.Text(self.results_frame, width=8, yscrollcommand=self.ybar.set,
                                  height=30)
        self.index_text.grid(row=0, column=0, sticky="news")

        self.meta_xbar = ttk.Scrollbar(self.results_frame, orient="horizontal")
        self.meta_xbar.grid(row=1, column=3, sticky="news")
        self.meta_canvas = tk.Canvas(self.results_frame, background="white",
                                     xscrollcommand=self.meta_xbar.set)
        self.meta_canvas.grid(row=0, column=3, sticky="news")
        self.meta_xbar.config(command=self.meta_canvas.xview)
        self.meta_canvas_frame = tk.Frame(self.meta_canvas)
        # by default corpus name and filename, eventually more with XML corpora
        # if attributes provided
        self.meta_text = {}
        self.meta_text["corpus"] = tk.Text(
            self.meta_canvas_frame, wrap="none", width=20, height=30)
        self.meta_text["file"] = tk.Text(
            self.meta_canvas_frame, wrap="none", width=20, height=30)
        self.parent.root.update_idletasks()
        x2 = self.meta_canvas_frame.winfo_reqwidth()
        self.meta_canvas.create_window(
            0, 0, anchor="nw", window=self.meta_canvas_frame)
        self.meta_canvas.config(scrollregion=(0, 0, x2, 0))
        # row 1 BUTTONS
        self.button_frame = ttk.Frame(self.all_frame)
        self.button_frame.columnconfigure(0, weight=0)
        self.button_frame.columnconfigure(1, weight=0)
        self.button_frame.columnconfigure(5, weight=1)

        self.button_frame.grid(row=1, column=0, sticky="news")
        self.start_button = ttk.Button(
            self.button_frame, text="Search all corpora", command=self.create_concordance)
        self.start_button.grid(row=1, column=0, sticky="news", columnspan=3)
        self.export_button = ttk.Button(self.button_frame, text="Export concordance",
                                        command=self.export_concordance, state="disabled",
                                        style="Small.TButton")
        self.export_button.grid(row=1, column=3, sticky="news")
        self.sort_button = ttk.Button(self.button_frame, text="Sort by",
                                      command=self.sort_concordance, state="disabled",
                                      style="Small.TButton")
        self.sort_button.grid(row=0, column=0, sticky="news")
        self.sort_combo = []
        self.sort_var = []

        for i in range(0, 3):
            self.sort_var.append(tk.StringVar())
            cb = ttk.Combobox(self.button_frame, textvariable=self.sort_var[i],
                              values=[
                                  "Left", "Key", "Right", "Corpus", "Filename"],
                              state="readonly", style="Small.TCombobox")
            cb.grid(row=0, column=i + 1, sticky="news")
            self.sort_combo.append(cb)
        self.sort_var[0].set("Key")
        self.sort_var[1].set("Right")
        self.sort_var[2].set("Corpus")

        self.filter_var = tk.StringVar()
        tk.Label(self.button_frame, text="Filter text", font="verdana 9").grid(column=4, row=0,
                                                                               sticky="news")
        self.filter_entry = ttk.Entry(self.button_frame, textvariable=self.filter_var,
                                      style="Small.TEntry", state="disabled")
        self.filter_entry.grid(row=0, column=5, sticky="news")
        self.filter_button = ttk.Button(self.button_frame, text="Filter results",
                                        command=self.filter_concordance,
                                        style="Small.TButton",
                                        state="disabled")
        self.filter_button.grid(row=1, column=4, columnspan=2, sticky="news")

        misc.pad_children(self.search_frame, 5, 5)
        misc.pad_children(self.button_frame, 5, 5)

    def filter_concordance(self):
        pass

    def sort_concordance(self):
        pass

    def create_concordance(self):
        pass

    def export_concordance(self):
        pass

    def load_recent_searches(self):
        store_path = os.path.join(self.parent.user_dir, "searches.log")
        try:
            with open(store_path, "r") as handler:
                searches = handler.read()
            searches = searches.split("\n")
            self.search_combo["values"] = searches
        except IOError:
            pass

    def store_recent_searches(self):
        search_terms = "\n".join(self.search_combo["values"])
        store_path = os.path.join(self.parent.user_dir, "searches.log")
        try:
            with open(store_path, "w") as handler:
                handler.write(search_terms)
                handler.close()
        except IOError:
            pass
