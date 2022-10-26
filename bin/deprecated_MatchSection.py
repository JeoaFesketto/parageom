#!/usr/bin/env python3
import os
import argparse
import sys

from parablade.blade_match import BladeMatch
from parablade.common.config import ReadUserInput, WriteBladeConfigFile, Scale

from parageom.reader import From_geomTurbo
from parageom.rotor import Rotor
from parageom.common import print_parageom


print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(
    description="Parametrize a specific section from a .geomTurbo file"
)
parser.add_argument(
    "geomTurbo_file", help="relative path to input .geomTurbo file", type=str
)
parser.add_argument(
    "config_file",
    help="Parablade configuration file to be used as initialisation.",
    type=str,
)
parser.add_argument(
    "-o",
    "--output_folder",
    help="relative path to output folder",
    default="section_match_output/",
    type=str,
)
parser.add_argument(
    "-s",
    "--section_index",
    help="index of section defined in .geomTurbo file.",
    default=0,
    type=int,
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

rotor = Rotor(From_geomTurbo(args.geomTurbo_file, init="sectioned"))
rotor.parablade_section_export(
    args.section_index,
    file=DIR + args.output_folder + f'{args.config_file.split("/")[-1][:-3]}txt',
    scale_factor=1e-3,
    dim="3D",
)

IN = ReadUserInput(DIR + args.config_file)
IN["NDIM"] = [2]
IN["Config_Path"] = DIR + args.output_folder + args.config_file.split("/")[-1]
IN["PRESCRIBED_BLADE_FILENAME"] = (
    DIR + args.output_folder + f'{args.config_file.split("/")[-1][:-3]}txt'
)
IN = Scale(IN, scale=rotor.scale_factor, in_place=True)

WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)

# Set plotting options
options = {
    "view_xy": "yes",  # 2D Recommended
    "view_xR": "yes",  # 3D Recommended
    "view_yz": "no",  # 3D Optional
    "view_3D": "yes",  # 3D Recommended
    "error_distribution": "yes",
}

matched_blade_object = BladeMatch(
    IN, coarseness=1, plot_options=options, _output_path=DIR + args.output_folder[:-1]
)

matched_blade_object.match_blade(matching_mode="manual")
matched_blade_object.match_blade(matching_mode="DVs")
