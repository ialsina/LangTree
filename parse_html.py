"""Given the html files for each of the language families,
build language tree for each and write them in json object
"""

from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import sys
import os

link = 'html/indo-european.html'
link = 'html/mongolic.html'
link = 'html/bororoan.html'



def get_list(html):
    if html.name == 'div' and 'item-list' in html.attrs['class']:
        # Already inputted item list
        item_list = html
    else:
        # Extract item list
        result1 = html.find_all('div', {'class': 'item-list'}, recursive=False)
        result2 = html.find_all('div', {'class': 'item-list'}, recursive=True)
        if len(result1) == 1:
            # Item list found in the top next level
            item_list = result1[0]
        elif len(result2) == 1:
            # Item list not found in the first children level
            # But there is only one list further on in the tree
            item_list = result2[0]


    ul = item_list.find_all('ul', recursive=False)
    if len(ul) != 1:
        # Failed
        return

    elements = ul[0].find_all('li', recursive=False)
    return elements


def strip(html):
    divs = html.find_all('div', recursive=False)

    #if any('item-list' in tag.attrs['class'] for tag in divs):
    if 'class' in html.attrs:

        if 'first' in html.attrs['class'] or 'last' in html.attrs['class']:
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
        return (name, [unravel(elem) for elem in elems])
    else:
        return (name, [])


def parse_file(path):

    family = os.path.split(path)[-1].replace('.html', '')

    with open(path, 'r') as f:

        soup = BeautifulSoup(f.read(), 'html.parser')

        root = soup.find_all('div', {"class": "views-field views-field-name-1"})

        assert len(root) == 1, "Too many root candidates!"

        root = root[0]

        #top = root.find_parent().find_parent().find_parent().find_parent().find_next_sibling()
        ##blocks = top.find_all('li', {'class': 'first'})

        top = root.find_next('div', {"class": "view-content"})
        
        res = [unravel(el) for el in get_list(top)]

    return {family: res}


def parse_all():
    tree = {}

    errcount = 0

    for file in tqdm(os.listdir('html')):
        if file == '.html':
            continue

        path = os.path.join('html', file)
        try:
            tree.update(parse_file(path))
        except Exception as e:
            print('ERROR IN', file)
            errcount += 1
            raise e
            continue

    print("Error count:", errcount)
    return tree


if __name__ == '__main__':
    res = parse_all()
    with open('data/language_families.json', 'w') as f:
        json.dump(res, f)
