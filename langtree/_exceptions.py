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
