import requests
import os

from tqdm import tqdm

from langtree.paths import DATA_DIR

REPLACE_FILENAMES = {
    "kx’a": "kx'",
}
REPLACE_URLS = {
    "kx’a": "kx’",
}

def get_url(family_name):
    return f"https://www.ethnologue.com/subgroups/{family_name:s}"

def fetch_ethnologue(file_path = None, dest_path = None):
    """Given the file families.txt, recursively guess
    the ethnologue url for each specific language family,
    and write the url content to file
    """

    file_path = file_path or DATA_DIR / "families.txt"
    dest_path = dest_path or DATA_DIR / "html"

    if not os.path.isdir(dest_path):
        os.mkdir(dest_path)

    session = requests.Session()
    session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))

    families = []
    with open(file_path, "r") as f:
        for l in f.readlines():
            line = l.replace("\t", "").replace("\n", "").strip()

            if line == "" or line.startswith("#"):
                continue

            family = "-".join(line.split(" ")[:-1]).lower().strip()
            family = family.replace("(", "").replace(")", "")

            families.append(family)

    families = sorted(families)

    with tqdm(total = len(families)) as progress:
        for family in families:
            family_name = REPLACE_URLS.get(family) or family
            filename = REPLACE_FILENAMES.get(family) or family
            url = get_url(family_name)

            progress.set_description_str("{:>30s}".format(family))
            progress.update()
            response = session.get(url)

            if response.status_code != 200:
                print("Error in", family)
            else:
                with open(os.path.join(dest_path, "{}.html".format(filename)), "w") as f:
                    f.write(response.text)
                    