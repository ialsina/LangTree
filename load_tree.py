from tqdm import tqdm
from utils import Node
import json
import sys
import os
import pickle

def load_json():

	with open('data/node_tree.json', 'r') as f:
		return json.load(f)


def load_obj():

	with open('data/node_tree.pickle', 'rb') as f:
		return pickle.load(f)


def load_paths():

	with open('data/lang_paths.txt', 'r') as f:
		return [el.replace('\n', '') for el in f.readlines()]


if __name__ == "__main__":

	tree_json = load_json()
	tree_paths = load_paths()
	tree = load_obj()
