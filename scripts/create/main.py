import os


from append import append_manual
from compare import compare, comparison_report
from fetch import fetch_ethnologue
from parse import parse_all
from langtree import load_iso639_3
from langtree.paths import DATA_DIR

def main():
    if not os.path.exists(os.path.join(DATA_DIR, 'families.txt')):
        print("File 'families.txt' missing. Please, add file in\n{}".format(DATA_DIR))
        return

    if not os.path.isdir(os.path.join(DATA_DIR / "html")):
        print("Directory 'html/' missing. Fetching html from ethnologue.com")
        fetch_ethnologue()

    print("Parsing all html files into Node tree")
    tree = parse_all()

    print("Appending manual records")
    tree, count = append_manual(tree)
    print("> Count: {}".format(count))

    print("Performing checks and comparison")
    _, comparison_result = compare(tree, load_iso639_3())

    print("Producing comparison report")
    comparison_report(*comparison_result, tree=tree)

    tree.save()
    tree.save_json()
    tree.save_paths()
    tree.save_paths(filename="paths_iso3", key="iso3")
    tree.save_paths(filename="paths_iso2", key="iso2")
