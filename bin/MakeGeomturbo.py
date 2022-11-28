#!/usr/bin/env python3
import argparse

from parageom.common import print_parageom
from parageom.functions import make_geomTurbo

print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(description="Build .geomTurbo file from .cfg file")
parser.add_argument(
    "config_file",
    help="Parablade configuration file to be used to generate the .geomTurbo file.",
    type=str,
)
parser.add_argument(
    "-o",
    "--output_folder",
    help="relative path to output folder",
    default="output_geometry/",
    type=str,
)
parser.add_argument(
    "-N",
    "--Nsections",
    help="number of sections in output geomTurbo file",
    default=181,
    type=int,
)
parser.add_argument(
    "-n",
    "--Npoints",
    help="number of points in each section. If -TE and -LE are used, more points will be added",
    default=362,
    type=int,
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
parser.add_argument(
    "-x",
    "--coordinates_order",
    help="Order in which the coordinates are set in the geomTurbo file. 'xyz' is default.",
    default="xyz",
    type=str,
)

args = parser.parse_args()


make_geomTurbo(
    args.config_file,
    output_folder=args.output_folder,
    N_sections=args.Nsections,
    N_points=args.Npoints,
    LE_fillet=bool(args.LE_fillet),
    TE_fillet=bool(args.TE_fillet),
    xyz=args.coordinates_order,
)
