import requests
import os

from tqdm import tqdm

from LangTree import PATH_DATA, PATH_HTML, PATH_OUT


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