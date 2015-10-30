import tkinter as tk
from tkinter import ttk
from configparser import SafeConfigParser
from openconc import misc
import os


class SettingsFrame(tk.Frame):
    def __init__(self, parent,  *args, **kwargs):
        tk.Frame.__init__(self)
        self.parent = parent
        self.check_config()
        self.load_config()
        self.draw_ui()

    def draw_ui(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.book = ttk.Notebook(self)
        self.book.grid(column=0, row=0, sticky="nesw")
        self.file_frame = ttk.Frame(self)
        self.definition_frame = ttk.Frame(self)
        self.frequency_frame = ttk.Frame(self)
        self.concordance_frame = ttk.Frame(self)
        self.xml_frame = ttk.Frame(self)
        self.book.add(self.file_frame, text="File")
        self.book.add(self.definition_frame, text="Definition")
        self.book.add(self.concordance_frame, text="Concordance")
        self.book.add(self.xml_frame, text="XML")
        # --- definition --- #
        self.definition_frame.columnconfigure(0, weight=0)
        self.definition_frame.columnconfigure(1, weight=1)
        self.word_regex_entry = ttk.Entry(self.definition_frame,
                                          textvariable=self.definition['WordRegex'])
        ttk.Label(self.definition_frame, text="Word definition (regular expression)",
                  font="verdana 10").grid(row=0, column=0, sticky="news")
        self.word_regex_entry.grid(row=0, column=1, sticky="news")
        self.word_set_entry = ttk.Entry(self.definition_frame,
                                        textvariable=self.definition['WordSet'])
        ttk.Label(self.definition_frame, text="Word definition (characters)",
                  font="verdana 10").grid(row=1, column=0, sticky="news")
        self.word_set_entry.grid(row=1, column=1, sticky="news")
        ttk.Separator(self.definition_frame, orient="horizontal").grid(row=2, column=0,
                                                                       columnspan=2, sticky="news")
        self.pos_delimiter_entry = ttk.Entry(self.definition_frame, style="Small.TEntry", width=2,
                                             textvariable=self.definition['POSDelim'])
        ttk.Label(self.definition_frame, text="Part-of-speech tag delimiter",
                  font="verdana 10").grid(row=3, column=0, sticky="news")
        self.pos_delimiter_entry.grid(row=3, column=1, sticky="nws")
        # --- file --- #
        self.file_frame.columnconfigure(0, weight=0)
        self.file_frame.columnconfigure(1, weight=1)
        self.file_frame.columnconfigure(2, weight=0)
        self.input_entry = ttk.Entry(self.file_frame, textvariable=self.file['InputDir'])
        self.input_button = ttk.Button(self.file_frame, text="Browse", command=self.browse_input,
                                       style="Small.TButton")
        ttk.Label(self.file_frame, text="Default corpus file extension",
                  font="verdana 10").grid(row=0, column=0, sticky="news")
        ttk.Label(self.file_frame, text="Default corpus directory",
                  font="verdana 10").grid(row=1, column=0, sticky="news")
        self.input_entry.grid(row=1, column=1, sticky="news")
        self.input_button.grid(row=1, column=2, sticky="news")
        self.output_entry = ttk.Entry(self.file_frame, textvariable=self.file['OutputDir'])
        self.output_button = ttk.Button(self.file_frame, text="Browse", command=self.browse_output,
                                        style="Small.TButton")
        ttk.Label(self.file_frame, text="Default output directory",
                  font="verdana 10").grid(row=2, column=0, sticky="news")
        self.output_entry.grid(row=2, column=1, sticky="news")
        self.output_button.grid(row=2, column=2, sticky="news")
        ttk.Separator(self.file_frame, orient="horizontal").grid(row=3, column=0,
                                                                 columnspan=3, sticky="news")
        self.csv_delim_entry = ttk.Entry(self.file_frame, width=2,
                                         textvariable=self.file['CSVDelim'])
        ttk.Label(self.file_frame, text="CSV delimiter",
                  font="verdana 10").grid(row=4, column=0, sticky="news")
        self.csv_delim_entry.grid(row=4, column=1, sticky="nws")
        self.csv_quote_entry = ttk.Entry(self.file_frame, width=2,
                                         textvariable=self.file['CSVQuote'])
        ttk.Label(self.file_frame, text="CSV quote character",
                  font="verdana 10").grid(row=5, column=0, sticky="news")
        self.csv_quote_entry.grid(row=5, column=1, sticky="nws")
        # --- XML --- #
        self.xml_frame.columnconfigure(0, weight=0)
        self.xml_frame.columnconfigure(1, weight=1)
        self.as_text_check = ttk.Checkbutton(self.xml_frame, text="Treat XML files as plaintext",
                                             variable=self.xml['TreatXMLAsText'])
        self.as_text_check.grid(row=0, column=0, sticky="news")
        self.text_nodes_check = ttk.Checkbutton(self.xml_frame, text="Search all text elements",
                                                variable=self.xml['SearchAllTextNodes'])
        self.text_nodes_check.grid(row=1, column=0, sticky="news")
        self.specified_nodes_entry = ttk.Entry(self.xml_frame,
                                               textvariable=self.xml['SearchSpecificNodes'])
        ttk.Label(self.xml_frame, text="Search only specified elements",
                  font="verdana 10").grid(row=2, column=0, sticky="news")
        self.specified_nodes_entry.grid(row=2, column=1, sticky="news")
        # --- concordance --- #
        self.concordance_frame.columnconfigure(0, weight=0)
        self.concordance_frame.columnconfigure(1, weight=0)
        self.concordance_frame.columnconfigure(2, weight=0)
        self.concordance_frame.columnconfigure(3, weight=0)
        self.context_left_entry = ttk.Entry(self.concordance_frame, width=3,
                                            textvariable=self.concordance['ContextLeft'])
        ttk.Label(self.concordance_frame, text="Context left",
                  font="verdana 10").grid(row=0, column=0, sticky="news")
        self.context_left_entry.grid(row=0, column=1, sticky="nws")
        self.context_right_entry = ttk.Entry(self.concordance_frame, width=3,
                                             textvariable=self.concordance['ContextRight'])
        ttk.Label(self.concordance_frame, text="Context right",
                  font="verdana 10").grid(row=0, column=2, sticky="news")
        self.context_right_entry.grid(row=0, column=3, sticky="nws")
        ttk.Label(self.concordance_frame, text="Context unit",
                  font="verdana 10").grid(row=0, column=4, sticky="news")
        self.unit_combo = ttk.Combobox(self.concordance_frame,
                                       textvariable=self.concordance['ContextUnit'],
                                       values=["Characters", "Words"], state="readonly")
        self.unit_combo["width"] = 8
        self.unit_combo.grid(row=0, column=5, sticky="news")
        self.conc_case_check = ttk.Checkbutton(self.concordance_frame, text="Case sensitive",
                                               variable=self.concordance['Case'])
        self.conc_case_check.grid(row=4, column=0, sticky="news", columnspan=2)
        self.regex_check = ttk.Checkbutton(self.concordance_frame, text="Regular expression",
                                           variable=self.concordance['IsRegEx'])
        self.regex_check.grid(row=4, column=2, sticky="news", columnspan=2)
        self.conc_pos_check = ttk.Checkbutton(self.concordance_frame,
                                              text="Ignore Part-of-speech tags",
                                              variable=self.concordance['IgnorePOS'])
        self.conc_pos_check.grid(row=5, column=0, sticky="news", columnspan=2)
        self.conc_xml_check = ttk.Checkbutton(self.concordance_frame, text="Ignore XML tags",
                                              variable=self.concordance['IgnoreXML'])
        self.conc_xml_check.grid(row=5, column=2, sticky="news", columnspan=2)
        misc.pad_children(self.file_frame, 5, 5)
        misc.pad_children(self.definition_frame, 5, 5)
        misc.pad_children(self.xml_frame, 5, 5)
        misc.pad_children(self.concordance_frame, 5, 5)

    def browse_input():
        pass

    def browse_output():
        pass

    def write_default_config(self):
        self.config.add_section("File")
        self.config.set("File", "CSVDelim", ",")
        self.config.set("File", "CSVQuote", '"')
        self.config.set("File", "InputDir", "")
        self.config.set("File", "OutputDir", "")
        self.config.set("File", "Extension", ".txt")
        self.config.add_section("Definition")
        self.config.set("Definition", "WordRegex", "0-9A-Za-z\-\'_")
        self.config.set("Definition", "WordSet", "")
        self.config.set("Definition", "POSDelim", "_")
        self.config.add_section("Frequency")
        self.config.set("Frequency", "Case", "0")
        self.config.set("Frequency", "STTR", "0")
        self.config.set("Frequency", "STTRInterval", "1000")
        self.config.set("Frequency", "IgnorePOS", "1")
        self.config.set("Frequency", "IgnoreXML", "1")
        self.config.set("Frequency", "NormalizeTo", "1000000")
        self.config.add_section("Concordance")
        self.config.set("Concordance", "Case", "0")
        self.config.set("Concordance", "IgnorePOS", "1")
        self.config.set("Concordance", "IgnoreXML", "1")
        self.config.set("Concordance", "IsRegEx", "1")
        self.config.set("Concordance", "ContextLeft", "60")
        self.config.set("Concordance", "ContextRight", "60")
        self.config.set("Concordance", "ContextUnit", "Characters")
        self.config.add_section("XML")
        self.config.set("XML", "TreatXMLAsText", "1")
        self.config.set("XML", "SearchAllTextNodes", "0")
        self.config.set("XML", "SearchSpecificNodes", "")
        with open(self.config_path, 'w') as f:
            self.config.write(f)

    def check_config(self):
        self.config_path = os.path.join(self.parent.base_dir, "config.ini")
        self.config = SafeConfigParser()
        self.config.optionxform = str
        self.config.read(self.config_path)
        if not os.path.exists(self.config_path):
            self.write_default_config()

    def get_current_settings(self):
        pass

    def load_config(self):
        """ Load config settings into tk variables """
        g = dict(self.config.items('File'))
        d = dict(self.config.items('Definition'))
        f = dict(self.config.items('Frequency'))
        c = dict(self.config.items('Concordance'))
        x = dict(self.config.items('XML'))
        self.file = {}
        self.frequency = {}
        self.definition = {}
        self.concordance = {}
        self.xml = {}
        self.definition['WordRegex'] = tk.StringVar()
        self.definition['WordRegex'].set(d['WordRegex'])
        self.definition['WordSet'] = tk.StringVar()
        self.definition['WordSet'].set(d['WordSet'])
        self.definition['POSDelim'] = tk.StringVar()
        self.definition['POSDelim'].set(d['POSDelim'])
        self.file['CSVDelim'] = tk.StringVar()
        self.file['CSVDelim'].set(g['CSVDelim'])
        self.file['CSVQuote'] = tk.StringVar()
        self.file['CSVQuote'].set(g['CSVQuote'])
        self.file['InputDir'] = tk.StringVar()
        self.file['InputDir'].set(g['InputDir'])
        self.file['OutputDir'] = tk.StringVar()
        self.file['OutputDir'].set(g['OutputDir'])
        self.file['Extension'] = tk.StringVar()
        self.file['Extension'].set(g['Extension'])
        self.concordance['Case'] = tk.IntVar()
        self.concordance['Case'].set(c['Case'])
        self.concordance['IsRegEx'] = tk.IntVar()
        self.concordance['IsRegEx'].set(c['IsRegEx'])
        self.concordance['ContextLeft'] = tk.IntVar()
        self.concordance['ContextLeft'].set(c['ContextLeft'])
        self.concordance['ContextRight'] = tk.IntVar()
        self.concordance['ContextRight'].set(c['ContextRight'])
        self.concordance['ContextUnit'] = tk.StringVar()
        self.concordance['ContextUnit'].set(c['ContextUnit'])
        self.concordance['IgnorePOS'] = tk.IntVar()
        self.concordance['IgnoreXML'] = tk.IntVar()
        self.concordance['IgnorePOS'].set(c['IgnorePOS'])
        self.concordance['IgnoreXML'].set(c['IgnoreXML'])
        self.frequency['Case'] = tk.IntVar()
        self.frequency['Case'].set(f['Case'])
        self.frequency['IgnorePOS'] = tk.IntVar()
        self.frequency['IgnoreXML'] = tk.IntVar()
        self.frequency['IgnorePOS'].set(f['IgnorePOS'])
        self.frequency['IgnoreXML'].set(f['IgnoreXML'])
        self.frequency['STTR'] = tk.IntVar()
        self.frequency['STTRInterval'] = tk.IntVar()
        self.frequency['STTR'].set(f['STTR'])
        self.frequency['STTRInterval'].set(f['STTRInterval'])
        self.frequency['NormalizeTo'] = tk.IntVar()
        self.frequency['NormalizeTo'].set(f['NormalizeTo'])
        self.xml['TreatXMLAsText'] = tk.IntVar()
        self.xml['SearchSpecificNodes'] = tk.StringVar()
        self.xml['SearchAllTextNodes'] = tk.StringVar()
        self.xml['TreatXMLAsText'].set(x['TreatXMLAsText'])
        self.xml['SearchSpecificNodes'].set(x['SearchSpecificNodes'])
        self.xml['SearchAllTextNodes'].set(x['SearchAllTextNodes'])

