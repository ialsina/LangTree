"""Given the file families.txt, recursively guess
the ethnologue url for each specific language family,
and write the url content to file
"""

import requests
from tqdm import tqdm

session = requests.Session()
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=2))


families = []
with open('families.txt', 'r') as f:
	for l in f.readlines():
		family = '-'.join(l.replace('\n', '').split(' ')[:-1]).lower().strip()
		if family[0] == '#':
			continue
		
		families.append(family)

families = sorted(families)
for family in tqdm(families):
	url = 'https://www.ethnologue.com/subgroups/{}'.format(family)
	response = session.get(url)
	if response.status_code != 200:
		print('Error in', family)
	else:
		with open('html/{}.html'.format(family), 'w') as f:
			f.write(response.text)