#!/usr/bin/env python3
import os
import errno

import argparse
import json
import shutil as sh

from parageom.common import print_parageom
from parageom.case import Case

import parablade.init_files.path as pb_path

print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(description="Make job files and sbatch the different jobs.")
parser.add_argument(
    "folders",
    help="Path to folder containing .run file etc..",
    default=".",
    type=str,
    nargs="+",
)
parser.add_argument(
    "-r",
    "--refine3D",
    help="Flag to run 3D matching afterwards. It might yield better results.",
    action="count",
    default=0,
)

args = parser.parse_args()

def recursive_get_files(folder):
    results = []
    for file in os.listdir(folder):
        path = f'{folder}/{file}'
        if os.path.isdir(path):
            results += recursive_get_files(path)
        elif os.path.isfile(path) and path.endswith('.run'):
            results.append(path)
    return results

for folder in args.folders:
    tmp_results = recursive_get_files(folder)
    print(tmp_results)