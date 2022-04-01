from copy import deepcopy, copy
import os
from helper import *

class NodeSet:
    def __init__(self, nodes, paths = None):
        assert isinstance(nodes, list) or isinstance(nodes, Node)
        assert isinstance(paths, list) or isinstance(paths, str) or paths is None
        assert all([isinstance(el, Node) for el in nodes])

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
            for node, path in zip(self._nodes, self._paths):
                output += "{:>52s}    {:<40s}\n".format(node.__repr__(), '/'.join(path.split('/')[:-1])+'/')

        else:
            for node in self._nodes:
                output += "{:>52s}\n".format(node.__frepr__())

        return output


    def __repr__(self):
        return self.__str__()


    def __len__(self):
        return len(self._nodes)

    def __getitem__(self, key):
        assert isinstance(key, int)

        if self.has_paths:
            return self._nodes[key], self._paths[key]

        else:
            return self._nodes[key]


    def append(self, node, path = None):
        assert isinstance(node, Node)

        if self.has_paths:
            assert isinstance(path, str)
        else:
            path = None

        self._nodes.append(node)
        if self.has_paths:
            self._paths.append(path)


class Node:
    def __init__(self, name, children=None, soup=None, path=None):
        self._attrs = {}
        self._soup_txt = str(soup) if soup is not None else ""
        self.path = path

        name = name.replace('\n', '').strip()
        self._name = name
        self.__parse_info(name)

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


    def follow(self, path, omit_self = False, copy = False):
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
        #return "NODE: {} | CHILDREN_COUNT: {}".format(self._name, len(self._children))

        if self.__len__() == 0:
            name = self._name
            iso3 = self.get("iso3")
            iso2 = self.get("iso2")

            if iso2:
                return "{} ({} | {})".format(name, iso3, iso2)
            else:
                return "{} ({})".format(name, iso3)

        else:
            return "NODE: {} | CHILDREN_COUNT: {}".format(self.name, self.__len__())


    def __getitem__(self, key):
        if isinstance(key, int):
            return self._children[key]
        elif isinstance(key, slice):
            return [self._children[i] for i in range(*key.indices(self.__len__()))]
        elif isinstance(key, str):
            return self.find(key, deep=False)


    def __len__(self):
        return len(self._children)


    def find(self, query, ret_path=False, deep=True, copy=False, terminal=False, single_as_element = True):

        assert isinstance(query, str), "Argument must be str"

        query = query.lower()

        if deep:
            candidates_str = [el for el in self.paths() if query in el.lower()]
            candidates_set = set()

            for path in candidates_str:
                path_list = path.split('/')
                for i, p in enumerate(path_list):
                    if query in p.lower():
                        candidates_set.add('/'.join(path_list[:i+1]))

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

            for node, path in zip(self.nodes(terminal = True), self.paths(terminal = True)):
                if node.attrs.get('iso3') == query:
                    output = (node, path)

        elif len(query) == 2:

            for node, path in zip(self.nodes(terminal = True), self.paths(terminal = True)):
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


    def html(self, path = None):
        path = path or "file.txt"

        with open(path, "w") as f:
            f.write(self.soup.prettify())


    def __apply_to_children(self, fun):
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


    def paths(self, terminal = False):
        outp = paths_(self)

        if terminal:
            outp = [pp for pp, nn in zip(outp, nodes_(self)) if nn.is_terminal]

        return outp


    def nodes(self, terminal = False, copy = False, **kwargs):
        outp = nodes_(self)

        if terminal:
            outp = list(filter(lambda x: x.is_terminal, outp))

        for kwarg in kwargs:
            outp = list(filter(lambda x: x.attrs.get(kwarg) == kwargs[kwarg], outp))

        if copy:
            outp = deepcopy(outp)

        return outp



    def __draw_level(self, stack=[], printer=print):
        pattern = ''.join(list(map(lambda x: {False: "   ", True: "┃  "}.get(x), stack[:-1])))
        if len(stack) == 0:
            pass
        else:
            pattern += {True: "┠─ ", False: "┖─ "}.get(stack[-1])
        printer(pattern + self._name)
        for (i, child) in enumerate(self._children):

            child.__draw_level(stack=stack+[i!=len(self._children)-1], printer=printer)


    # TO BE DEPRECATED
    def terminal(self, ret_paths = False):
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



    # TO BE UPDATED
    @property
    def count_nodes(self):
        return len(self.nodes(terminal = False))

    def count_terminal(self):
        return len(self.nodes(terminal = True))

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
    def name(self):
        return self._name


    def update(self, **kwargs):
        self._attrs.update(kwargs)


    def get(self, key):
        return self._attrs.get(key)


    # TO BE DEPRECATED
    def flatten(self, last_level = False):

        output = copy(self._children)

        for child in self._children:
            output.extend(child.flatten())

        if last_level:
            output = [el for el in output if len(el) == 0]

        return output


    def tree(self, printer=print):
        self.__draw_level(printer=printer)


    def __parse_info(self, readstream, replace_name=True):
        import re
        roun = re.findall(r"\((.*?) *\)", readstream)
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
            out = re.sub(r"\((.*?) *\)", "", readstream)
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
            out = expected == self.count_terminal

        if verbose:
            if out is None:
                print("Check impossible")
            elif out is False:
                print("Result: expected - actual = {}".format(expected - self.count_terminal))

        return out


    def save(self, location = None):
        import pickle

        location = location or 'data/node_tree.pickle'

        with open(location, "wb") as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

        print("> Saved object in {}".format(os.path.abspath(location)))


    def save_json(self, location = None):
        import json

        location = location or 'data/node_tree.json'

        with open(location, "w") as f:
            json.dump(self.json(), f)

        print("> Saved json in {}".format(os.path.abspath(location)))


    def save_paths(self, kind = 'txt', location = None):
        import json

        assert isinstance(kind, str)
        kind = kind.lower()
        assert kind in ['txt', 'json'], "kind not supported"

        if kind == 'txt':
            location = location or 'data/lang_paths.txt'

            with open(location, "w") as f:
                f.write("\n".join(self.paths()))

        elif kind == 'json':
            location = location or 'data/lang_paths.json'

            with open(location, "w") as f:
                json.dump({el.split('/')[-1]: el for el in self.paths()}, f)

        print("> Saved paths ({}) in {}".format(kind, location))


    def tree_to_file(self, location = None):
        location = location or 'output/{}_tree.txt'.format(self._name)

        with open(location, "w") as f:
            self.tree(lambda x: print(x, file=f))

    def html_to_file(self, location = None):
        location = location or 'output/{}_html.txt'.format(self._name)

        with open(location, "w") as f:
            f.write(self.soup.prettify())



def nodes_(node):

    children = node.children

    if len(node) == 0:
        return [node]

    l = []

    for child in children:

        l.extend(nodes_(child))

    return l



def paths_(node):

    name = node.name.replace('/', '')
    children = node.children

    if len(node) == 0:
        return [name]

    l = []

    for child in children:

        l.extend([name + '/' + el for el in paths_(child)])

    return l


if __name__ == "__main__":
    print("'utils.py' run as script")

    a = Node("a", [Node("a{}".format(i)) for i in range(1, 8)])
    b = Node("b", [Node("b{}".format(i)) for i in range(1, 10)])
    c = Node("c", [Node("c{}".format(i)) for i in range(1, 12)])
    d = Node("d", [Node("d{}".format(i)) for i in range(1, 4)])

    b[3] = d

    z = Node("z", [a, b, Node("x"), c])
