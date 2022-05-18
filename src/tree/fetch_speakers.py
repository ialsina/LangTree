import requests
import json
from tqdm import tqdm
from collections import defaultdict

with open('data/lang_iso_name.json', 'r') as f:
	iso = json.load(f)

url = lambda inp: 'https://en.wikipedia.org/wiki/{}'.format(inp)

good = []
bad = []

responses = defaultdict(list)


with tqdm(total=len(iso)) as t:
	for key, val in iso.items():

		#t.set_description('Request: {:>20s} [{:3s}]'.format(val, key))

		if ',' in val:
			lang = [val.split(',')[1],
			        val.replace(',', ''),
			        val.replace(',', '') + '_language']
		else:
			lang = [val + '_language']

		for l in lang:
			r = requests.get(url(l))
			if r.status_code == 200:
				break

		responses[r.status_code].append(key)

		t.set_description('Request: {:>20s} [{:3s}] - {}'.format(val, key, r.status_code))
		t.update()