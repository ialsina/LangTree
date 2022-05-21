from tqdm import tqdm
import json
import sys
import os
import pickle

from LangTree import Node

def protect(func):
	def inner(*args, **kwargs):

		try:
			return func(*args, **kwargs)

		except FileNotFoundError as e:
			return

	return inner


@protect
def load_json():
	with open(os.path.join('..', 'data', 'node_tree.json'), 'r') as f:
		return json.load(f)

@protect
def load_obj():
	with open(os.path.join('..', 'data', 'node_tree.pickle'), 'rb') as f:
		return pickle.load(f)

@protect
def load_paths():
	with open(os.path.join('..', 'data', 'lang_paths.txt'), 'r') as f:
		return [el.replace('\n', '') for el in f.readlines()]


def load_tree():
	return get_tree(load_json())


def get_tree(inp):

	assert isinstance(inp, list) or isinstance(inp, dict) or isinstance(inp, str)

	if isinstance(inp, list):

		for el in inp:

			n = get_tree(el)

	elif isinstance(inp, dict):

		assert len(inp) == 1
		key, val = list(inp.items())[0]
		assert isinstance(val, list)

		n = Node(key, [get_tree(el) for el in val])


	elif isinstance(inp, str):

		n = Node(inp)

	return n


def load_all():
	return load_json(), load_paths(), load_obj(), load_tree()

	


if __name__ == "__main__":

	tree_json = load_json()
	tree_paths = load_paths()
	tree = load_obj()
	j = tree_json
	a = tree_json['/'][0]
	t = load_tree()
