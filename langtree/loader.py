import json
from pandas import read_table

from langtree import Node
from langtree.paths import paths

def load_paths(fp=None):
    if fp is None:
        fp = paths.default_language_paths_txt
    with open(fp, "r", encoding="utf-8") as f:
        return [el.replace('\n', '') for el in f.readlines()]

def load_tree(fp=None):
    if fp is None:
        fp = paths.default_node_tree
    with open(fp, "r", encoding="utf-8") as f:
        return Node.from_json(json.load(f))

def load_iso639_3(fp=None):
    if fp is None:
        fp = paths.iso639_3
    return read_table(fp, index_col = 0, encoding = 'utf-8', na_values = "")
