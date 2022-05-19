import pathlib
import sys
import os

#sys.path.insert(0, str(pathlib.Path(__file__).parent))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "LangTree")))

from utils import Node, nodes_, paths_

def nodes2_(node, terminal = False):

    children = node.children

    l = []

    if not terminal or len(children) == 0:
    	l.append(node)

    for child in children:
        l.extend(nodes2_(child, terminal = terminal))

    return l


def nodes3_(node):
    children = node.children

    l = []

    if len(children) == 0:
    	l.append(node)

    for child in children:
        l.extend(nodes3_(child))

    return l


def nodes0_(node):

	l = nodes3_(node)

	return list(filter(lambda x: x.is_terminal, l))


a = Node("a", [Node("a{}".format(i)) for i in range(1, 8)])
b = Node("b", [Node("b{}".format(i)) for i in range(1, 10)])
c = Node("c", [Node("c{}".format(i)) for i in range(1, 12)])
d = Node("d", [Node("d{}".format(i)) for i in range(1, 4)])

b[3] = d

tree = Node("z", [a, b, Node("x"), c])



l1 = nodes2_(tree, terminal = True)
l2 = nodes2_(tree, terminal = False)


