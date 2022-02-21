import os
import sys
from bs4 import BeautifulSoup
from tqdm import tqdm
import json
import requests

with open('data/lang_iso_name.json', 'r') as f:
	ISO_LANG = json.load(f)

with open('data/language_families.json', 'r') as f:
	fam = json.load(f)

with open('data/language_paths.json', 'r') as f:
	paths = json.load(f)

