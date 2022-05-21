import requests
import requests
import json
import sys
import os
from copy import copy, deepcopy
from collections import Counter

from bs4 import BeautifulSoup
from tqdm import tqdm
import pandas as pd
import numpy as np

from LangTree import PATH_DATA, PATH_OUT, PATH_HTML


def load_iso639_3(filepath = None):

    filepath = filepath or os.path.join(PATH_DATA, 'iso639-3.txt')
    return pd.read_table(filepath, index_col = 0, encoding = 'utf-8', na_values = "")