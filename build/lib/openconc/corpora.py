import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import colorchooser
import multiprocessing as mp
import os
from openconc import misc
from openconc.concordance import worker_search_files, conc_worker


class Corpus(tk.Frame):

    def __init__(self, parent, n, color="lightgray", *args, **kwargs):
        self.parent = parent
        self.n = n
        self.color = color

        self.concordance = []  # to store current concordance results for this corpus
        self.word_list = []  # for word frequency list results
        self.files = []

        self.name_var = tk.StringVar()
        self.name_var.set("Corpus {}".format(n+1))
        self.name_var.trace('w', lambda a, b, c: self.on_name_var_changed())
        self.set_styles()

    def __del__(self):
        self.remove()

    def set_styles(self):
        self.button_style = "C{}.TButton".format(self.n)
        self.tab_style = "C{}.TNotebook.Tab".format(self.n)
        style = ttk.Style()
        style.configure(self.button_style, background=self.color)
        style.configure(self.tab_style, background=self.color)

    def on_name_var_changed(self):
        name = self.name_var.get()
        self.parent.file_frame.listbox.delete(self.n)
        self.parent.file_frame.listbox.insert(self.n, name)
        self.parent.concordance_frame.book.tab(self.n+1, text=name)  # 0 = "All corpora"

    def on_name_entry_leave(self, event=None):
        name = self.name_var.get()
        if not name:
            name = "Corpus {}".format(self.n+1)
            self.name_var.set(name)

    def draw_setup_ui(self):
        parent = self.parent.file_frame.corpora_frame
        self.setup_frame = ttk.Frame(parent)
        self.setup_frame.rowconfigure(0, weight=0)
        self.setup_frame.rowconfigure(2, weight=1)
        self.setup_frame.columnconfigure(0, weight=0)
        self.setup_frame.grid(row=0, column=1, sticky="news")
        # row 0
        self.open_button = ttk.Button(self.setup_frame, style=self.button_style, text="Add files",
                                      command=self.add_files)
        self.clear_button = ttk.Button(self.setup_frame, style=self.button_style,
                                       text="Clear files", command=self.clear_files)
        self.color_button = ttk.Button(self.setup_frame, style=self.button_style,
                                       text="Change color", command=self.choose_color)
        self.open_button.grid(row=0, column=0, sticky="new")
        self.clear_button.grid(row=0, column=1, sticky="new")
        self.color_button.grid(row=0, column=2, sticky="new")
        # row 1
        name_label = ttk.Label(self.setup_frame, text="Corpus name", font="verdana 12")
        self.name_entry = ttk.Entry(self.setup_frame, textvariable=self.name_var,
                                    font="verdana 12")
        name_label.grid(column=0, row=1, sticky="nws")
        self.name_entry.grid(row=1, column=1, columnspan=2, sticky="news")
        self.name_entry.bind('<Leave>', self.on_name_entry_leave)
        # row 3
        self.remove_button = ttk.Button(self.setup_frame, style=self.button_style,
                                        text="Remove this corpus", command=self.remove)
        self.remove_button.grid(row=3, column=2, sticky="ne")
        # default padding
        misc.pad_children(self.setup_frame, 5, 5)
        # row 2 / no padding
        self.listbox = tk.Listbox(self.setup_frame)
        self.listbox.grid(row=2, column=0, columnspan=3, sticky="news")
        self.scrollbar = ttk.Scrollbar(self.setup_frame, command=self.listbox.yview)
        self.scrollbar.grid(row=2, column=4, sticky="ns")
        self.listbox["yscrollcommand"] = self.scrollbar.set

    def draw_conc_ui(self):
        parent = self.parent.concordance_frame
        self.button_style = "C{}.TButton".format(self.n)
        self.conc_frame = ttk.Frame(parent)
        parent.book.add(self.conc_frame, text=self.name_var.get())
        # row 0
        self.conc_results_frame = ttk.Frame(self.conc_frame)
        self.conc_results_frame.grid(row=0, column=0, sticky="news")
        # row 1
        self.conc_button_frame = ttk.Frame(self.conc_frame)
        self.conc_button_frame.grid(row=1, column=0, sticky="news")

        self.conc_results_frame = ttk.Frame(self.conc_frame)
        self.conc_results_frame.grid(row=0, column=0, sticky="news")
        self.conc_ybar = ttk.Scrollbar(self.conc_results_frame, command=self.concordance_yview)
        self.conc_ybar.grid(row=0, column=2, sticky="news")
        self.conc_line_xbar = ttk.Scrollbar(self.conc_results_frame, orient="horizontal")
        self.conc_line_xbar.grid(row=1, column=1, sticky="news")
        self.conc_line_text = tk.Text(self.conc_results_frame, wrap="none", height=30,
                                      yscrollcommand=self.conc_ybar.set,
                                      xscrollcommand=self.conc_line_xbar.set, width=100)
        self.conc_line_text.grid(row=0, column=1, sticky="nesw")
        self.conc_line_xbar.config(command=self.conc_line_text.xview)
        self.conc_index_text = tk.Text(self.conc_results_frame, width=6,
                                       yscrollcommand=self.conc_ybar.set, height=30)
        self.conc_index_text.grid(row=0, column=0, sticky="nesw")
        self.conc_meta_xbar = ttk.Scrollbar(self.conc_results_frame, orient="horizontal")
        self.conc_meta_xbar.grid(row=1, column=3, sticky="news")
        self.conc_meta_canvas = tk.Canvas(self.conc_results_frame, background="white",
                                          xscrollcommand=self.conc_meta_xbar.set)
        self.conc_meta_canvas.grid(row=0, column=3, sticky="news")
        self.conc_meta_xbar.config(command=self.conc_meta_canvas.xview)
        self.conc_meta_canvas_frame = tk.Frame(self.conc_meta_canvas)
        self.conc_meta_text = {}  # corpus & file name, later more with XML corpora if attributes
        self.conc_meta_text["corpus"] = tk.Text(self.conc_meta_canvas_frame, wrap="none", width=20,
                                                height=30)
        self.conc_meta_text["file"] = tk.Text(self.conc_meta_canvas_frame, wrap="none", width=20,
                                              height=30)
        self.parent.root.update_idletasks()
        x2 = self.conc_meta_canvas_frame.winfo_reqwidth()
        self.conc_meta_canvas.create_window(0, 0, anchor="nw", window=self.conc_meta_canvas_frame)
        self.conc_meta_canvas.config(scrollregion=(0, 0, x2, 0))
        # row 1 BUTTONS
        self.conc_button_frame = ttk.Frame(self.conc_frame)
        self.conc_button_frame.columnconfigure(0, weight=0)
        self.conc_button_frame.columnconfigure(1, weight=0)
        self.conc_button_frame.columnconfigure(5, weight=1)
        self.conc_button_frame.grid(row=1, column=0, sticky="news")
        self.conc_start_button = ttk.Button(self.conc_button_frame, text="Search all corpora",
                                            command=self.create_concordance,
                                            style=self.button_style)
        self.conc_start_button.grid(row=1, column=0, sticky="news", columnspan=3)
        self.conc_export_button = ttk.Button(self.conc_button_frame, text="Export concordance",
                                             command=self.export_concordance, state="disabled",
                                             style="Small.TButton")
        self.conc_export_button.grid(row=1, column=3, sticky="news")
        self.conc_sort_button = ttk.Button(self.conc_button_frame, text="Sort by",
                                           command=self.sort_concordance, state="disabled",
                                           style="Small.TButton")
        self.conc_sort_button.grid(row=0, column=0, sticky="news")
        self.conc_sort_combo = []
        self.conc_sort_var = []
        for i in range(0, 3):
            self.conc_sort_var.append(tk.StringVar())
            cb = ttk.Combobox(self.conc_button_frame, textvariable=self.conc_sort_var[i],
                              values=["Left", "Key", "Right", "Corpus", "Filename"],
                              state="readonly", style="Small.TCombobox")
            cb.grid(row=0, column=i+1, sticky="news")
            self.conc_sort_combo.append(cb)
        self.conc_sort_var[0].set("Key")
        self.conc_sort_var[1].set("Right")
        self.conc_sort_var[2].set("Corpus")
        self.conc_filter_var = tk.StringVar()
        tk.Label(self.conc_button_frame, text="Filter text",
                 font="verdana 9").grid(column=4, row=0, sticky="news")
        self.conc_filter_entry = ttk.Entry(self.conc_button_frame,
                                           textvariable=self.conc_filter_var,
                                           style="Small.TEntry", state="disabled")
        self.conc_filter_entry.grid(row=0, column=5, sticky="news")
        self.conc_filter_button = ttk.Button(self.conc_button_frame, text="Filter results",
                                             command=self.filter_concordance,
                                             style="Small.TButton", state="disabled")
        self.conc_filter_button.grid(row=1, column=4, columnspan=2, sticky="news")
        misc.pad_children(self.conc_button_frame, 5, 5)

    def concordance_yview(self, *args):
        self.conc_index_text.yview(*args)
        self.conc_line_text.yview(*args)
        for key, m_text in self.conc_meta_text.items():
            m_text.yview(*args)

    def filter_concordance(self):
        pass

    def sort_concordance(self):
        pass

    def export_concordance(self):
        pass

    def clear_concordance(self):
        self.concordance = []
        self.conc_line_text.delete("0.0", "end")
        self.conc_index_text.delete("0.0", "end")
        for key, m_text in self.conc_meta_text.items():
            m_text.delete("0.0", "end")

    def create_concordance(self):
        self.clear_concordance()
        self.conc_export_button["state"] = "disabled"
        self.num_files = len(self.files)
        options = {}
        options['Regex'] = self.regex
        options['ContextLeft'] = self.context_left.get()
        options['ContextRight'] = self.context_right.get()
        manager = mp.Manager()
        self.pipe, worker_pipe = mp.Pipe()
        self.return_shared = manager.list()
        self.search_job = mp.Process(target=worker_search_files,
                                     args=(self.files, options, self.return_shared, worker_pipe,))
        if self.conc_start_button["text"] == "Search corpus":
            self.set_status("Creating concordance ...")
            self.c_a_start_btn.configure(text="Abort")
            options = misc.get_tk_vars(self.conf['Conc'])
            options.update(dict(self.config.items('General')))
            options.update(self.get_tk_vars(self.conf['XML']))
            options["SearchTerm"] = str(self.c_a_search_term_combo.get())
            search_terms = list(self.c_a_search_term_combo["values"])
            if options["SearchTerm"] not in search_terms:
                search_terms.insert(0, options["SearchTerm"])
                self.c_a_search_term_combo["values"] = search_terms
            corpora = []
            for c in self.corpus:
                corpora.append(c)  # == corpora = self.corpus ?
            self.c_worker_proc = mp.Process(target=conc_worker,
                                            args=(corpora, options,
                                                  self.shared,))
            self.c_worker_proc.start()
            self.root.update()
            self.root.after(500, self.check_conc_proc_status)
        elif self.conc_start_button["text"] == "Abort":
            self.set_status("Concordance creation was aborted.", True)
            self.conc_start_button.configure(text="Search", state="normal")
            self.parent.root.update()
            self.c_worker_proc.terminate()

    def undraw_all(self):
        self.setup_frame.grid_forget()
        self.parent.conc_frame.book.forget(self.conc_frame)
        self.conc_frame.grid_forget()

    def remove(self):
        # remove and hide
        self.undraw_all()
        self.parent.corpus.pop(self.n)
        self.parent.file_frame.listbox.delete(self.n)
        # fix index
        for i, c in enumerate(self.parent.corpus):
            c.n = i
        # select another corpus if possible
        if self.parent.file_frame.listbox.size() > 0:
            if self.n > 0:
                self.parent.file_frame.listbox.selection_set(self.n-1)
            else:
                self.parent.file_frame.listbox.selection_set(0)
            visible_n = self.parent.file_frame.listbox.curselection()[0]
            self.parent.file_frame.on_corpus_select(visible_n=visible_n)

    def clear_files(self):
        self.files = []
        self.listbox.delete(0, "end")

    def choose_color(self):
        color = colorchooser.askcolor()
        if color:
            self.color = color[1]
            self.set_styles()

    def add_files(self):
        options = {}
        config = self.parent.config_frame.config
        options['defaultextension'] = config["General"]["DefaultExtension"]
        if options['defaultextension'] == ".txt":
            options['filetypes'] = [('Text files', '.txt'), ('XML files', '.xml'),
                                    ('HTML files', '.html')]
        if options['defaultextension'] == ".xml":
            options['filetypes'] = [('XML files', '.xml'), ('Text files', '.txt'),
                                    ('HTML files', '.html')]
        if options['defaultextension'] == ".html":
            options['filetypes'] = [('HTML files', '.html'),
                                    ('Text files', '.txt'),
                                    ('XML files', '.xml')]
        default_dir = config["General"]["DefaultInputDir"].strip()
        if os.path.exists(default_dir):
            options['initialdir'] = default_dir
        else:
            options['initialdir'] = ""
        options['initialfile'] = ''
        options['parent'] = self.setup_frame
        options['title'] = 'Open corpus file(s)'
        files_str = filedialog.askopenfilenames(**options)
        for f in self.parent.root.splitlist(files_str):
            self.files.append(f)
            self.listbox.insert("end", os.path.basename(f))

if __name__ == "__main__":
    openconc.main()
 
