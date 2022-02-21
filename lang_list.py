import json
import pandas as pd

with open('data/language_families.json', 'r') as f:
	fam = json.load(f)

fam = ('', list(fam.items()))

#iso_lang = pd.read_csv('data/iso639-3.txt', sep='\t', header=0)
ISO_LANG = {}


def clean_name(name):
    out = name.replace('\n', '')
    out = out.split('[')[0]
    out = out.split('(')[0]
    out = out.strip()
    return out


def get_iso(name):
    out = name.replace('\n', '')
    out = out.split('[')[1]
    out = out.split(']')[0]
    return out

def walk(tup):
	assert isinstance(tup, tuple) or isinstance(tup, list)
	assert len(tup) == 2
	assert isinstance(tup[0], str)
	assert isinstance(tup[1], list)

	name = clean_name(tup[0])
	children = tup[1]

	if len(children) == 0:
		iso_char = get_iso(tup[0])
		ISO_LANG[iso_char] = name
		return [name]

	l = []

	for child in children:

		outcome = walk(child)

		l.extend([name + '/' + el for el in walk(child)])

	return l


flatten = walk(fam)
LANG_ISO = {val: key for (key, val) in ISO_LANG.items()}

paths = {}

for element in flatten:
	split = element.split('/')
	path = split[:-1]
	lang = split[-1]
	paths[lang] = '/'.join(path)

with open('data/language_paths.json', 'w') as f:
	json.dump(paths, f)

with open('data/lang_iso_name.json', 'w') as f:
	json.dump(ISO_LANG, f)
