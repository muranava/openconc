import tkinter as tk
from tkinter import ttk
import multiprocessing as mp
import os
import re
from openconc import misc
import operator


def worker_search_files(files, options, return_shared, q):
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
    pool_size = 2  # testing
    pool = mp.Pool(pool_size)
    for job in pool.imap_unordered(worker_search_in_file, args):
        if job:
            return_shared += job
            try:
                q.put(job)
            except Exception as e:
                print(e)
    pool.close()



def worker_search_in_file(args):
    f, o = args
    handler = open(f, "r")
    f_text = handler.read()
    conc = []
    if bool(o['IgnorePOS']) == True:
        pos_delim = o['POSDelim']
        pos_tag = "[A-Z\.,-]{2,}[A-Z$0-9+*]*?"
        tag_str = "{0}{1}".format(pos_delim, pos_tag)
        f_text = re.sub(r"{0}\s".format(tag_str), r" ", f_text)
    if bool(o['IgnoreXML']) == True:
        f_text = re.sub(r"<[^>]+>", r"", f_text)
        f_text = re.sub(r"&lt;[^&]+&gt;", r" ", f_text)
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
                c['Left'] = misc.tokenize_str(f_text[s - l_char:s], o['WordRegex'])
                c['Left'] = " ".join(c['Left'][-int(o['ContextRight']):])
                c['Right'] = " ".join(c['Right'][0:int(o['ContextRight'])])

            c['Corpus'] = o['Corpus']
            if "CorpusIndex" in o.keys():
                c['CorpusIndex'] = o['CorpusIndex']
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
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.book = ttk.Notebook(self)
        self.book.grid(column=0, row=0, sticky="news")
        self.rowconfigure(0, weight=1)  # conc tabs
        self.rowconfigure(1, weight=0)  # search frame
        # SEARCH frame
        self.search_frame = ttk.Frame(self)
        self.search_frame.grid(row=1, column=0, sticky="news")
        self.search_frame.rowconfigure(0, weight=0)
        self.search_frame.rowconfigure(1, weight=0)
        self.search_frame.columnconfigure(0, weight=0)
        self.search_frame.columnconfigure(8, weight=1)
        # row 0
        tk.Label(self.search_frame, text="Search text", font="verdana 12").grid(column=0, row=0,
                                                                                sticky="nw")
        self.search_var = tk.StringVar()
        self.search_combo = ttk.Combobox(self.search_frame, textvariable=self.search_var,
                                         style="Search.TCombobox", font="verdana 12")
        self.search_combo.grid(row=0, column=1, sticky="new", columnspan=8)
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
        self.left_entry.grid(row=1, column=1, sticky="new")
        self.right_entry.grid(row=1, column=3, sticky="new")
        self.unit_combo = ttk.Combobox(self.search_frame,
                                       textvariable=settings.concordance[
                                           'ContextUnit'],
                                       values=["Characters", "Words"], state="readonly")
        self.unit_combo["width"] = 8
        self.unit_combo.grid(row=1, column=5, sticky="new")

        self.case_check = ttk.Checkbutton(
            self.search_frame, text="Case sensitive", variable=settings.concordance['Case'])
        self.case_check.grid(row=1, column=6)

        self.regex_check = ttk.Checkbutton(
            self.search_frame, text="Regular expression", variable=settings.concordance['IsRegEx'])
        self.regex_check.grid(row=1, column=7)

        # ALL tab
        self.all_frame = ttk.Frame(self)
        self.all_frame.rowconfigure(0, weight=1)
        self.all_frame.rowconfigure(1, weight=0)
        self.all_frame.columnconfigure(0, weight=1)  # !!!
        self.book.add(self.all_frame, text="All corpora")
        # row 0 RESULTS
        self.results_frame = ttk.Frame(self.all_frame)
        self.results_frame.rowconfigure(0, weight=1)
        self.results_frame.rowconfigure(1, weight=0)  # x scrollbars
        self.results_frame.columnconfigure(0, weight=0)  # index
        self.results_frame.columnconfigure(1, weight=1)  # conc line
        self.results_frame.columnconfigure(2, weight=0)  # y  scrollbar
        self.results_frame.columnconfigure(3, weight=0)   # metadata
        self.results_frame.grid(row=0, column=0, sticky="news")
        self.ybar = ttk.Scrollbar(self.results_frame, command=self.yview)
        self.ybar.grid(row=0, column=2, sticky="news")
        self.line_xbar = ttk.Scrollbar(self.results_frame, orient="horizontal")
        self.line_xbar.grid(row=1, column=1, sticky="news")
        self.line_text = tk.Text(self.results_frame, wrap="none", font='courier 10',
                                 yscrollcommand=self.ybar.set,
                                 xscrollcommand=self.line_xbar.set)
        self.line_text.grid(row=0, column=1, sticky="news")
        self.line_text.tag_configure('key', foreground='black', font='courier 10 bold')
        self.line_xbar.config(command=self.line_text.xview)
        self.index_text = tk.Text(self.results_frame, width=8, yscrollcommand=self.ybar.set, font='courier 10',
                                  wrap="none")
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
        self.parent.root.update_idletasks()
        for i, m in enumerate(metadata):
            self.meta_text[m] = tk.Text(self.meta_canvas_frame, wrap="none", font='courier 10')
            self.meta_text[m].grid(row=0, column=i, sticky="news")
        self.parent.root.update_idletasks()
        x2 = self.meta_canvas_frame.winfo_reqwidth()
        self.meta_canvas.create_window(0, 0, anchor="nw", window=self.meta_canvas_frame)
        self.meta_canvas.config(scrollregion=(0, 0, x2, 0))
        h = self.meta_canvas_frame.winfo_reqheight()
        for i, m_text in self.meta_text.items():
            m_text["height"] = h
            m_text["width"] = 20

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
        self.filter_entry.grid(row=0, column=5, sticky="news", columnspan=3)
        self.filter_button = ttk.Button(self.button_frame, text="Filter concordance results",
                                        command=self.filter_concordance,
                                        style="Small.TButton",
                                        state="disabled")
        self.filter_button.grid(row=1, column=4, columnspan=2, sticky="news")
        self.filter_what_var = tk.StringVar()
        self.filter_what_combo = ttk.Combobox(self.button_frame, textvariable=self.filter_what_var,
                                              values=['Key', "Left", "Right", "Line"], state="readonly")
        self.filter_what_var.set('Key')
        self.filter_what_combo.grid(row=1, column=6, sticky="news")
        self.unfilter_button = ttk.Button(self.button_frame, text="Undo filter",
                                          command=self.unfilter_concordance, style="Small.TButton", state="disabled")
        self.unfilter_button.grid(row=1, column=7, sticky="news")

        misc.pad_children(self.search_frame, 5, 5)
        misc.pad_children(self.button_frame, 5, 5)

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
            try:
                results = self.q.get()
            except (OSError, UnicodeDecodeError) as e:
                print("concodance pipe.recv:", e)
            except Exception as e:
                print("concodance pipe.recv UNEXPECTEd", e)
                raise(e)
            else:
                for r in results:
                    self.add_concordance_line(r)
                    self.parent.corpus[r['CorpusIndex']].add_concordance_line(r)
                n = int(self.index_text.index('end-1c').split('.')[0])
                if n > 0:
                    self.parent.set_status("Creating concordance... ({} results so far)".format(n))
            for job in self.jobs:
                if job.is_alive():
                    alive += 1
                else:
                    job.join()
            if alive == 0:
                if not self.cancelled:
                    self.finish_search()
                else:
                    self.clear_concordance_view()
                    self.concordance = []
                try:
                    self.parent.root.after_cancel(self.after_job)
                except AttributeError:
                    pass  # if it hasn't been called yet, no problem
                self.start_button["text"] = "Search all corpora"
                for j in self.jobs:
                    j.terminate()
            else:
                self.parent.root.update_idletasks()
                self.after_job = self.parent.root.after(500, self.check_proc_statuses)

        except Exception as e:
            raise(e)

    def improve_concordance_display(self):
        """ resize frames depending on content """
        i = int(self.line_text.index('end-1c').split('.')[0])-1
        self.index_text.configure(width=len(str(i)))
        longest_filename = 0
        longest_corpus = 0
        for l in self.concordance:
            if len(l['Filename']) > longest_filename:
                longest_filename = len(l['Filename'])
            if len(l['Corpus']) > longest_corpus:
                longest_corpus = len(l['Corpus'])
        self.meta_text['Filename'].configure(width=longest_filename)
        self.meta_text['Corpus'].configure(width=longest_corpus)
        self.parent.root.update_idletasks()

    def display_concordance(self):
        if self.concordance is not None:
            misc.enable_all_in_frame(self.results_frame)
            for i, l in enumerate(self.concordance):
                self.add_concordance_line(l, i)
            self.parent.root.update_idletasks()
            if len(self.concordance) > 0:
                self.improve_concordance_display()
            misc.disable_all_in_frame(self.results_frame)

    def unfilter_concordance(self):
        self.concordance_filtered = []
        self.clear_concordance_view()
        self.display_concordance()

    def filter_concordance(self):
        if len(self.concordance) > 0:
            self.concordance_filtered = []
            filter_by = self.filter_var.get()
            what = self.filter_what_combo.get()
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
            misc.enable_all_in_frame(self.results_frame)
            for i, l in enumerate(self.concordance_filtered):
                self.add_concordance_line(l, i)
            self.parent.root.update_idletasks()
            misc.disable_all_in_frame(self.results_frame)
            self.unfilter_button["state"] = "enabled"

    def sort_concordance(self):
        if len(self.concordance) > 0:
            sort_by = [s.get() for s in self.sort_var]
            self.concordance = sorted(self.concordance, key=operator.itemgetter(*sort_by))
            self.clear_concordance_view()
            self.display_concordance()

    def finish_search(self):
        self.concordance = []
        for corpus in self.parent.corpus:
            corpus_tag = "C{}".format(corpus.name_var.get().replace(" ", ""))
            self.meta_text["Corpus"].tag_configure(corpus_tag, background=corpus.color)
            self.concordance += corpus.conc_return_shared
            corpus.finish_conc_search()
        self.concordance = sorted(self.concordance, key=operator.itemgetter('Corpus', 'Filename', 'N'))
        self.clear_concordance_view()
        self.display_concordance()
        if len(self.concordance) > 0:
            self.export_button["state"] = "normal"
            self.sort_button["state"] = "normal"
            self.start_button["state"] = "normal"
            self.start_button["text"] = "Search all corpora"
            self.filter_button["state"] = "normal"
            self.filter_entry["state"] = "normal"
        self.parent.set_status("Found {} results in all corpora.".format(len(self.concordance)))

    def add_metadata(self, l):
        for key, m_text in self.meta_text.items():
            m_text.insert("end", "{}\n".format(l[key]))

    def add_concordance_line(self, l, i=0):
        l['Left'] = l['Left'].rjust(self.options['ContextLeft'])
        l['Right'] = l['Right'].ljust(self.options['ContextRight'])
        conc_line = "{0}    {1}    {2}\n".format(l['Left'], l['Key'], l['Right'])
        self.line_text.insert("end", conc_line)
        self.add_metadata(l)
        i = int(self.line_text.index('end-1c').split('.')[0])-1  # last line of text
        line_key_start = "{}.{}".format(i, len(l['Left'])+4)
        line_key_end = "{}.{}".format(i, len(l['Left']) + 4 + len(l['Key']))
        self.line_text.tag_add("key", line_key_start, line_key_end)
        self.index_text.insert("end", "{}\n".format(i))
        corpus_tag = "C{}".format(l['Corpus'].replace(" ", ""))
        corpus_start = "{}.0".format(i)
        corpus_end = "{}.{}".format(i, len(l['Corpus']))
        self.meta_text["Corpus"].tag_add(corpus_tag, corpus_start, corpus_end)



    def create_concordance(self):
        self.clear_concordance_view()
        self.concordance = []
        self.concordance_filtered = []
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
            self.q = mp.Queue()
            for i, corpus in enumerate(self.parent.corpus):
                corpus_tag = "C{}".format(corpus.name_var.get().replace(" ", ""))
                self.meta_text["Corpus"].tag_configure(corpus_tag, background=corpus.color)
                misc.enable_all_in_frame(corpus.conc_results_frame)
                misc.disable_all_in_frame(corpus.conc_button_frame)
                options["CorpusIndex"] = i
                options["Corpus"] = corpus.name_var.get()
                corpus.conc_options = options
                manager = mp.Manager()
                corpus.conc_return_shared = manager.list()
                job = mp.Process(target=worker_search_files,
                                 args=(corpus.files, options,
                                       corpus.conc_return_shared, self.q,))
                self.jobs.append(job)
                job.start()
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
