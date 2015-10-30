import tkinter as tk
from tkinter import ttk
from openconc import misc
from openconc import corpora


class FileFrame(tk.Frame):
    def __init__(self, parent,  *args, **kwargs):
        tk.Frame.__init__(self)
        self.parent = parent
        self.default_colors = ["#77DD77", "#5EF1F2", "#FFA8BB", "#AEC6CF", "#FFCC99", "#CB99C9",
                               "#94FFB5", "#FFB347", "#9DCC00", "#00AA9F", "#E0FF66", "#FFD1DC"]
        self.draw_ui()
        self.set_bindings()

    def draw_ui(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(2, weight=1)
        self.add_button = ttk.Button(self, command=self.add_corpus, text="Add a corpus", width=20)
        self.add_button.grid(row=1, column=0, sticky="news")
        self.corpora_frame = ttk.Frame(self)
        self.corpora_frame.rowconfigure(0, weight=1)
        self.corpora_frame.columnconfigure(0, weight=0)
        self.corpora_frame.grid(row=0, column=2, sticky="news")
        misc.pad_children(self, 5, 5)
        self.listbox = tk.Listbox(self, selectmode='browse', exportselection=0)
        self.listbox.grid(row=0, column=0, sticky="news")
        self.scrollbar = ttk.Scrollbar(self, command=self.listbox.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.listbox["yscrollcommand"] = self.scrollbar.set

    def set_bindings(self):
        self.listbox.bind('<<ListboxSelect>>', self.on_corpus_select)

    def on_corpus_select(self, event=None, visible_n=None):
        if visible_n is not None:
            self.visible_n = visible_n
        n = self.listbox.curselection()[0]
        # deal with previous
        self.parent.corpus[self.visible_n].setup_frame.grid_remove()
        name = self.parent.corpus[self.visible_n].name_var.get()  # for name sanity check
        if not name:
            self.parent.corpus[self.visible_n].name_var.set("Corpus {}".format(self.visible_n+1))
            self.listbox.delete(self.visible_n)
            self.listbox.insert(self.visible_n, self.parent.corpus[self.visible_n].name_var.get())

        # show new
        self.parent.corpus[n].setup_frame.grid()
        self.visible_n = n

    def hide_all_corpora(self):
        for c in self.parent.corpus:
            c.setup_frame.grid_remove()

    def add_corpus(self):
        self.hide_all_corpora()
        n = len(self.parent.corpus)
        if n >= len(self.default_colors):
            color = "silver"  # for everything outside default colors, user can change it
        else:
            color = self.default_colors[n]
        corpus = corpora.Corpus(self.parent, n, color)
        self.parent.corpus.append(corpus)
        self.listbox.insert("end", corpus.name_var.get())
        corpus.draw_setup_ui()
        self.visible_n = n
        corpus.draw_conc_ui()
