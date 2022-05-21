import os

from .append import append_manual
from .compare import compare, comparison_report
from .fetch import fetch_ethnologue
from .loader import load_iso639_3
from .parse import parse_all
from LangTree import PATH_DATA, PATH_HTML, PATH_OUT


def main():
    if not os.path.exists(os.path.join(PATH_DATA, 'families.txt')):
        print("File 'families.txt' missing. Please, add file in\n{}".format(PATH_DATA))
        return


    if not os.path.isdir(os.path.join(PATH_HTML)):
        print("Directory 'html/' missing. Fetching html from ethnologue.com")
        fetch_ethnologue()

    print("Parsing all html files into Node tree")
    tree = parse_all()

    #tree.save()
    #tree.save_json()
    #return

    print("Appending manual records")
    tree, count = append_manual(tree)
    print("> Count: {}".format(count))

    print("Performing checks and comparison")
    dicts, comparison_result = compare(tree, load_iso639_3())

    print("Producing comparison report")
    comparison_report(*comparison_result, tree = tree)

    tree.save()
    tree.save_json()