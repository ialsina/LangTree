from ete3 import Tree as EteTree

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
