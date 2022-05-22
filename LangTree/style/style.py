import colorsys
import random

from ete3 import Tree as EteTree
from ete3 import TreeStyle, TreeFace, TextFace
from ete3 import Tree, faces, AttrFace, TreeStyle, NodeStyle

from LangTree import Node, load_obj

def palette(amount, *args):

    for x in range(amount):
        hsv = (x * 1.0 / amount, 0.5, 0.5)
        rgb1 = colorsys.hsv_to_rgb(*hsv)
        rgb255 = tuple([int(255*el) for el in rgb1])
        rgb_hex = '#%02x%02x%02x' % rgb255
        yield rgb_hex

def layout(node):
    if node.is_leaf():
        attr = AttrFace("name", fsize=20)
        faces.add_face_to_node(attr, node, 0, position="aligned")

    else:
        attr = AttrFace("name", fsize=15, fgcolor="#903000")
        faces.add_face_to_node(attr, node, 0, position="branch-top")


def to_render(tree):

    node_styles = []

    t = tree.ete_tree()
    print(len(t))

    colors = palette(len(tree))
    for child, color in zip(t.children, colors):
        nst = NodeStyle()
        nst["bgcolor"] = color
        child.set_style(nst)
        node_styles.append(nst)

    ts = TreeStyle()
    ts.layout_fn = layout
    ts.show_leaf_name = False

    #ts.mode = "c"
    ts.root_opening_factor = 0
    return t, ts

if __name__ == "__main__":
    tree = load_obj()
    t, ts = to_render(tree)
    #t.render("node_background.png", w=400, tree_style=ts)
    t.show(tree_style=ts)