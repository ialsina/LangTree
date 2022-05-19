"""Fetch html for a single url
"""

import requests
from tqdm import tqdm

session = requests.Session()
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))

url = 'https://www.ethnologue.com/subgroups/kx%E2%80%99'
response = session.get(url)
with open('html/{}.html'.format('kx%E2%80%99'), 'w') as f:
	f.write(response.text)