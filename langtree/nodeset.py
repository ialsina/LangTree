from .core import Node

__all__ = ["NodeSet"]

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
