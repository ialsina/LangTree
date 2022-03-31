from load_tree import load_obj
from utils import Node
import pandas as pd
from tqdm import tqdm
import numpy as np

tree = load_obj()

df = pd.read_table('data/iso639-3.txt', index_col = 0, encoding = 'utf-8')

ISO3_LANG = {}
ISO2_LANG = {}
ISO3_2 = {}

errors = []

for node in tqdm(tree.nodes(terminal = True, copy = False)):
	iso3 = node.attrs.get('iso3')

	try:
		rec = df.loc[iso3]
	except:
		errors.append(iso3)
		continue

	iso2 = rec.get('Part1')
	if iso2 is np.nan:
		iso2 = ""

	name = rec.get('Ref_Name')

	ISO3_LANG[iso3] = name

	if iso2:
		ISO3_2[iso3] = iso2
		ISO2_LANG[iso2] = name


	node.update(iso2 = iso2,
                scope = rec.get('Scope'),
                type = rec.get('Language_Type')
                )