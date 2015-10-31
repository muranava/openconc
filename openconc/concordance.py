import tkinter as tk
from tkinter import ttk
import multiprocessing as mp
import os
import re
from openconc import misc
import operator


def worker_search_files(files, options, return_shared, pipe):
    b = ""
    if bool(options['Case']):
        flags = re.UNICODE
    else:
        flags = re.UNICODE | re.IGNORECASE
    if bool(options['IsRegEx']):
        s = r'{0}{1}{0}'.format(b, options["SearchTerm"])
        options['RegExPattern'] = re.compile(s, flags=flags)
    else:
        s = r'{0}{1}{0}'.format(
            b, re.escape(options["SearchTerm"].strip()))
        options['RegExPattern'] = re.compile(s, flags=flags)
    args = ((i, options) for i in files)
    jobs = []
    pool_size = mp.cpu_count()
    if pool_size > 1:
        pool_size -= 1
    pool = mp.Pool(pool_size)
    for job in pool.imap_unordered(worker_search_in_file, args):
        jobs.append(job)
        if job:
            try:
                pipe.send(job)
            except OSError as e:
                print(e)
            return_shared += job
    pool.close()


def worker_search_in_file(args):
    f, o = args
    handler = open(f, "r")
    f_text = handler.read()
    conc = []
    if bool(o['IgnorePOS']) == True:
        pos_delim = o['POSDelim']
        pos_tag = "[A-Z]{2,}[A-Z$0-9+*]*?"
        tag_str = "{0}{1}".format(pos_delim, pos_tag)
        f_text = re.sub(r"{0}\s".format(tag_str), r"", f_text)
    if bool(o['IgnoreXML']) == True:
        f_text = re.sub(r"<[^>]+>", r"", f_text)
        f_text = re.sub(r"&lt;[^&]+&gt;", r"", f_text)
    handler.close()
    matches = re.finditer(o['RegExPattern'], f_text)
    if matches:
        for n, m in enumerate(matches):
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
                # assume that each word = 30 characters long , to be reasonably safe
                l_char = int(o['ContextLeft']) * 30
                r_char = int(o['ContextRight']) * 30
                c['Right'] = misc.tokenize_str(f_text[e:e + r_char],
                                               o['WordRegex'])
                c['Left'] = misc.tokenize_str(f_text[s - l_char:s],
                                               o['WordRegex'])
                c['Left'] = " ".join(c['Left'][-int(o['ContextRight']):])
                c['Right'] = " ".join(c['Right'][0:int(o['ContextRight'])])

            c['Filename'] = os.path.basename(f)
            c['N'] = n  # number of match within file, used for sorting after filename
            conc.append(c)
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
        self.line_text.grid(row=0, column=1, sticky="news")
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
        metadata = ["Corpus", "Filename"]
        for i, m in enumerate(metadata):
            self.meta_text[m] = tk.Text(self.meta_canvas_frame, wrap="none", width=30, height=30)
            self.meta_text[m].grid(row=0, column=i, sticky="news")
        self.parent.root.update_idletasks()
        x2 = self.meta_canvas_frame.winfo_reqwidth()
        self.meta_canvas.create_window(0, 0, anchor="nw", window=self.meta_canvas_frame)
        self.meta_canvas.config(scrollregion=(0, 0, x2, 0))
        # row 1 BUTTONS
        self.button_frame = ttk.Frame(self.all_frame)
        self.button_frame.columnconfigure(0, weight=0)
        self.button_frame.columnconfigure(1, weight=0)
        self.button_frame.columnconfigure(5, weight=1)

        self.button_frame.grid(row=1, column=0, sticky="news")
        self.start_button = ttk.Button(self.button_frame, text="Search all corpora",
                                       command=self.create_concordance)
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
        self.filter_button = ttk.Button(self.button_frame, text="Filter concordance results",
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

    def clear_concordance_view(self):
        misc.enable_all_in_frame(self.results_frame)
        self.line_text.delete("0.0", "end")
        self.index_text.delete("0.0", "end")
        for key, m_text in self.meta_text.items():
            m_text.delete("0.0", "end")
        misc.disable_all_in_frame(self.results_frame)

    def add_search_term(self, search_term):
        search_terms = list(self.parent.concordance_frame.search_combo["values"])
        if search_term not in search_terms:
            search_terms.insert(0, search_term)
            self.parent.concordance_frame.search_combo["values"] = search_terms

    def check_proc_statuses(self):
        try:
            alive = 0
            for i, job in enumerate(self.jobs):
                if job.is_alive():
                    alive += 1
                    n = self.parent.corpus[i].name_var.get()
                    try:
                        if self.pipes[i].poll():
                            try:
                                results = self.pipes[i].recv()
                            except OSError as e:
                                print(e)
                            else:
                                for r in results:
                                    self.add_concordance_line(r, n)
                                    self.parent.corpus[i].add_concordance_line(r, n)
                    except OSError as e:
                        print(e)
                else:
                    job.join()
            if alive == 0:
                if not self.cancelled:
                    self.finish_search()
                else:
                    self.clear_concordance_view()
                    self.concordance = []
                self.parent.root.after_cancel(self.after_job)
                self.start_button["text"] = "Search all corpora"
                for j in self.jobs:
                    j.terminate()
            else:
                self.parent.root.update_idletasks()
                self.after_job = self.parent.root.after(1000, self.check_proc_statuses)

        except Exception as e:
            print("checking...", e)

    def improve_concordance_display(self):
        """ resize frames depending on content """
        i = int(self.line_text.index('end-1c').split('.')[0])-1
        self.index_text.configure(width=len(str(i)))
        self.parent.root.update_idletasks()

    def display_concordance(self):
        if self.concordance is not None:
            misc.enable_all_in_frame(self.results_frame)
            for i, l in enumerate(self.concordance):
                self.add_concordance_line(l, None, i)
            self.parent.root.update_idletasks()
            self.improve_concordance_display()
            misc.disable_all_in_frame(self.results_frame)

    def finish_search(self):
        self.concordance = []
        for corpus in self.parent.corpus:
            for l in corpus.conc_return_shared:
                l["Corpus"] = corpus.name_var.get()
                self.concordance.append(l)
            corpus.finish_conc_search()
        self.concordance = sorted(self.concordance,
                                  key=operator.itemgetter('Corpus', 'Filename', 'N'))
        self.clear_concordance_view()
        self.display_concordance()
        self.export_button["state"] = "normal"
        self.parent.set_status("Found {} results in all corpora.".format(len(self.concordance)))

    def add_metadata(self, l, n):
        for key, m_text in self.meta_text.items():
            if n is not None:
                l['Corpus'] = n
            m_text.insert("end", "{}\n".format(l[key]))

    def add_concordance_line(self, l, n, i=0):
        l['Left'] = l['Left'].rjust(self.options['ContextLeft'])
        l['Right'] = l['Right'].ljust(self.options['ContextRight'])
        conc_line = "{0}\t\t{1}\t\t{2}\n".format(l['Left'],
                                                 l['Key'],
                                                 l['Right'])
        self.line_text.insert("end", conc_line)
        i = int(self.line_text.index('end-1c').split('.')[0])-1  # last line of text
        self.index_text.insert("end", "{}\n".format(i))
        self.add_metadata(l, n)

    def create_concordance(self):
        self.clear_concordance_view()
        self.concordance = []
        if self.start_button["text"] == "Search all corpora":
            self.cancelled = False
            self.export_button["state"] = "disabled"
            self.filter_button["state"] = "disabled"
            self.parent.set_status("Creating concordance ...")
            self.start_button["text"] = "Abort"
            self.index_text["width"] = 6
            options = misc.get_tk_vars(self.parent.settings_frame.definition)
            options.update(misc.get_tk_vars(self.parent.settings_frame.file))
            options.update(misc.get_tk_vars(self.parent.settings_frame.concordance))
            options.update(misc.get_tk_vars(self.parent.settings_frame.xml))
            options["SearchTerm"] = self.parent.concordance_frame.search_var.get()
            self.options = options
            self.add_search_term(options["SearchTerm"])
            self.pipes = []
            self.jobs = []
            self.corpora = []
            self.shared = []
            misc.enable_all_in_frame(self.results_frame)
            for corpus in self.parent.corpus:
                misc.enable_all_in_frame(corpus.conc_results_frame)
                corpus.conc_options = options
                manager = mp.Manager()
                corpus.conc_return_shared = manager.list()
                pipe, worker_pipe = mp.Pipe()
                job = mp.Process(target=worker_search_files,
                                 args=(corpus.files, corpus.conc_options,
                                       corpus.conc_return_shared, worker_pipe,))
                self.jobs.append(job)
                self.pipes.append(pipe)
                #  so that job, pipe and corpus frame can be accessed with same index
            for j in self.jobs:
                j.start()
            self.parent.root.update_idletasks()
            self.parent.root.after(500, self.check_proc_statuses)
        elif self.start_button["text"] == "Abort":
            self.cancelled = True
            self.parent.set_status("Concordance creation was aborted.", True)
            self.start_button.configure(text="Search", state="normal")
            self.parent.root.update_idletasks()
            for job in self.jobs:
                job.terminate()

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
