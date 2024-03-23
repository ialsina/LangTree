from copy import deepcopy, copy
import os

from .paths import DATA_DIR, paths
from .utils import to_ete_tree
from ._exceptions import BadPathError

__all__ = ["NodeSet", "Node"]


class NodeSet:
    """Class that represents a collection of nodes,
    typically as a result of a query.
    """

    def __init__(self, nodes, paths=None):
        if not isinstance(nodes, (list, Node)):
            raise TypeError(
                f"nodes must be of type Node or list, not {type(nodes)}"
            )
        if not (isinstance(paths, (list, str)) or paths is None):
            raise TypeError(
                f"If passed, paths must be of type list, or str, not {type(paths)}"
            )
        assert all(isinstance(el, Node) for el in nodes)

        if isinstance(nodes, Node):
            nodes = [nodes]

        if isinstance(paths, str):
            paths = [paths]

        if paths is not None:
            assert len(nodes) == len(paths)

        self._nodes = nodes
        self._paths = paths
        self.has_paths = paths is not None

    def __str__(self):
        output = ""

        if self.__len__() == 0:
            return output + "* Empty *"

        if self.has_paths:
            for i, (node, clean_path) in enumerate(zip(self._nodes, self.clean_paths)):
                output += "{:>2d}. {:>52s}    {:<40s}\n".format(i + 1, node.__repr__(), clean_path)

        else:
            for i, node in enumerate(self._nodes):
                output += "{:>2d}. {:>52s}\n".format(i + 1, node.__repr__())

        return output

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self._nodes)

    def __getitem__(self, key):
        if not isinstance(key, int):
            raise TypeError("NodeSet indices must be integers, not {}".format(type(key).__name__))

        if not (abs(key) >= 1 and abs(key) <= self.__len__()):
            raise IndexError("NodeSet index out of range")
            # raise IndexError("NodeSet index must be between 1 and {:d}".format(self.__len__()))

        if key > 0:
            key -= 1  # Nummeration from 1 (instead of 0). For negative indices, no change
        if self.has_paths:
            return self._nodes[key], self._paths[key]
        else:
            return self._nodes[key]

    def append(self, node, path=None):
        assert isinstance(node, Node)

        if self.has_paths:
            assert isinstance(path, str)
        else:
            path = None

        self._nodes.append(node)
        if self.has_paths:
            self._paths.append(path)

    @property
    def nodes(self):
        return self._nodes

    @property
    def paths(self):
        return self._paths

    @property
    def clean_paths(self):
        return ['/'.join(path.split('/')[:-1]) + '/' for path in self._paths]


class Node:
    """Core notion of the Tree. A nodes is each instance within it.
    It can contain children, and many attributes
    """

    def __init__(self, name, children=None, soup=None, path=None, **attrs):
        self._attrs = {}
        self._soup_txt = str(soup) if soup is not None else ""
        self.path = path

        name = name.replace('\n', '').strip()
        self._name = name
        self._parse_info(name)

        if attrs is not None:
            self.update(**attrs)

        if isinstance(children, list):
            if len(children) == 0:
                self._children = []
            else:
                self.__assert(*children)
                self._children = children

        elif children is None:
            self._children = []

        else:
            raise TypeError("Argument 'children' must be list or None.")

    def add(self, *children):
        self.__assert(*children)
        self._children.extend(children)
        self._children = sorted(self._children, key=lambda el: el.name)

    def follow(self, path, omit_self=False, copy=False):
        levels = [el for el in path.split('/') if len(el) > 0]
        cur = ''

        if omit_self:
            if levels[0] == self._name:
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

    def __repr__(self):
        # return "NODE: {} | CHILDREN_COUNT: {}".format(self._name, len(self._children))

        if self.is_language:
            name = self._name
            iso3 = self.get("iso3")
            iso2 = self.get("iso2")

            if iso2:
                symb = "{} ({} | {})".format(name, iso3, iso2)
            else:
                symb = "{} ({})".format(name, iso3)

        else:
            symb = self.name

        if self.__len__() == 0:
            return symb

        else:
            return "NODE: {} | CHILDREN_COUNT: {}".format(symb, self.__len__())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._children[key]
        elif isinstance(key, slice):
            return [self._children[i] for i in range(*key.indices(self.__len__()))]
        elif isinstance(key, str):
            return self.find(key, deep=False)

    def __len__(self):
        return len(self._children)

    def find(self, query, ret_path=False, deep=True, copy=False, terminal=False, single_as_element=True):

        assert isinstance(query, str), "Argument must be str"

        query = query.lower()

        if deep:
            candidates_str = [el for el in self.paths() if query in el.lower()]
            candidates_set = set()

            for path in candidates_str:
                path_list = path.split('/')
                for i, p in enumerate(path_list):
                    if query in p.lower():
                        candidates_set.add('/'.join(path_list[:i + 1]))

            candidates = []
            candidate_paths = list(candidates_set)

            for path in candidate_paths:
                candidates.append(self.follow(path, omit_self=True, copy=copy))

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

            if len(candidates) == 1 and single_as_element:
                candidates = candidates[0]
                candidate_paths = candidate_paths[0]

            if ret_path:
                return NodeSet(candidates, candidate_paths)

            else:
                return NodeSet(candidates)

        else:
            for child in self._children:
                if child.name.lower() == query:
                    return child
            for child in self._children:
                if query in child.name.lower():
                    return child
            return None

    def find_iso(self, query, ret_path=False, copy=False):

        assert isinstance(query, str), "Argument must be str"
        assert len(query) in [2, 3], "Argument must be str of length 2 or 3"

        output = (None, None)

        if len(query) == 3:

            for node, path in zip(self.nodes(language=True), self.paths(language=True)):
                if node.attrs.get('iso3') == query:
                    output = (node, path)

        elif len(query) == 2:

            for node, path in zip(self.nodes(language=True), self.paths(language=True)):
                if node.attrs.get('iso2') == query:
                    output = (node, path)

        if ret_path:
            return output

        else:
            return output[0]

    @property
    def soup(self):
        from bs4 import BeautifulSoup
        return BeautifulSoup(self._soup_txt, 'html.parser')

    def launch(self):
        import webbrowser
        if self.path is not None:
            return webbrowser.open(self.path)
        else:
            return False

    def html(self, path=None):
        path = path or "file.txt"

        with open(path, "w") as f:
            f.write(self.soup.prettify())

    def _apply_to_children(self, fun):
        return [fun(el) for el in self._children]

    def __setitem__(self, ind, child):
        self.__assert(child)
        if not isinstance(ind, int):
            raise ValueError
        self._children[ind] = child

    def __assert(self, *seq):
        if not all(isinstance(el, __class__) for el in seq):
            raise TypeError("Not all elements in input sequence belong to {}.".format(__class__))

    def json(self):
        if len(self._children) == 0:
            return self._name
        else:
            return {self._name: [child.json() for child in self._children]}

    def ete_tree(self, verbose=False):
        return to_ete_tree(self.json(), verbose=verbose)

    def paths(self, terminal=False, language=False, key=None):
        assert not (terminal and language), "Both terminal and language cannot be True"

        if key:
            return self._get_by_key(key=key, which='paths')

        outp = _paths(self)

        if terminal:
            outp = [pp for pp, nn in zip(outp, _nodes(self)) if nn.is_terminal]


        elif language:
            outp = [pp for pp, nn in zip(outp, _nodes(self)) if nn.is_language]

        return outp

    def nodes(self, terminal=False, language=False, copy=False, key=None, **kwargs):
        if key:
            return self._get_by_key(key=key, which='paths')

        outp = _nodes(self)

        if terminal:
            outp = list(filter(lambda x: x.is_terminal, outp))

        elif language:
            outp = list(filter(lambda x: x.is_language, outp))

        for kw, value in kwargs.items():
            outp = list(filter(lambda x: x.attrs.get(kw) == value, outp))

        if copy:
            outp = deepcopy(outp)

        return outp

    def _get_by_key(self, key, which='paths'):
        nodes = self.nodes()
        paths = self.paths()

        assert which in ['paths', 'nodes'], "'which' must be either 'nodes' or 'paths'"

        keys = []
        for nn in nodes:
            try:
                val = getattr(nn, key)
            except AttributeError:
                val = nn.attrs.get(key, '')
            keys.append(val)

        if which == 'paths':
            return {k: v for k, v in zip(keys, paths) if k != ''}
        elif which == 'nodes':
            return {k: v for k, v in zip(keys, nodes) if k != ''}

    def __draw_level(self, stack=[], printer=print):
        pattern = ''.join(list(map(lambda x: {False: "   ", True: "┃  "}.get(x), stack[:-1])))
        if len(stack) == 0:
            pass
        else:
            pattern += {True: "┠─ ", False: "┖─ "}.get(stack[-1])
        printer(pattern + self._name)
        for (i, child) in enumerate(self._children):
            child.__draw_level(stack=stack + [i != len(self._children) - 1], printer=printer)

    # TO BE DEPRECATED
    def terminal(self, ret_paths=False):
        if not ret_paths:
            return list(filter(lambda x: x.is_terminal, self.flatten()))

        else:
            paths, nodes = self.paths(), self.nodes()
            filtered_paths = []
            filtered_nodes = []

            for path, node in zip(paths, nodes):
                if node.is_terminal:
                    filtered_paths.append(path)
                    filtered_nodes.append(node)

            return filtered_nodes, filtered_paths

    def count_nodes(self):
        return len(self.nodes(terminal=False))

    def count_terminal(self):
        return len(self.nodes(terminal=True))

    def count_children(self):
        return self.__len__()

    @property
    def children(self):
        return self._children

    @property
    def attrs(self):
        return self._attrs

    @property
    def is_terminal(self):
        return len(self._children) == 0

    @property
    def is_language(self):
        return self.is_terminal or self.get("iso2") is not None

    @property
    def name(self):
        return self._name

    def update(self, **kwargs):
        self._attrs.update(kwargs)

    def get(self, key):
        return self._attrs.get(key)

    # TO BE DEPRECATED
    def flatten(self, last_level=False):

        output = copy(self._children)

        for child in self._children:
            output.extend(child.flatten())

        if last_level:
            output = [el for el in output if len(el) == 0]

        return output

    def tree(self, printer=print):
        self.__draw_level(printer=printer)

    def _parse_info(self, readstream, replace_name=True):
        import re
        # https://stackoverflow.com/questions/15864800/
        # searching-for-outermost-parentheses-using-python-regex
        roun = re.findall(r"\((.*)\)", readstream)
        squa = re.findall(r"\[(.*?) *\]", readstream)
        roun_readd = []

        if len(squa) == 0:
            if len(roun) == 1:
                if roun[0].isnumeric():
                    self._attrs["exp_len"] = int(roun[0])

            elif len(roun) > 1:
                for el in roun:
                    if el.isnumeric():
                        self._attrs["exp_len"] = int(el)
                    else:
                        roun_readd.append(el)

        elif len(squa) == 1:
            if len(roun) == 1:
                if "A language of " in roun[0]:
                    self._attrs["country"] = roun[0].replace("A language of ", "")

            if len(squa[0]) == 3:
                self._attrs["iso3"] = squa[0]

        if replace_name:
            out = re.sub(r"\((.*)\)", "", readstream)
            out = re.sub(r"\[(.*?) *\]", "", out)
            out = out.strip()

            for el in roun_readd:
                out += " ({})".format(el)

            self._name = out.strip()

    def check(self, verbose=False):
        expected = self._attrs.get("exp_len")
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
        import pickle

        filename = _ensure_extension(filename, 'pickle') or 'node_tree.pickle'
        filepath = filepath or os.path.join(DATA_DIR, filename)

        with open(filepath, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

        print("> Saved object in {}".format(os.path.abspath(filepath)))

    def save_json(self, filepath=None, filename=None):
        import json

        filename = _ensure_extension(filename, 'json') or paths.default_node_tree
        filepath = filepath or os.path.join(DATA_DIR, filename)

        with open(filepath, "w") as f:
            json.dump(self.json(), f)

        print("> Saved json in {}".format(os.path.abspath(filepath)))

    def save_paths(self, kind='txt', filepath=None, filename=None, key=None):
        import json

        assert isinstance(kind, str)
        kind = kind.lower()
        assert kind in ['txt', 'json'], "kind not supported"

        filename = filename or "paths"

        if key == 'last':
            paths = {el.split('/')[-1]: el for el in self.paths(key=None)}
        else:
            paths = self.paths(key=key)

        if kind == 'txt':
            filepath = filepath or os.path.join(DATA_DIR, _ensure_extension(filename, 'txt'))
            with open(filepath, "w") as f:
                f.write(_to_string(paths, sort=True))

        elif kind == 'json':
            filepath = filepath or os.path.join(DATA_DIR, _ensure_extension(filename, 'json'))
            with open(filepath, "w") as f:
                json.dump(paths, f)

        print("> Saved paths ({}) in {}".format(kind, filepath))

    def tree_to_file(self, location=None):
        location = location or 'output/{}_tree.txt'.format(self._name)

        with open(location, "w") as f:
            self.tree(lambda x: print(x, file=f))

    def html_to_file(self, location=None):
        location = location or 'output/{}_html.txt'.format(self._name)

        with open(location, "w") as f:
            f.write(self.soup.prettify())


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
        else:
            return "\n".join(list_like)
    elif isinstance(inp, list):
        if sort:
            return "\n".join(sorted(inp))
        else:
            return "\n".join(inp)
    elif isinstance(inp, str):
        return inp
    else:
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
