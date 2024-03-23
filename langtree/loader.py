import json
from typing import Sequence, Mapping, Any
from pandas import read_table

from langtree import Node
from langtree.paths import paths

def load_json(fp=None):
    if fp is None:
        fp = paths.default_node_tree
    with open(fp, "r") as f:
        return json.load(f)

def load_paths(fp=None):
    if fp is None:
        fp = paths.language_paths
    with open(fp, "r") as f:
        return [el.replace('\n', '') for el in f.readlines()]

def load_tree(fp=None):
    return create_tree(load_json(fp=fp))

def load_iso639_3(fp=None):
    if fp is None:
        fp = paths.iso639_3
    return read_table(fp, index_col = 0, encoding = 'utf-8', na_values = "")

def create_tree(data: Sequence[Any] | Mapping[str, Any]):
    if isinstance(data, list):
        return [create_tree(el) for el in data]
    if isinstance(data, dict):
        if not len(data) == 1:
            raise ValueError(
                f"If data is a dict, must be of len 1, not {len(data)}"
            )
        key, val = list(data.items())[0]
        if not isinstance(val, (list, tuple)):
            raise TypeError(
                f"If data is a dict, value must be of type list, not {type(data)}"
            )
        return Node(key, [create_tree(el) for el in val])
    if isinstance(data, str):
        return Node(data)
    raise TypeError(
        f"data must be of type list, tuple, dict or str, not {type(data)}"
    )
