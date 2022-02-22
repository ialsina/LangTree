from copy import deepcopy

class Node:
    def __init__(self, name, children=None):
        self.attrs = {}

        name = name.replace('\n', '').strip()
        self.name = name
        self.__parse_info(name)
        if isinstance(children, list):
            if len(children) == 0:
                self._children = []
                self.is_terminal = True
            else:
                self.__assert(*children)
                self._children = children
                self.is_terminal = False

        elif children is None:
            self._children = []
            self.is_terminal = True

        else:
            raise TypeError("Argument 'children' must be list or None.")


    def add(self, *children):
        self.__assert(*children)
        self._children.extend(children)

    def __repr__(self):
        return "NODE: {} | CHILDREN_COUNT: {}".format(self.name, len(self._children))

    def __getitem__(self, ind):
        if isinstance(ind, int):
            return self._children[ind]
        elif isinstance(ind, str):
            return self.find(ind)

    def __len__(self):
        return len(self._children)

    def find(self, query, deep=False):
        if deep:
            raise NotImplementedError

        if isinstance(query, str):
            query = query.lower()
            for child in self._children:
                if child.name.lower() == query:
                    return child
            for child in self._children:
                if query in child.name.lower():
                    return child
            return None

        else:
            raise TypeError("Argument must be str")

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
            return self.name
        else:
            return {self.name: [child.json() for child in self._children]}

    def __draw_level(self, stack=[]):
        pattern = ''.join(list(map(lambda x: {False: "   ", True: "┃  "}.get(x), stack[:-1])))
        if len(stack) == 0:
            pass
        else:
            pattern += {True: "┠─ ", False: "┖─ "}.get(stack[-1])
        print(pattern + self.name)
        #print("┃  "*(stack-1) + ("┠─ " + self.name if stack else self.name))
        for (i, child) in enumerate(self._children):

            child.__draw_level(stack=stack+[i!=len(self._children)-1])

    @property
    def terminal(self):
        return list(filter(lambda x: x.is_terminal, self.flatten()))

    @property
    def count_nodes(self):
        return len(self.flatten())

    @property
    def count_terminal(self):
        return len(self.terminal)

    @property
    def count_children(self):
        return self.__len__()    

    @property
    def children(self):
        return self._children


    def flatten(self):

        output = deepcopy(self._children)

        for child in self._children:
            output.extend(child.flatten())

        return output

    def tree(self):

        self.__draw_level()

    def __parse_info(self, readstream, replace_name=True):
        import re
        roun = re.findall(r"\((.*?) *\)", readstream)
        squa = re.findall(r"\[(.*?) *\]", readstream)

        if len(squa) == 0:
            if len(roun) == 1:
                if roun[0].isnumeric():
                    self.attrs["exp_len"] = int(roun[0])

        elif len(squa) == 1:
            if len(roun) == 1:
                if "A language of " in roun[0]:
                    self.attrs["country"] = roun[0].replace("A language of ", "")

            if len(squa) == 3:
                self.attrs["iso3"] = squa[0]

        if replace_name:
            out = re.sub(r"\((.*?) *\)", "", readstream)
            out = re.sub(r"\[(.*?) *\]", "", out)
            self.name = out


    def check(self, verbose=False):
        expected = self.attrs.get("exp_len")
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







if __name__ == "__main__":
    a = Node("a", [Node("a{}".format(i)) for i in range(1, 8)])
    b = Node("b", [Node("b{}".format(i)) for i in range(1, 10)])
    c = Node("c", [Node("c{}".format(i)) for i in range(1, 12)])
    d = Node("d", [Node("d{}".format(i)) for i in range(1, 4)])

    b[3] = d

    z = Node("z", [a, b, Node("x"), c])