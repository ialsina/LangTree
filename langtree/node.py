import os
import re
import json
import pickle
from collections.abc import MutableSequence
from typing import Optional
from copy import deepcopy
from functools import partial

from ._exceptions import BadPathError
from .paths import DATA_DIR, OUTPUT_DIR, paths as fpaths
from .utils import to_ete_tree
from .nodeset import NodeSet

__all__ = ["Node"]


class Node(MutableSequence):
    """Core notion of the Tree. A nodes is each instance within it.
    It can contain children, and many attributes
    """

    def __init__(self, name, children=None, path=None, soup=None, **attrs):
        if children is None:
            children = []
        if not (children is None or isinstance(children, list)):
            raise TypeError(
                f"children must be either list or None, not {type(children)}."
            )
        self._assert_children(*children)
        parsed_name, parsed_attrs = self._parse_info(name, ret_name=True)
        attrs.update(parsed_attrs)
        self.name = parsed_name
        self._children = children
        self.path = path
        self.attrs = attrs
        self.soup = self._parse_soup(soup)

    def __repr__(self):
        if self.is_language:
            name = self.name
            iso3 = self.get("iso3")
            iso2 = self.get("iso2")
            symb = (
                f"{name} ({iso3} | {iso2})" if iso2 else
                f"{name} ({iso3})"
            )
        else:
            symb = self.name
        return (
            f"NODE: {symb} | CHILDREN_COUNT: {len(self)}"
            if len(self) > 0
            else symb
        )

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._children[key]
        if isinstance(key, slice):
            return [self._children[i] for i in range(*key.indices(self.__len__()))]
        if isinstance(key, str):
            return self.find(key, deep=False)
        raise TypeError(
            f"key must be int, slice or str, not {type(key)}"
        )

    def __setitem__(self, ind, child):
        self._assert_children(child)
        if not isinstance(ind, int):
            raise ValueError
        self._children[ind] = child
    
    def __delitem__(self, key):
        del self._children[key]

    def __len__(self):
        return len(self._children)

    def _assert_children(self, *seq):
        if not all(isinstance(el, self.__class__) for el in seq):
            raise TypeError(
                f"Not all elements in input sequence belong to {self.__class__.__name__}."
            )

    def _apply_to_children(self, fun):
        return [fun(el) for el in self]

    def _get_by_key(self, key, which='paths'):
        nodes = self.nodes()
        paths = self.paths()
        if which not in ("nodes", "paths"):
            raise ValueError(
                f"'which' must be either 'nodes' or 'paths', was {which}."
            )
        keys = []
        for node in nodes:
            if hasattr(node, key):
                val = getattr(node, key)
            else:
                val = node.attrs.get(key, '')
            keys.append(val)
        if which == 'paths':
            return {k: v for k, v in zip(keys, paths) if k != ''}
        return {k: v for k, v in zip(keys, nodes) if k != ''}

    def _draw_level(self, stack=None, printer=None):
        def vert_str(x):
            return "┃  " if x else "   "
        def hor_str(x):
            return "┠─ " if x else "┖─ "
        if stack is None:
            stack = []
        if printer is None:
            printer = partial(print, end="")
        pattern = ''.join(list(map(vert_str, stack[:-1])))
        if stack:
            pattern += hor_str(stack[-1])
        printer(pattern + self.name)
        printer("\n")
        for i, child in enumerate(self._children):
            # pylint: disable=W0212
            child._draw_level(stack=stack + [i != len(self._children) - 1], printer=printer)

    @staticmethod
    def _parse_info(readstream, ret_name=True):
        attrs = {}
        roun = re.findall(r"\((.*)\)", readstream)
        squa = re.findall(r"\[(.*?) *\]", readstream)
        roun_readd = []
        if len(squa) == 0:
            if len(roun) == 1:
                if roun[0].isnumeric():
                    attrs["exp_len"] = int(roun[0])
            elif len(roun) > 1:
                for el in roun:
                    if el.isnumeric():
                        attrs["exp_len"] = int(el)
                    else:
                        roun_readd.append(el)
        elif len(squa) == 1:
            if len(roun) == 1:
                if "A language of " in roun[0]:
                    attrs["country"] = roun[0].replace("A language of ", "")
            if len(squa[0]) == 3:
                attrs["iso3"] = squa[0]
        if not ret_name:
            return attrs
        readstream = re.sub(r"\((.*)\)", "", readstream)
        readstream = re.sub(r"\[(.*?) *\]", "", readstream)
        readstream = readstream.strip()
        for el in roun_readd:
            readstream += f" ({el})"
        return readstream.strip(), attrs
    
    @staticmethod
    def _parse_soup(soup):
        if soup is None:
            return None
        from bs4 import BeautifulSoup
        if isinstance(soup, str):
            return BeautifulSoup(soup, 'soup.parser')
        if isinstance(soup, BeautifulSoup):
            return soup
        raise TypeError(
            f"Bad type for soup: {soup}"
        )

    

    def add(self, *children):
        self._assert_children(*children)
        self._children.extend(children)
        self._children = sorted(self._children, key=lambda el: el.name)
    
    def insert(self, index, value):
        self._assert_children(value)
        self._children.insert(index, value)

    def follow(self, path, omit_self=False, copy=False):
        levels = [el for el in path.split('/') if len(el) > 0]
        cur = ''
        if omit_self:
            if levels[0] == self.name:
                levels = levels[1:]
        if copy:
            output = deepcopy(self)
        else:
            output = self
        for level in levels:
            output = output.find(level, deep=False)
            cur += '/' + level
            if output is None:
                raise BadPathError(cur)
        return output

    def find(self,
             query: str,
             ret_path: Optional[bool] = False,
             deep: Optional[bool] = True,
             copy: Optional[bool] = False,
             terminal: Optional[bool] = False,
             single_as_element: Optional[bool] = True,
             ):
        if not isinstance(query, str):
            raise TypeError(
                f"query must be of type str, not {type(query)}."
            )
        query = query.lower()
        if deep:
            candidates, candidate_paths = _find_deep(self, query, copy=copy, terminal=terminal)
            if len(candidates) == 1 and single_as_element:
                candidates = candidates[0]
                candidate_paths = candidate_paths[0]
            if ret_path:
                return NodeSet(candidates, candidate_paths)
            return NodeSet(candidates)
        return _find_shallow(self, query)

    def find_iso(self, query: str, ret_path: Optional[bool] = False):
        if not isinstance(query, str):
            raise TypeError(
                f"query must be of type str, not {type(query)}"
            )
        if len(query) not in (2, 3):
            raise ValueError(
                f"Argument must be str of length 2 or 3, but was {len(query)}."
            )
        for node, path in zip(self.nodes(language=True), self.paths(language=True)):
            iso3 = node.attrs.get('iso3')
            iso2 = node.attrs.get('iso2')
            if iso3 == query or iso2 == query:
                break
        else:
            node, path = None, None
        if ret_path:
            return node, path
        return node

    def launch(self):
        import webbrowser
        if self.path is not None:
            return webbrowser.open(self.path)
        return None

    def json(self):
        return (
            {self.name: [child.json() for child in self._children]}
            if len(self._children) > 0
            else self.name
        )

    @classmethod
    def from_json(cls, data):
        if isinstance(data, list):
            return [cls.from_json(el) for el in data]
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
            return cls(key, [cls.from_json(el) for el in val])
        if isinstance(data, str):
            return cls(data)
        raise TypeError(
            f"data must be of type list, tuple, dict or str, not {type(data)}"
        )

    def ete_tree(self, verbose=False):
        return to_ete_tree(self.json(), verbose=verbose)

    def paths(self, terminal=False, language=False, key=None):
        if terminal is True and language is True:
            raise ValueError(
                "Both terminal and language cannot be True."
            )
        if key is not None:
            return self._get_by_key(key=key, which='paths')
        outp = _paths(self)
        if terminal:
            outp = [pp for pp, nn in zip(outp, _nodes(self)) if nn.is_terminal]
        elif language:
            outp = [pp for pp, nn in zip(outp, _nodes(self)) if nn.is_language]
        return outp

    def nodes(self, terminal=False, language=False, copy=False, key=None, **kwargs):
        if terminal is True and language is True:
            raise ValueError(
                "Both terminal and language cannot be True."
            )
        if key is not None:
            return self._get_by_key(key=key, which='paths')
        outp = _nodes(self)
        if copy:
            outp = deepcopy(outp)
        if terminal:
            outp = list(filter(lambda x: x.is_terminal, outp))
        elif language:
            outp = list(filter(lambda x: x.is_language, outp))
        for kw, value in kwargs.items():
            outp = [el for el in outp if el.attrs.get(kw) == value]
        return outp


    def count_nodes(self):
        return len(self.nodes(terminal=False))

    def count_terminal(self):
        return len(self.nodes(terminal=True))

    def count_children(self):
        return len(self)

    @property
    def children(self):
        return self._children

    @property
    def is_terminal(self):
        return len(self._children) == 0

    @property
    def is_language(self):
        return self.is_terminal or self.get("iso2") is not None

    def update(self, **kwargs):
        self.attrs.update(kwargs)

    def get(self, key):
        return self.attrs.get(key)

    def tree(self, printer=print):
        self._draw_level(printer=printer)

    def check(self, verbose=False):
        expected = self.attrs.get("exp_len")
        if expected is None:
            out = None
        else:
            out = expected == self.count_terminal()

        if verbose:
            if out is None:
                print("Check impossible")
            elif out is False:
                print("Result: expected - actual = {}".format(expected - self.count_terminal()))

        return out

    def save(self, filepath=None, filename=None):

        filename = _ensure_extension(filename, 'pickle') or 'node_tree.pickle'
        if filepath is None:
            filepath = DATA_DIR / filename

        with open(filepath, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

        print("> Saved object in {}".format(os.path.abspath(filepath)))

    def save_json(self, filepath=None, filename=None):

        filename = _ensure_extension(filename, 'json') or fpaths.default_node_tree
        filepath = filepath or os.path.join(DATA_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.json(), f)

        print("> Saved json in {}".format(os.path.abspath(filepath)))

    @staticmethod
    def _paths_to_str(paths, kind):
        if not kind in ("txt", "json"):
            raise ValueError(
                f"Unknown value for kind: {kind}"
            )
        if kind == 'txt':
            return _to_string(paths, sort=True)
        return json.dumps(paths)

    def save_paths(self, kind='txt', filepath=None, key=None):
        if key == 'last':
            paths = {el.split('/')[-1]: el for el in self.paths(key=None)}
        else:
            paths = self.paths(key=key)
        if filepath is None:
            filepath = (
                fpaths.default_language_paths_txt
                if kind == "txt"
                else fpaths.default_language_paths_json
            )
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(filepath, self._paths_to_str(paths=paths, kind=kind))
        print("> Saved paths ({}) in {}".format(kind, filepath))

    def tree_to_file(self, location=None):
        if location is None:
            location = OUTPUT_DIR / f"{self.name}_tree.txt"
        with open(location, "w", encoding="utf-8") as f:
            self.tree(partial(print, file=f))

    def html_to_file(self, location=None):
        if location is None:
            location = OUTPUT_DIR / f"{self.name}_html.txt"
        with open(location, "w", encoding="utf-8") as f:
            f.write(self.soup.prettify())

def _find_deep(node: Node, query: str, terminal: bool, copy: bool):
    candidates_str = [el for el in node.paths() if query in el.lower()]
    candidates_set = set()
    for path in candidates_str:
        path_list = path.split('/')
        for i, p in enumerate(path_list):
            if query in p.lower():
                candidates_set.add('/'.join(path_list[:i + 1]))
    candidates = []
    candidate_paths = list(candidates_set)
    for path in candidate_paths:
        candidates.append(node.follow(path, omit_self=True, copy=copy))
    if terminal:
        temp1, temp2 = [], []
        for cand, cand_path in zip(candidates, candidate_paths):
            if cand.is_terminal:
                temp1.append(cand)
                temp2.append(cand_path)
        candidates = temp1.copy()
        candidate_paths = temp2.copy()
        del temp1
        del temp2
    return candidates, candidate_paths

def _find_shallow(node: Node, query: str):
    for child in node:
        if child.name.lower() == query:
            return child
    for child in node:
        if query in child.name.lower():
            return child
    return None

def _nodes(node):
    children = node.children
    l = [node]
    for child in children:
        l.extend(_nodes(child))
    return l

def _paths(node):
    name = node.name.replace('/', '')
    children = node.children
    l = [name]
    for child in children:
        l.extend([name + '/' + el for el in _paths(child)])
    return l

def _to_string(inp, sort=False):
    if isinstance(inp, dict):
        list_like = ["{}: {}".format(k, v) for k, v in inp.items()]
        if sort:
            return "\n".join(sorted(list_like))
        return "\n".join(list_like)
    if isinstance(inp, list):
        if sort:
            return "\n".join(sorted(inp))
        return "\n".join(inp)
    if isinstance(inp, str):
        return inp
    raise TypeError("inp must be dict, list or str")

def _ensure_extension(filename, extension):
    if filename is None:
        return None
    assert isinstance(filename, str), "Filename must be str"
    assert isinstance(extension, str), "Extension must be str"
    if not extension.startswith('.'):
        extension = '.' + extension
    if not filename.endswith(extension):
        filename = filename + extension
    return filename

if __name__ == "__main__":
    print("'utils.py' run as script")

    a = Node("a", [Node("a{}".format(i)) for i in range(1, 8)])
    b = Node("b", [Node("b{}".format(i)) for i in range(1, 10)])
    c = Node("c", [Node("c{}".format(i)) for i in range(1, 12)])
    d = Node("d", [Node("d{}".format(i)) for i in range(1, 4)])

    b[3] = d

    z = Node("z", [a, b, Node("x"), c])
