#!/usr/bin/env python3
import argparse
import json

from parageom.common import print_parageom
from parageom.case import Case


print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(description="Make a .cfg file from a .geomTurbo file")
parser.add_argument(
    "geomTurbo_file",
    help="Source .geomTurbo file to be matched.",
    type=str,
)
parser.add_argument(
    "Nsections",
    help="Number of sections in output cfg file.",
    default=10,
    type=int,
)
parser.add_argument(
    "-o",
    "--output_folder",
    help="Relative path to output folder.",
    default="CASE",
    type=str,
)
parser.add_argument(
    "-d",
    "--options_dict",
    help=".json file with all the options for the case.",
    default='config.json',
    type=str,
)
parser.add_argument(
    "-p",
    "--on_hpc",
    help="Flag to run non-interactively. Can also be defined inside of init.json.",
    action="count",
    default=0,
)


args = parser.parse_args()
try:
    options = json.load(args.options_dict)
except:
    options={}


if bool(args.on_hpc):
    options['on_hpc'] = True

o = Case(
    args.output_folder,
    args.geomTurbo_file,
    **options
)
o.match_blade(N_sections=args.Nsections)