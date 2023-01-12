#!/usr/bin/env python3
import os

import argparse
from subprocess import check_output
import os

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
    "-a",
    "--auto_sbatch",
    help="Sbatch all the created job files automatically.",
    action="count",
    default=0,
)
parser.add_argument(
    "-c",
    "--csv_sbatch",
    help="Sbatch all the created job files automatically from csv file.",
    type=str,
    default='comps.csv',
)
parser.add_argument(
    "-o",
    "--overwrite",
    help="overwrite pre-existing job files",
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

created = []

for folder in args.folders:
    tmp_results = recursive_get_files(folder)
    for run_file in tmp_results:
        _CASENAME_ = run_file.split('/')[-1][:-4]
        output_directory = '/'.join(run_file.split('/')[:-1])
        output_directory = f"{output_directory}/.."
        if not os.path.exists(f'{output_directory}/job_{_CASENAME_}') or args.overwrite:
            with open(f'{output_directory}/job_{_CASENAME_}', 'w') as f:
                f.write(data.replace('_CASENAME_', _CASENAME_))
            created.append(f'{output_directory}/job_{_CASENAME_}')

if args.csv_sbatch:
    def _job_id(prefix, rpm, pressure):
            name = f'{prefix}_{rpm}rpm_{pressure[:2]}kp'
            raw_string = check_output(f'squeue --name {name}', shell=True)
            job_id = int(raw_string.split()[8])
            return job_id
    def _job_filename(prefix, rpm, pressure):
            return f'job_{prefix}_{rpm}rpm_{pressure[:2]}kp'

    prefix = os.path.abspath(args.csv_sbatch).split('/')[-2]

    with open(args.csv_sbatch, 'r') as f: data = f.read()
    computations = [tuple(computation.replace(' ', '').split(',')) for computation in data.split('\n') if computation]

    for i, computation in enumerate(computations):
            dependent = False
            if len(computation) == 2:
                    init = _job_id(prefix, computations[i-1][0], computations[i-1][1])
                    dependent = True
            elif len(computation) == 4:
                    init = _job_id(prefix, computation[2], computation[3])
                    dependent = True
            job_name = _job_filename(prefix, computation[0], computation[1])
            if dependent:
                    print(f'sbatch -d {init} {job_name}')
                    os.system(f'sbatch -d {init} {job_name}')
            else:
                    print(f'sbatch {job_name}')
                    os.system(f'sbatch {job_name}')


if args.auto_sbatch and not args.csv_sbatch:
    for file in created:
        os.system(f'sbatch {file}')
