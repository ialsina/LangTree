"""Given the html files for each of the language families,
build language tree for each and write them in json object
"""

from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import Node
import json
import sys
import os
from copy import copy, deepcopy

from helper import *

link = 'html/indo-european.html'
link = 'html/mongolic.html'
link = 'html/bororoan.html'


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
    global result1, result2, hh
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


def get_root(inp, is_path=False, write=False):

    global soup

    if is_path:
        path = '{}'.format(inp)
        family = os.path.split(path)[-1].replace('.html', '')

    else:
        path = 'html/{}.html'.format(inp)
        family = inp

    with open(path, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    root = soup.find_all("div", {"class": "ethn-tree"})
    assert len(root) == 1, "Too many root candidates!"
    root = root[0]

    if write:
        write_root(root, 'pretty/{}.txt'.format(family))

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

    root = get_root(path, is_path=True, write=False)

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


def write_root(r, path_to_file):

    with open(path_to_file, "w") as f:
        f.write(r.prettify())


def parse_all(save_soup=True):
    tree = Node("/")

    errcount = 0
    
    dirs = sorted(os.listdir('html'))

    with tqdm(total=len(dirs)) as progress:
        for file in dirs:

            progress.set_description_str('{:>30s}'.format(file))
            #progress.sleep(1)
            progress.update()

            if file == '.html':
                continue

            path = os.path.join('html', file)
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

    print("Parsing error count:", errcount)
    print("Tree uncheckable count:", checks.count(None))
    print("Tree error count:", checks.count(False))

    return tree


if __name__ == '__main__':
    tree = parse_all(True)
    tree.save()
    tree.save_json()
    tree.save_paths()

    #aa = parse_file('html/afro-asiatic.html')
    #ie = parse_file('html/indo-european.html')
