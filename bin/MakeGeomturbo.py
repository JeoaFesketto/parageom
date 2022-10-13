#!/usr/bin/env python3
import os
import argparse

from parageom.reader import From_param_3D
from parageom.common import print_parageom


print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(
    description="Build .geomTurbo file from .cfg file"
)
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
    "-LE",
    "--LE_fillet",
    help="Bool to fillet or not the leading edge",
    default=False,
    type=bool,
)
parser.add_argument(
    "-TE",
    "--TE_fillet",
    help="Bool to fillet or not the trailing edge",
    default=False,
    type=bool,
)


args = parser.parse_args()
DIR = os.getcwd() + "/"

# SCRIPT STARTS HERE:

if not args.output_folder.endswith("/"):
    args.output_folder += "/"

try:
    os.mkdir(DIR + args.output_folder)
except:
    print("Writing to existing folder, files might have been overwriten.")


blade = From_param_3D(DIR+args.config_file)
blade.output_geomTurbo(
    DIR+args.output_folder+args.config_file.split('/')[-1][:-3]+'geomTurbo',
    args.LE_fillet,
    args.TE_fillet
)