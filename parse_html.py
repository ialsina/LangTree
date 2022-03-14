"""Given the html files for each of the language families,
build language tree for each and write them in json object
"""

from bs4 import BeautifulSoup
from tqdm import tqdm
from utils import Node
import json
import sys
import os

from helper import *

link = 'html/indo-european.html'
link = 'html/mongolic.html'
link = 'html/bororoan.html'


deb = Debug()
counter = Counter()
prelangs = dict()


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
        result2 = [el for el in result2 if el.text.replace('\n', '').strip() != ""]

        deb.h = html
        deb.r1 = result1
        deb.r2 = result2

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


def unravel(tag):

    name, elems = strip(tag)
    if elems is not None:
        return Node(name, [unravel(elem) for elem in elems], soup=tag)
    else:
        return Node(name, soup=tag)


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

    deb.path = path

    with open(path, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    deb.soup = soup

    root = soup.find_all('div', {"class": "views-field views-field-name-1"})
    assert len(root) == 1, "Too many root candidates!"
    root = root[0]

    root2 = soup.find_all("div", {"class": "ethn-tree"})
    assert len(root2) == 1, "Too many root2 candidates!"
    root2 = root2[0]

    if write:
        write_root(root2, 'pretty/{}.txt'.format(family))

    deb.root1 = root
    deb.root2 = root2

    return root2


def clean(tag):
    for t in tag.find_all(recursive=False):
        if text_clean(t) == "":
            t.extract()

    return tag


def text_clean(tag):
    return tag.text.replace('\n', '').strip()

def parse_len1(tag):
    if not 'attachment-before' in tag.attrs.get('class', []):
        assert False

    #divs = tag.find_all('div', recursive=False)
    #divs = [el for el in divs if text_clean(el) != ""]
    #assert len(divs) == 1, "Bad number of divs!"

    name_candidate = tag.find_all('div', {'class': 'views-field-name-1'})
    assert len(name_candidate) == 1
    name = text_clean(name_candidate[0])

    elements_candidate = tag.find_all('div', {'class': 'item-list'})
    assert len(elements_candidate) in [0, 1]
    if len(elements_candidate) == 1:
        elements_tag = get_list(elements_candidate[0])
    else:
        elements_tag = []

    elements_node = [unravel(el) for el in elements_tag]

    #print(name, '\n', len(elements_tag), end='\n\n\n')

    prelangs[deb.cur] = elements_node

    return name, elements_node



def parse_file(path):

    deb.cur = path2name(path)
    root = get_root(path, is_path=True, write=True)

    #top = root.find_parent().find_parent().find_parent().find_parent().find_next_sibling()
    ##blocks = top.find_all('li', {'class': 'first'})

    children = []

    divs = root.find_all('div', recursive=False)
    assert len(divs) in [1, 2]

    name, c = parse_len1(divs[0])

    children.extend(c)

    if len(divs) == 2:

        #tops = divs[1].find_all_next('div', {"class": "view-content"}, recursive=False)
        #tops = [el for el in tops if el.text.replace("\n", "").strip() != ""]

        tops = get_list(divs[1])

        deb.tops = tops        

        for i, top in enumerate(tops):
            try:
                if len(top.text.replace('\n', '').strip()) > 30:
                    children.extend([unravel(el) for el in get_list(top)])
                else:
                    continue
                deb['rootok'] = root
                deb['topsok'] = tops
            except Exception as e:
                print("RAISED IN TOP #{}".format(i))
                deb.errtop = top
                deb['rootko'] = root
                deb['topsko'] = tops
                raise(e)

    return Node(name, children)


def write_root(r, path_to_file):

    with open(path_to_file, "w") as f:
        f.write(r.prettify())


def parse_all():
    tree = Node("/")

    errcount = 0

    stats = Counter()
    
    dirs = sorted(os.listdir('html'))

    for file in tqdm(dirs):
        if file == '.html':
            continue

        path = os.path.join('html', file)
        deb.curpath = path
        try:
            tree.add(parse_file(path))

        except EmptyR1 as e:
            deb.d['r1error'].append(path)
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


def statistics():

    stats = Counter()
    cont_soup = Container()
    cont_attb = Container()

    dirs = sorted(os.listdir('html'))

    for file in tqdm(dirs):

        deb.cur = file

        if file == '.html':
            continue

        root = get_root('html/'+file, is_path=True, write=False)
        attb = attachment_before(root)
        parse_len1(attb)


    # MOCK SPLIT

        divs = root.find_all('div', recursive=False)

        name = path2name(file)
        cont_soup[len(divs)][name] = root
        cont_attb[len(divs)][name] = attb
        stats.update(len(divs))


    return stats, (cont_soup, cont_attb)





if __name__ == '__main__':
    res = parse_all()
    with open('data/language_families.json', 'w') as f:
        json.dump(res.json(), f)
    
    #s, (c, ca) = statistics()



