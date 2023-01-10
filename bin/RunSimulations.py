#!/usr/bin/env python3
import os

import argparse
import shutil as sh

from parageom.common import print_parageom

import parageom.ressources.path as pg_path
init_f_path = os.path.dirname(pg_path.__file__)

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

def recursive_get_files(element):
    results = []
    if os.path.isdir(element):
        for file in os.listdir(element):
            path = f'{element}/{file}'
            if os.path.isdir(path):
                results += recursive_get_files(path)
            elif os.path.isfile(path) and path.endswith('.run'):
                results.append(path)
    return results



with open(f'{init_f_path}/job', 'r') as f:
    data = f.read()

for folder in args.folders:
    tmp_results = recursive_get_files(folder)
    for run_file in tmp_results:
        _CASENAME_ = run_file.split('/')[-1][:-4]
        output_directory = '/'.join(run_file.split('/')[:-1])
        output_directory = f"{output_directory}/.."
        with open(f'{output_directory}/{_CASENAME_}', 'w') as f:
            f.write(data.replace('_CASENAME_', _CASENAME_))
        

    