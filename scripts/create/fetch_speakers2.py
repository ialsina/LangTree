from bs4 import BeautifulSoup
import requests
import json
from collections import defaultdict
from tqdm import tqdm

from langtree.paths import paths


URL = 'https://en.wikipedia.org/wiki/{}'

def parse(html):

	soup = BeautifulSoup(html, 'html.parser')

	box = soup.find('table', {'class': 'infobox vevent'})

	rows = box.find_all('tr')

	for row in rows:
		if 'Native speakers' in row.text:
			return row.find('td').text

	return "-1"

def navigate(lang_value):

		if ',' in lang_value:
			lang = [lang_value.split(',')[1],
					lang_value.split(',')[1] + ' ' + lang_value.split(',')[0],
			        lang_value.replace(',', ''),
			        lang_value.replace(',', '') + '_language']
		else:
			lang = [lang_value + '_language']

		for l in lang:
			r = requests.get(URL.format(l))
			if r.status_code == 200:
				break

		else:
			return '', r.status_code

		return r.text, r.status_code


if __name__ == "__main__":

	with open(paths.lang_iso_name, 'r') as f:
		iso = json.load(f)


	good = []
	bad = []

	responses = defaultdict(list)
	speakers = {}

	with open(paths.language_speakers, 'w') as f:
		with tqdm(total=len(iso)) as t:
			
			f.write("{:^50s} | {:3s} | {:3s} | {}\n".format('LANGUAGE', 'ISO', 'STA', 'SPEAKERS'))
			
			for key, val in iso.items():

				text, status_code = navigate(val)

				if status_code == 200:
					try:
						spk = parse(text)
					except Exception as e:
						spk = "-2"

				else:
					spk = "-3"

				responses[status_code].append(key)
				speakers[key] = spk

				f.write("{:<50s} | {:3s} | {:3d} | {}\n".format(val, key, status_code, spk))
				t.set_description('Request: {:>20s} [{:3s}] - {:3d} - {}'.format(val, key, status_code, spk))
				t.update()
