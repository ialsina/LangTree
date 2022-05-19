import requests
import json
import sys
import os
from copy import copy, deepcopy
from collections import Counter

from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import numpy as np

from utils import Node, NodeSet
from helper import ParsingError, BadPathError, EmptyR1, FullR1
from definitions import *

def fetch_ethnologue(file_path = None, dest_path = None, dict_urls = None, dict_filenames = None):
    """Given the file families.txt, recursively guess
    the ethnologue url for each specific language family,
    and write the url content to file
    """

    file_path = file_path or os.path.join(PATH_DATA, 'families.txt')
    dest_path = dest_path or PATH_HTML
    dict_urls = dict_urls or {"kx’a": "kx’"}
    dict_filenames = dict_filenames or {"kx’a": "kx'"}

    if not os.path.isdir(dest_path):
        os.mkdir(dest_path)

    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))

    families = []
    with open(file_path, 'r') as f:
        for l in f.readlines():
            line = l.replace('\t', '').replace('\n', '').strip()

            if line == "" or line.startswith("#"):
                continue

            family = '-'.join(line.split(' ')[:-1]).lower().strip()
            family = family.replace('(', '').replace(')', '')
            
            families.append(family)

    families = sorted(families)

    with tqdm(total = len(families)) as progress:
        for family in families:
            family_name = dict_urls.get(family) or family
            filename = dict_filenames.get(family) or family
            url = 'https://www.ethnologue.com/subgroups/{}'.format(family_name)

            progress.set_description_str('{:>30s}'.format(family))
            progress.update()
            response = session.get(url)

            if response.status_code != 200:
                print('Error in', family)
            else:
                with open(os.path.join(dest_path, '{}.html'.format(filename)), 'w') as f:
                    f.write(response.text)


def get_elements(html):

    result_try1 = html.find_all('ul', recursive=False)
    if len(result_try1) == 1:
        ul = result_try1[0]

    elif len(result_try1) == 0:
        result_try2 = html.find_all('div', {'class': 'view-content'}, recursive=False) #modified this recursive
        if len(result_try2) == 1:
            result_try21 = result_try2[0].find_all('div', {'class': 'item-list'}, recursive=False) #modified this recursive
            if len(result_try21) == 1:
                result_try211 = result_try21[0].find_all('ul', recursive=False)
                if len(result_try211) == 1:
                    ul = result_try211[0]
                else:
                    raise ParsingError("result_try211", len(result_try211), html)
            else:
                raise ParsingError("result_try21", len(result_try21), html)
        elif len(result_try2) == 0:
            return []
        else:
            raise ParsingError("result_try2", len(result_try2), html)
    else:
        raise ParsingError("result_try1", len(result_try1), html)

    elements = ul.find_all(['li', 'div'], recursive=False)

    return elements


def get_list(html):
    global result1, result2
    if html.name == 'div' and 'item-list' in html.attrs.get('class', []):
        # Already inputted item list
        elements = get_elements(html)

    else:
        # Extract item list
      #  result1 = html.find_all('div', {'class': ['item-list', 'view-language']}, recursive=False)
        result1 = html.find_all('div', {'class': 'view-language'}, recursive=False)
        result2 = html.find_all('div', {'class': 'item-list'}, recursive=False)
        result2 = [el for el in result2 if clean(el) != ""]

        elements = []

        if len(result1) + len(result2) == 0:
            raise EmptyR1

        for r in result1:
            elements.extend(get_elements(r))

        for r in result2:
            elements.extend(get_elements(r))

    return elements
    


def strip(html):
    divs = html.find_all('div', recursive=False)

    #if any('item-list' in tag.attrs['class'] for tag in divs):
    if 'class' in html.attrs:

        if 'first' in html.attrs['class'] or 'last' in html.attrs['class']:
        #if 'first' in html.attrs['class']:
            name = html.find_next('a').text
            elems = get_list(html)

        elif 'lang-indent' in html.attrs['class']:
            name = html.text
            elems = None

        else:
            print(html)
            assert False

    else:
        name = html.find_next('a').text
        elems = get_list(html)

    return name, elems


def unravel(tag, save_soup=True):

    name, elems = strip(tag)
    if elems is not None:
        return Node(name, [unravel(elem, save_soup) for elem in elems], soup=tag if save_soup else None)
    else:
        return Node(name, soup=tag if save_soup else None)


def attachment_before(soup):
    res = soup.find_all('div', {'class': 'attachment-before'}, recursive=False)
    assert len(res) == 1, "Too many attachment-before"
    return res[0]


def get_root(path):

    global soup

    family = os.path.split(path)[-1].replace('.html', '')

    with open(path, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    root = soup.find_all("div", {"class": "ethn-tree"})
    assert len(root) == 1, "Too many root candidates!"
    root = root[0]

    return root


def clean(tag):
    return tag.text.replace('\n', '').strip()


def parse_len1(tag, save_soup=True):
    """Parse the information under the tag "attachment-before", namely:
        - name of the family
        - first (ungrouped) elements
    """
    if not 'attachment-before' in tag.attrs.get('class', []):
        assert False

    name_candidate = tag.find_all('div', {'class': 'views-field-name-1'})
    assert len(name_candidate) == 1
    name = clean(name_candidate[0])

    elements_candidate = tag.find_all('div', {'class': 'item-list'})
    assert len(elements_candidate) in [0, 1]
    if len(elements_candidate) == 1:
        elements_tag = get_list(elements_candidate[0])
    else:
        elements_tag = []

    elements_node = [unravel(el, save_soup) for el in elements_tag]

    return name, elements_node



def parse_file(path, save_soup=True):
    global name, c, children, divs, tops, children1

    root = get_root(path)

    children = []

    divs = root.find_all('div', recursive=False)
    assert len(divs) in [1, 2]


    name, c = parse_len1(divs[0], save_soup)

    children.extend(c)
    children1 = copy(children)

    if len(divs) == 2:

        tops = get_list(divs[1])

        for i, top in enumerate(tops):
            try:
                if len(clean(top)) > 30:
                    #children.extend([unravel(el, save_soup) for el in get_list(top)])
                    children.append(unravel(top, save_soup))
                else:
                    continue

            except Exception as e:
                print("RAISED IN TOP #{}".format(i))
                raise(e)

    return Node(name, children, path=path, soup = root if save_soup else None)


def parse_all(save_soup = True):
    tree = Node("/")

    errcount = 0
    
    dirs = sorted(os.listdir(PATH_HTML))

    with tqdm(total=len(dirs)) as progress:
        for file in dirs:

            progress.set_description_str('{:>30s}'.format(file))
            #progress.sleep(1)
            progress.update()

            if file == '.html':
                continue

            path = os.path.join(PATH_HTML, file)
            try:
                tree.add(parse_file(path, save_soup))

            except EmptyR1 as e:
                print('EMPTY ERROR in {}'.format(path))
                raise e

            except Exception as e:
                print('ERROR IN', file)
                errcount += 1
                raise e


    checks = [el.check() for el in tree]

    print("> Number of nodes:", tree.count_nodes())
    print("> of which, terminal:", tree.count_terminal())
    print("> Parsing error count:", errcount)
    print("> Tree uncheckable count:", checks.count(None))
    print("> Tree error count:", checks.count(False))

    return tree


def load_iso639_3(filepath = None):

    filepath = filepath or os.path.join(PATH_DATA, 'iso639-3.txt')
    return pd.read_table(filepath, index_col = 0, encoding = 'utf-8', na_values = "")


def append_manual(tree, filepath = None):

    df = load_iso639_3()
    filepath = filepath or os.path.join(PATH_DATA, "manual_nodes.txt")

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


def compare(tree, df):

    ISO3_LANG = {}
    ISO2_LANG = {}
    ISO3_2 = {}
    ISO3_NODE = {}
    ISO3_PATH = {}

    control_nodes = tree.nodes(terminal = True, copy = True)
    control_paths = tree.paths(terminal = True)

    #df = pd.read_table('data/iso639-3.txt', index_col = 0, encoding = 'utf-8', na_values = "")

    df_control = df.copy() # Will contain registers in df not present in tree

    not_in_df = NodeSet([], []) # Will contain registers in tree not present in df

    for node in tree.nodes(language = True, copy = False):
        node.update(edited = False)

    for node, path in tqdm(zip(tree.nodes(language = True, copy = False),
                               tree.paths(language = True)),
                           total = tree.count_terminal()):

        iso3 = node.attrs.get('iso3')

        try:
            rec = df.loc[iso3]
            df_control = df_control.drop(iso3)
        except:
            not_in_df.append(node, path)
            continue

        iso2 = rec.get('Part1')
        if iso2 is np.nan:
            iso2 = ""

        name = rec.get('Ref_Name')

        ISO3_LANG[iso3] = name
        ISO3_NODE[iso3] = node
        ISO3_PATH[iso3] = path

        if iso2:
            ISO3_2[iso3] = iso2
            ISO2_LANG[iso2] = name

        node.update(iso2 = iso2,
                    scope = rec.get('Scope'),
                    type = rec.get('Language_Type'),
                    edited = True
                    )

    ISO2_3 = {v: k for k, v in ISO3_2.items()}

    return (ISO3_LANG, ISO2_LANG, ISO3_PATH), (df_control, not_in_df)


def comparison_report(df_control, nodeset_control, tree = None, filepath = None):

    df = load_iso639_3()
    filepath = filepath or os.path.join(PATH_OUT, "comparison_report.txt")

    with open(filepath, "w") as f:

        def print_(text):
            f.write(str(text) + '\n')

        print_("CROSS LANGUAGE (tree & ISO639-3) REPORT\n" + '='*78)

        print_("")
        print_("{:_^128s}".format("SECTION 1"))

        if tree is not None:
            print_("\n> Records in tree non-extisting in ISO639-3: {} out ouf {}".format(len(nodeset_control), tree.count_terminal()))
        else:
            print_("\n> Records in tree non-extisting in ISO639-3: {}".format(len(nodeset_control)))

        print_(nodeset_control)

        print_("")
        print_("{:_^128s}".format("SECTION 2"))
        untouched_iso2 = df_control[df_control["Part1"].notnull()][["Part1", "Ref_Name", "Scope", "Language_Type"]]
        all_iso2 = df[df["Part1"].notnull()]
        print_("\n> Records in ISO639-3 containing field 'ISO2' not present in tree: {} out of {}".format(len(untouched_iso2), len(all_iso2)))
        print_(untouched_iso2)

        if tree is not None:
            print_("")
            print_("{:_^128s}".format("SECTION 3"))
            print_("\n> For each of them (SECTION 2) best match in tree by name")

            untouched_iso2_iso2 = untouched_iso2["Part1"].to_list()
            untouched_iso2_iso3 = untouched_iso2.index.to_list()
            untouched_iso2_names = untouched_iso2["Ref_Name"].to_list()
            untouched_iso2_paths = []

            for i, (iso2, iso3, name) in enumerate(zip(untouched_iso2_iso2, untouched_iso2_iso3, untouched_iso2_names)):
                header = '{}. {} ({} | {}) '.format(i+1, name, iso3, iso2)
                print_("")
                print_('{:.<128s}'.format(header))
                output_set = tree.find(name, terminal = True, ret_path = True)
                print_(output_set)
                untouched_iso2_paths.append(output_set.clean_paths)

        print_("")
        print_("{:_^128s}".format("SECTION 4"))
        print_("\n> Records in ISO639-3 not present in tree: {} out of {}".format(len(df_control), len(df)))
        print_(df_control[["Part1", "Ref_Name", "Scope", "Language_Type"]].fillna('').to_string())


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


if __name__ == "__main__":
    from load import load_obj

    main()

    tree = load_obj()
    


