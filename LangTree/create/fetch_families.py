

import requests
import os
from tqdm import tqdm

def fetch_families(file_path = None, dest_path = None, dict_manual = None):
    """Given the file families.txt, recursively guess
    the ethnologue url for each specific language family,
    and write the url content to file
    """

    file_path = file_path or os.path.join(PATH_DATA, 'families.txt')
    dest_path = dest_path or PATH_HTML
    dict_manual = dict_manual or {"kx’a": "kx'"}

    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))

    families = []
    with open(file_path, 'r') as f:
        for l in f.readlines():
            if l == '\n':
                continue

            if l.strip().startswith("#"):
                continue

            family = '-'.join(l.replace('\n', '').split(' ')[:-1]).lower().strip()
            family = family.replace('(', '').replace(')', '')
            family = dict_manual.get(family) or family
            
            families.append(family)

    families = sorted(families)
    for family in tqdm(families):
        url = 'https://www.ethnologue.com/subgroups/{}'.format(family)
        response = session.get(url)
        if response.status_code != 200:
            print('Error in', family)
        else:
            with open(os.path.join(dest_path, '{}.html'.format(family)), 'w') as f:
                f.write(response.text)