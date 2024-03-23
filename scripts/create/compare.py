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

from langtree import NodeSet, load_iso639_3
from langtree.paths import paths


def compare(tree, df):

    ISO3_LANG = {}
    ISO2_LANG = {}
    ISO3_2 = {}
    ISO3_NODE = {}
    ISO3_PATH = {}

    control_nodes = tree.nodes(terminal = True, copy = True)
    control_paths = tree.paths(terminal = True)

    #df = pd.read_table('data/iso639-3.txt', index_col = 0, encoding = 'utf-8', na_values = "")

    df_control = df.copy() # Will contain registers in df not present in tree

    not_in_df = NodeSet([], []) # Will contain registers in tree not present in df

    for node in tree.nodes(language = True, copy = False):
        node.update(edited = False)

    for node, path in tqdm(zip(tree.nodes(language = True, copy = False),
                               tree.paths(language = True)),
                           total = tree.count_terminal()):

        iso3 = node.attrs.get('iso3')

        try:
            rec = df.loc[iso3]
            df_control = df_control.drop(iso3)
        except:
            not_in_df.append(node, path)
            continue

        iso2 = rec.get('Part1')
        if iso2 is np.nan:
            iso2 = ""

        name = rec.get('Ref_Name')

        ISO3_LANG[iso3] = name
        ISO3_NODE[iso3] = node
        ISO3_PATH[iso3] = path

        if iso2:
            ISO3_2[iso3] = iso2
            ISO2_LANG[iso2] = name

        node.update(iso2 = iso2,
                    scope = rec.get('Scope'),
                    type = rec.get('Language_Type'),
                    edited = True
                    )

    ISO2_3 = {v: k for k, v in ISO3_2.items()}

    return (ISO3_LANG, ISO2_LANG, ISO3_PATH), (df_control, not_in_df)


def comparison_report(df_control, nodeset_control, tree = None, filepath = None):

    df = load_iso639_3()
    if filepath is None:
        filepath = paths.comparison_report

    with open(filepath, "w") as f:

        def print_(text):
            f.write(str(text) + '\n')

        print_("CROSS LANGUAGE (tree & ISO639-3) REPORT\n" + '='*78)

        print_("")
        print_("{:_^128s}".format("SECTION 1"))

        if tree is not None:
            print_("\n> Records in tree non-extisting in ISO639-3: {} out ouf {}".format(len(nodeset_control), tree.count_terminal()))
        else:
            print_("\n> Records in tree non-extisting in ISO639-3: {}".format(len(nodeset_control)))

        print_(nodeset_control)

        print_("")
        print_("{:_^128s}".format("SECTION 2"))
        untouched_iso2 = df_control[df_control["Part1"].notnull()][["Part1", "Ref_Name", "Scope", "Language_Type"]]
        all_iso2 = df[df["Part1"].notnull()]
        print_("\n> Records in ISO639-3 containing field 'ISO2' not present in tree: {} out of {}".format(len(untouched_iso2), len(all_iso2)))
        print_(untouched_iso2)

        if tree is not None:
            print_("")
            print_("{:_^128s}".format("SECTION 3"))
            print_("\n> For each of them (SECTION 2) best match in tree by name")

            untouched_iso2_iso2 = untouched_iso2["Part1"].to_list()
            untouched_iso2_iso3 = untouched_iso2.index.to_list()
            untouched_iso2_names = untouched_iso2["Ref_Name"].to_list()
            untouched_iso2_paths = []

            for i, (iso2, iso3, name) in enumerate(zip(untouched_iso2_iso2, untouched_iso2_iso3, untouched_iso2_names)):
                header = '{}. {} ({} | {}) '.format(i+1, name, iso3, iso2)
                print_("")
                print_('{:.<128s}'.format(header))
                output_set = tree.find(name, terminal = True, ret_path = True)
                print_(output_set)
                untouched_iso2_paths.append(output_set.clean_paths)

        print_("")
        print_("{:_^128s}".format("SECTION 4"))
        print_("\n> Records in ISO639-3 not present in tree: {} out of {}".format(len(df_control), len(df)))
        print_(df_control[["Part1", "Ref_Name", "Scope", "Language_Type"]].fillna('').to_string())
