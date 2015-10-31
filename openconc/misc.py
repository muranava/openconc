import re
import os
import tkinter as tk


def tokenize_str(s, word_chars="0-9A-Za-z\-'_"):
    not_word_chars = "[^{0}]+".format(word_chars)
    tokens = re.split(r'{0}'.format(not_word_chars), s)
    tokens = [_t for _t in tokens if _t]
    return tokens


def make_dir(dir_path):
    """ makes sure directory exists, creating it if necessary"""
    try:
        os.makedirs(dir_path)
        return True
    except OSError:
        if os.path.exists(dir_path):
            return True
        else:
            return False


def get_tk_vars(variables):
    """
    using the .get() of tk.IntVar() & tk.StringVar
    """
    rv = {}
    for v in variables:
        try:
            rv[v] = variables[v].get()

        except AttributeError:
            pass
    return rv

def disable_all_in_frame(frame):
   for child in frame.winfo_children():
        try:
            child["state"] = "disabled"
        except tk.TclError:
            pass

def enable_all_in_frame(frame):
   for child in frame.winfo_children():
        try:
            child["state"] = "normal"
        except tk.TclError:
            pass

def pad_children(parent, x=5, y=5):
    for child in parent.winfo_children():
        try:
            child.grid_configure(padx=x, pady=y)
        except tk.TclError:
            pass


def normalize_filename(s):
    s = "".join([c if c.isalnum() else "_" for c in s])
    return s
