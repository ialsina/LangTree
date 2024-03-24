from collections.abc import Sequence

__all__ = ["NodeSet"]

class NodeSet(Sequence):
    """Class that represents a collection of nodes,
    typically as a result of a query.
    """

    def __init__(self, nodes, paths=None):
        nodes = self._normalize_nodes(nodes)
        if paths is not None:
            paths = self._normalize_paths(paths)
            if len(nodes) != len(paths):
                raise ValueError(
                    f"Lengths of nodes and paths must match (they were {len(nodes)} and {len(paths)})."
                )
        self._nodes = nodes
        self._paths = paths
    
    @staticmethod
    def _normalize_nodes(nodes):
        from .node import Node # pylint: disable=C0415
        if isinstance(nodes, Node):
            return [nodes]
        if isinstance(nodes, list):
            if all(isinstance(element, Node) for element in nodes):
                return nodes
            raise ValueError(
                "If passed as list, all elements of node must be of type Node."
            )
        raise TypeError(
            f"node must be of type Node, not {type(nodes)}."
        )
    
    @staticmethod
    def _normalize_paths(paths):
        if isinstance(paths, str):
            return [paths]
        if isinstance(paths, list):
            if all(isinstance(element, str) for element in paths):
                raise ValueError(
                    "If passed as list, all elements of path must be of type str."
                )
            return paths
        raise TypeError(
            f"path must be of type Node, not {type(paths)}."
        )

    def __str__(self):
        output = ""

        if len(self) == 0:
            return output + "* Empty *"

        if self.has_paths:
            for i, (node, clean_path) in enumerate(zip(self._nodes, self.clean_paths)):
                output += "{:>2d}. {:>52s}    {:<40s}\n".format(i + 1, node.__repr__(), clean_path)

        else:
            for i, node in enumerate(self._nodes):
                output += "{:>2d}. {:>52s}\n".format(i + 1, node.__repr__())

        return output

    def __repr__(self):
        return str(self)

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
        node = self._normalize_nodes(node)
        self._nodes.extend(node)
        if self.has_paths:
            if not isinstance(path, str):
                raise TypeError(
                    f"path must be str, not {type(path)}"
                )
            self._paths.append(path)

    @property
    def nodes(self):
        return self._nodes

    @property
    def paths(self):
        return self._paths

    @property
    def has_paths(self):
        return (self._paths is not None)

    @property
    def clean_paths(self):
        return ['/'.join(path.split('/')[:-1]) + '/' for path in self._paths]
