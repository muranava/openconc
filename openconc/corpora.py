import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import colorchooser
import multiprocessing as mp
import os
import re
import operator
from openconc import misc
from openconc.concordance import worker_search_files


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
        self.conc_frame.rowconfigure(0, weight=1)
        self.conc_frame.rowconfigure(1, weight=0)
        self.conc_frame.columnconfigure(0, weight=1)
        parent.book.add(self.conc_frame, text=self.name_var.get())
        # row 1
        self.conc_button_frame = ttk.Frame(self.conc_frame)
        self.conc_button_frame.grid(row=1, column=0, sticky="news")
        # row 0
        self.conc_results_frame = ttk.Frame(self.conc_frame)
        self.conc_results_frame.grid(row=0, column=0, sticky="news")
        self.conc_results_frame.rowconfigure(0, weight=1)
        self.conc_results_frame.rowconfigure(1, weight=0)  # x scrollbars
        self.conc_results_frame.columnconfigure(0, weight=0)  # index
        self.conc_results_frame.columnconfigure(1, weight=1)  # conc line
        self.conc_results_frame.columnconfigure(2, weight=0)  # y  scrollbar
        self.conc_results_frame.columnconfigure(3, weight=0)   # metadata
        self.conc_ybar = ttk.Scrollbar(self.conc_results_frame, command=self.concordance_yview)
        self.conc_ybar.grid(row=0, column=2, sticky="news")
        self.conc_line_xbar = ttk.Scrollbar(self.conc_results_frame, orient="horizontal")
        self.conc_line_xbar.grid(row=1, column=1, sticky="news")
        self.conc_line_text = tk.Text(self.conc_results_frame, wrap="none", yscrollcommand=self.conc_ybar.set,
                                      xscrollcommand=self.conc_line_xbar.set, font='courier 10')
        self.conc_line_text.grid(row=0, column=1, sticky="news")
        self.conc_line_text.tag_configure('key', foreground='black', font='courier 10 bold')
        self.conc_line_xbar.config(command=self.conc_line_text.xview)
        self.conc_index_text = tk.Text(self.conc_results_frame, width=8, yscrollcommand=self.conc_ybar.set,
                                       font='courier 10', wrap="none")
        self.conc_index_text.grid(row=0, column=0, sticky="nesw")
        self.conc_meta_xbar = ttk.Scrollbar(self.conc_results_frame, orient="horizontal")
        self.conc_meta_xbar.grid(row=1, column=3, sticky="news")
        self.conc_meta_canvas = tk.Canvas(self.conc_results_frame, background="white",
                                          xscrollcommand=self.conc_meta_xbar.set)
        self.conc_meta_canvas.grid(row=0, column=3, sticky="news")
        self.conc_meta_xbar.config(command=self.conc_meta_canvas.xview)
        self.conc_meta_canvas_frame = tk.Frame(self.conc_meta_canvas)
        self.conc_meta_text = {}  # corpus & file name, later more with XML corpora if attributes
        metadata = ["Corpus", "Filename"]
        for i, m in enumerate(metadata):
            self.conc_meta_text[m] = tk.Text(self.conc_meta_canvas_frame, wrap="none", font='courier 10')
            self.conc_meta_text[m].grid(row=0, column=i, sticky="news")
        misc.disable_all_in_frame(self.conc_results_frame)
        self.parent.root.update_idletasks()
        x2 = self.conc_meta_canvas_frame.winfo_reqwidth()
        self.conc_meta_canvas.create_window(0, 0, anchor="nw", window=self.conc_meta_canvas_frame)
        self.conc_meta_canvas.config(scrollregion=(0, 0, x2, 0))
        h = self.conc_meta_canvas_frame.winfo_reqheight()
        for i, m_text in self.conc_meta_text.items():
            m_text["height"] = h
            m_text["width"] = 20

        # row 1 BUTTONS
        self.conc_button_frame = ttk.Frame(self.conc_frame)
        self.conc_button_frame.columnconfigure(0, weight=0)
        self.conc_button_frame.columnconfigure(1, weight=0)
        self.conc_button_frame.columnconfigure(5, weight=1)
        self.conc_button_frame.grid(row=1, column=0, sticky="news")
        self.conc_start_button = ttk.Button(self.conc_button_frame, text="Search this corpus",
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
        self.conc_filter_entry.grid(row=0, column=5, sticky="news", columnspan=3)
        self.conc_filter_button = ttk.Button(self.conc_button_frame, text="Filter",
                                             command=self.filter_concordance,
                                             style="Small.TButton", state="disabled")
        self.conc_filter_button.grid(row=1, column=4, columnspan=2, sticky="news")
        self.conc_filter_what_var = tk.StringVar()
        self.conc_filter_what_combo = ttk.Combobox(self.conc_button_frame, textvariable=self.conc_filter_what_var,
                                                   values=['Key', "Left", "Right", "Line"], state="readonly")
        self.conc_filter_what_var.set('Key')
        self.conc_filter_what_combo.grid(row=1, column=6, sticky="news")
        self.conc_unfilter_button = ttk.Button(self.conc_button_frame, text="Undo filter",
                                               command=self.unfilter_concordance,
                                               style="Small.TButton", state="disabled")
        self.conc_unfilter_button.grid(row=1, column=7, sticky="news")
        misc.pad_children(self.conc_button_frame, 5, 5)

    def concordance_yview(self, *args):
        self.conc_index_text.yview(*args)
        self.conc_line_text.yview(*args)
        for key, m_text in self.conc_meta_text.items():
            m_text.yview(*args)

    def unfilter_concordance(self):
        self.concordance_filtered = []
        self.clear_concordance_view()
        self.display_concordance()

    def filter_concordance(self):
        if len(self.concordance) > 0:
            self.concordance_filtered = []
            filter_by = self.conc_filter_var.get()
            what = self.conc_filter_what_combo.get()
            case = bool(self.parent.settings_frame.concordance['Case'].get())
            regex = bool(self.parent.settings_frame.concordance['IsRegEx'].get())
            if case and not regex:
                filter_by = filter_by.lower()
            elif regex:
                if case:
                    flags = re.UNICODE
                else:
                    flags = re.UNICODE | re.IGNORECASE
                s = r'{0}'.format(filter_by)
                re_pattern = re.compile(s, flags=flags)
            for l in self.concordance:
                if what == "Line":
                    line = "{} {} {}".format(l['Left'], l['Key'], l['Right'])
                    if not regex:
                        if not case:
                            line = line.lower()
                        if filter_by in line:
                            self.concordance_filtered.append(l)
                    else:
                        if re_pattern.search(line):
                            self.concordance_filtered.append(l)
                else:
                    if not regex:
                        if not case:
                            l[what] = l[what].lower()
                        if filter_by in l[what]:
                            self.concordance_filtered.append(l)
                    else:
                        if re_pattern.search(l[what]):
                            self.concordance_filtered.append(l)
            self.clear_concordance_view()
            misc.enable_all_in_frame(self.conc_results_frame)
            for i, l in enumerate(self.concordance_filtered):
                self.add_concordance_line(l, i)
            self.parent.root.update_idletasks()
            misc.disable_all_in_frame(self.conc_results_frame)
            self.conc_unfilter_button["state"] = "enabled"

    def sort_concordance(self):
        if len(self.concordance) > 0:
            sort_by = [s.get() for s in self.conc_sort_var]
            self.concordance = sorted(self.concordance, key=operator.itemgetter(*sort_by))
            self.clear_concordance_view()
            self.display_concordance()

    def export_concordance(self):
        pass

    def clear_concordance_view(self):
        misc.enable_all_in_frame(self.conc_results_frame)
        self.conc_line_text.delete("0.0", "end")
        self.conc_index_text.delete("0.0", "end")
        for key, m_text in self.conc_meta_text.items():
            m_text.delete("0.0", "end")
        misc.disable_all_in_frame(self.conc_results_frame)

    def check_conc_proc_status(self):
        try:
            if self.conc_job.is_alive():
                try:
                    results = self.q.get()
                except (OSError, UnicodeDecodeError) as e:
                    print(e)
                else:
                    for i, m in self.conc_meta_text.items():
                        m["state"] = "normal"
                    self.conc_index_text["state"] = "normal"
                    self.conc_line_text["state"] = "normal"
                    for r in results:
                        self.add_concordance_line(r)
                        self.concordance.append(r)

                self.parent.root.update_idletasks()
                self.after_conc_job = self.parent.root.after(500, self.check_conc_proc_status)
            else:
                try:
                    self.parent.root.after_cancel(self.after_conc_job)
                except AttributeError:
                    pass  # if it hasn't been called yet, no problem
                self.conc_start_button["text"] = "Search this corpus"
                self.parent.concordance_frame.start_button["state"] = "normal"
                self.conc_job.terminate()
                if self.conc_cancelled:
                    self.clear_concordance_view()
                    self.concordance = []
                else:
                    self.finish_conc_search()
        except AttributeError as e:
            print(e)


    def add_metadata(self, l):
        for key, m_text in self.conc_meta_text.items():
            m_text.insert("end", "{}\n".format(l[key]))

    def add_concordance_line(self, l, i=0):
        l['Left'] = l['Left'].rjust(self.conc_options['ContextLeft'])
        l['Right'] = l['Right'].ljust(self.conc_options['ContextRight'])
        conc_line = "{0}    {1}    {2}\n".format(l['Left'], l['Key'], l['Right'])
        self.add_metadata(l)
        self.conc_line_text.insert("end", conc_line)
        i = int(self.conc_line_text.index('end-1c').split('.')[0])-1  # last line of text
        line_key_start = "{}.{}".format(i, len(l['Left'])+4)
        line_key_end = "{}.{}".format(i, len(l['Left']) + 4 + len(l['Key']))
        self.conc_line_text.tag_add("key", line_key_start, line_key_end)
        self.conc_index_text.insert("end", "{}\n".format(i))

    def improve_concordance_display(self):
        """ resize frames depending on content """
        longest_filename = 0
        for f in self.files:
            fn = os.path.basename(f)
            if len(fn) > longest_filename:
                longest_filename = len(fn)
        self.conc_meta_text['Filename'].configure(width=longest_filename)
        self.conc_meta_text['Corpus'].configure(width=len(self.concordance[0]["Corpus"]))
        i = int(self.conc_line_text.index('end-1c').split('.')[0])-1
        self.conc_index_text.configure(width=len(str(i)))
        self.parent.root.update_idletasks()

    def display_concordance(self):
        self.clear_concordance_view()
        if self.concordance is not None:
            for i, m in self.conc_meta_text.items():
                m["state"] = "normal"
            self.conc_index_text["state"] = "normal"
            self.conc_line_text["state"] = "normal"
            for i, l in enumerate(self.concordance):
                self.add_concordance_line(l, i)
            self.parent.root.update_idletasks()
            for i, m in self.conc_meta_text.items():
                m["state"] = "disabled"
            self.conc_index_text["state"] = "disabled"
            self.conc_line_text["state"] = "disabled"
            if len(self.concordance) > 0:
                self.improve_concordance_display()

    def finish_conc_search(self):
        self.concordance = sorted(self.conc_return_shared,
                                  key=operator.itemgetter('Filename', 'N'))
        self.parent.set_status("Found {} results in '{}'.".format(len(self.concordance),
                                                                  self.name_var.get()))
        self.display_concordance()
        self.conc_export_button["state"] = "normal"
        misc.disable_all_in_frame(self.conc_results_frame)
        if len(self.concordance) > 0:
            self.conc_export_button["state"] = "normal"
            self.conc_sort_button["state"] = "normal"
            self.conc_start_button["state"] = "normal"
            self.conc_start_button["text"] = "Search all corpora"
            self.conc_filter_button["state"] = "normal"
            self.conc_filter_entry["state"] = "normal"

    def create_concordance(self):
        self.clear_concordance_view()
        self.concordance = []
        self.concordance_filtered = []
        self.conc_export_button["state"] = "disabled"
        if self.conc_start_button["text"] == "Search this corpus":
            self.conc_cancelled = False
            self.parent.set_status("Creating concordance ...")
            self.conc_start_button["text"] = "Abort"
            self.parent.concordance_frame.start_button["state"] = "disabled"
            self.conc_index_text["width"] = 6
            options = misc.get_tk_vars(self.parent.settings_frame.definition)
            options.update(misc.get_tk_vars(self.parent.settings_frame.file))
            options.update(misc.get_tk_vars(self.parent.settings_frame.concordance))
            options.update(misc.get_tk_vars(self.parent.settings_frame.xml))
            options["SearchTerm"] = self.parent.concordance_frame.search_var.get()
            options["Corpus"] = self.name_var.get()
            self.conc_options = options
            self.parent.concordance_frame.add_search_term(options["SearchTerm"])
            manager = mp.Manager()
            self.conc_return_shared = manager.list()
            self.q = mp.Queue()
            self.conc_job = mp.Process(target=worker_search_files,
                                       args=(self.files, options, self.conc_return_shared, self.q,))
            self.conc_job.start()
            self.parent.root.update_idletasks()
            self.parent.root.after(500, self.check_conc_proc_status)
        elif self.conc_start_button["text"] == "Abort":
            self.search_cancelled = True
            self.parent.set_status("Concordance creation was aborted.", True)
            self.conc_start_button.configure(text="Search", state="normal")
            self.parent.root.update_idletasks()
            self.conc_job.terminate()

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
        config = self.parent.settings_frame.config
        options['defaultextension'] = config["File"]["Extension"]
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
        default_dir = config["File"]["InputDir"].strip()
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
