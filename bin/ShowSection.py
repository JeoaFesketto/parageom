#!/usr/bin/env python3
import os
import argparse

from parageom.common import print_parageom
from parageom.functions import show_section

print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(
    description="Plot a specified section of one or more geomTurbo files"
)
parser.add_argument(
    "geomTurbo_files", help="geomTurbo files to plot.", type=str, nargs="+"
)
parser.add_argument(
    "-s",
    "--span_percentage",
    help="position along the span to plot",
    default=0,
    type=int,
)
parser.add_argument(
    "-3D",
    "--_3Dimensional",
    help="use this flag to plot in 3 dimensions [NOT YET IMPLEMENTED]",
    action="count",
    default=0,
)
parser.add_argument(
    "-LE",
    "--LE_fillet",
    help="Flag to fillet or not the leading edge",
    action="count",
    default=0,
)
parser.add_argument(
    "-TE",
    "--TE_fillet",
    help="Flag to fillet or not the trailing edge",
    action="count",
    default=0,
)

args = parser.parse_args()

show_section(
    *args.geomTurbo_files,
    span_percentage=args.span_percentage,
    _3Dimensional=bool(args._3Dimensional),
    LE_fillet=bool(args.LE_fillet),
    TE_fillet=bool(args.TE_fillet),
)

for file in args.geomTurbo_files:
    if file.endswith('.cfg'):
        os.system(f"rm -rf tmp_geomturbo")
        continue