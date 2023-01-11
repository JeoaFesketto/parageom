#!/usr/bin/env python3
import os
import argparse

from parageom.common import print_parageom
from parageom.functions import make_computations
import time


print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(
    description="Add computations to an iec file."
)
parser.add_argument(
    "iec_file",
    help="Relative path to iec file in which to create the additional computations.",
    type=str,
)
parser.add_argument(
    "csv_file",
    help="Relative path to the csv file containing the computations to be created. Each line should contain an rpm value and a pressure value separated by a coma.",
    type=str,
)


args = parser.parse_args()

with open(args.csv_file, 'r') as f:
    data = f.read()

computations = [tuple(map(float, computation.split(','))) for computation in data.split('\n') if computation]

runme = make_computations(args.iec_file, computations)

os.system(f'. {runme}')