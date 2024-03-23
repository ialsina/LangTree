from langtree import Node, load_iso639_3
from langtree.paths import paths


def append_manual(tree, filepath = None):

    df = load_iso639_3()
    if filepath is None:
        filepath = paths.manual_nodes

    counter = 0

    with open(filepath, 'r') as f:

        lines = f.readlines()

        for l in lines:
            line = l.replace("\n", "").strip()

            if line == "" or line.startswith("#"):
                continue

            elements = line.split("\t")

            if len(elements) < 2:
                continue

            iso3 = elements[0]
            path = elements[1]
            node = tree.follow(path)
            is_new = path.endswith("/")
            extra = {el.split(":")[0]: el.split(":")[1] for el in elements[2:]}

            rec = df.loc[iso3]
            attrs = dict(
                iso3  = iso3,
                iso2  = rec.get('Part1'),
                scope = rec.get('Scope'),
                type  = rec.get('Language_Type'),
                edited = True,
                **extra
            )

            if not is_new:
                node.update(**attrs)

            else:
                new_node = Node(name = rec.get('Ref_Name'), **attrs)
                node.add(new_node)

            counter += 1

    return tree, counter