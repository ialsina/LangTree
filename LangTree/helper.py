from ete3 import Tree as EteTree

class ParsingError(Exception):
    def __init__(self, variable, length=None, soup=None):
        self.variable = variable
        self.length = length
        self.soup = soup
        self.base_msg = "PARSING ERROR OCCURRED"
        super().__init__(self.base_msg)

    def __str__(self):
        return self.msg

    @property
    def msg(self):
        m = self.base_msg
        m += '\n\t>>> {}'.format(self.variable)

        if self.length is not None:
            m += '\n\t\t has length {}'.format(self.length)

        if self.soup is not None:
            m += '\n\nHTML:\n' + self.soup.prettify()

        return m


class BadPathError(Exception):
    def __init__(self, path=None):
        self.path = path
        self.base_msg = "INVALID PATH"

    def __str__(self):
        return self.msg

    @property
    def msg(self):
        m = self.base_msg

        if self.path:
            m += '\n\t>>> {}'.format(self.path)

        return m
    



class DebugStop(Exception):
    pass

class EmptyR1Error(Exception):
    pass

class FullR1Error(Exception):
    pass

class Container:
    def __init__(self):
        from collections import defaultdict
        self.__d = defaultdict(dict)

    def __getitem__(self, item):
        return self.__d[item]

    def __setitem__(self, item, value):
        self.__d[item] = value

    def keys(self, item, sort=True):
        out = list(self.__d.get(item).keys())
        if sort:
            out = sorted(out)
        return out


    def apply(self, func, elem):
        raise NotImplementedError



class Debug:
    def __init__(self):
        from collections import defaultdict
        self.d = defaultdict(list)
        self.slots = dict()
        self.cur = None


    def pretty(self):
        print(self.h.prettify())

    def launch(self):
        import webbrowser
        if hasattr(self, 'path'):
            return webbrowser.open(self.path)
        else:
            return False

    def to_file(self, attr, pretty = True):
        target = getattr(self, attr)

        if isinstance(target, list):
            if pretty:
                target = [el.prettify() for el in target]
            for i in range(len(target)):
                f = open('file{}.txt'.format(i), "w")
                print(target[i], file=f)
                f.close()

        else:
            if pretty:
                target = target.prettify()
            f = open('file.txt', 'w')
            print(target, file=f)
            f.close()

    def __setitem__(self, slot_id, value):
        if self.slots.get(slot_id) is None:
            self.slots[slot_id] = value

    def __getitem__(self, slot_id):
        return self.slots.get(slot_id)





class Counter:

    def __init__(self):
        from collections import defaultdict
        self.__counter = defaultdict(lambda: 0)

    def update(self, inp):
        self.__counter[inp] += 1

    def counts(self):
        return dict(self.__counter)

    def __getitem__(self, item):
        return self.counts().get(item, 0)

    def reset(self):
        self.__init__()


def path2name(path):
    return path.replace('html', '').replace('/', '').replace('.', '')


def to_tuple(inp):

    if isinstance(inp, dict):
        if len(inp) == 1:
            key, val = list(inp.items())[0]
            return (key, to_tuple(val))

        else:
            print("dict len larger than 1")

    elif isinstance(inp, list):
        return tuple([to_tuple(el) for el in inp])

    elif isinstance(inp, str):
        return inp


def to_newick_inner(inp):

    if isinstance(inp, dict):
        assert len(inp) == 1, "dict len larger than 1"
        key, val = list(inp.items())[0]
        return strtuple(to_newick_inner(val)) + key

    elif isinstance(inp, list):
        return tuple([to_newick_inner(el) for el in inp])

    elif isinstance(inp, str):
        return inp.replace(",", "_").replace(")", ">").replace("(", "<")

    else:
        raise AssertionError("inp of invalid type: {}".format(inp.__class__.__name__))


def to_newick(inp):
    newick = to_newick_inner(inp)
    assert isinstance(newick, str), "newick is of type {}".format(newick.__class__.__name__)
    return newick + ";"

def strtuple(tup):
    return str(tup).replace("'", "").replace(",)", ")")

def to_ete_tree(json, verbose=False):
    newick = to_newick(json)

    try:
        etetree = EteTree(newick, format=1)

    except Exception as e:
        if verbose:
            print("Exception raised when constructing EteTree:\n{}\n"
                  "Returning newick instead.".format(e))

        return newick

    for node in etetree.traverse():
        node.name = node.name.replace("_", ",").replace("<", "(").replace(">", ")")

    return etetree

