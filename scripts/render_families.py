import colorsys
import os

from ete3 import Tree as EteTree
from ete3 import TreeStyle, TreeFace, TextFace
from ete3 import Tree, faces, AttrFace, TreeStyle, NodeStyle

from tqdm import tqdm

from langtree import Node, load_obj, OUTPUT_DIR

ORIENTATIONS = {"up": 0, "down": 180, "left": 270, "right": 90}
OUTPUT_FORMAT = 'svg'


def get_angle(n_leaves, default=180):
    from numpy import inf

    angles = [45, 90, 135, 180, 225, 270, 359]
    points = [0, 21, 51, 81, 111, 151, 261, inf]

    for angle, min, max in zip(angles, points[:-1], points[1:]):
        if min <= n_leaves < max:
            return angle

    return default


def palette(amount, *args):
    for x in range(amount):
        hsv = (x * 1.0 / amount, 0.5, 0.5)
        rgb1 = colorsys.hsv_to_rgb(*hsv)
        rgb255 = tuple([int(255 * el) for el in rgb1])
        rgb_hex = '#%02x%02x%02x' % rgb255
        yield rgb_hex


def layout(node):
    if node.is_leaf():
        attr = AttrFace("name")
        faces.add_face_to_node(attr, node, 0, position="branch-right")

    else:
        attr = AttrFace("name", fgcolor="#903000")
        faces.add_face_to_node(attr, node, 0, position="branch-top")


def guess_orientation(angle):
    return "right" if angle < 180 else "up"


def to_render(tree, angle=270, orientation=None):
    if callable(orientation):
        orientation = orientation(angle)
    elif orientation in [None, "guess"]:
        orientation = guess_orientation(angle)
    else:
        assert orientation in ORIENTATIONS.keys(), "Invalid orientation"

    add_angle = ORIENTATIONS.get(orientation, 0)

    node_styles = []

    t = tree.ete_tree()

    # colors = palette(len(tree))
    colors = ("#FFFFFF" for i in range(len(tree)))
    for child, color in zip(t.children, colors):
        nst = NodeStyle()
        nst["bgcolor"] = color
        child.set_style(nst)
        node_styles.append(nst)

    ts = TreeStyle()
    ts.layout_fn = layout
    ts.optimal_scale_level = "full"
    ts.show_leaf_name = False

    ts.mode = "c" if angle >= 0 else "r"
    ts.scale = 100
    ts.arc_span = angle
    ts.arc_start = - 0.5 * angle + 270 + add_angle
    ts.complete_branch_lines_when_necessary = True
    ts.extra_branch_line_color = "#000000"
    ts.extra_branch_line_type = 0
    ts.force_topology = False
    return t, ts


if __name__ == "__main__":

    tree = load_obj()
    children_names = ["indo-european", "australian", "uralic", "afro-asiatic", "chibchan"]
    #children = [tree[child_name] for child_name in children_names]
    children = tree.children

    for child in tqdm(children):
        name = child.name
        angle = get_angle(child.count_terminal())
        t, ts = to_render(child, angle=angle, orientation='guess')
        path = PATH_OUT / 'family_png' / f"{name:s}.{OUTPUT_FORMAT:s}"
        t.render(path, w=20, units="mm", tree_style=ts, dpi=20000)
        #t.show(tree_style=ts)
