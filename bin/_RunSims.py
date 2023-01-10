#!/usr/bin/env python3
import os
import argparse

from parageom.common import print_parageom
from parageom.functions import prepare_mesh_cfg


print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(description="Make an .iec file to launch calculations given a base one and a mesh.")
parser.add_argument(
    "iec_file",
    help="Relative path to .iec file to be used as a template to create the simulations to be run.",
    type=str,
)
parser.add_argument(
    "trb_file",
    help="Relative path to input mesh file for simulations.",
    type=str,
)
parser.add_argument(
    "-o",
    "--output_folder",
    help="Output folder to which to write all the created files and the output mesh.",
    type=str,
    default="to_run",
)
parser.add_argument(
    "-r",
    "--run",
    help="Use this flag to launch the simulations directly.",
    action="count",
    default=0,
)


args = parser.parse_args()

# TODO finish this

if args.mesh:
    os.system(f". {args.output_folder}/RUN.ME")
else:
    print(
        "\n\nPreparation of scripts done. Run `RUN.ME` from here when you are ready to mesh the geometries." 
        f"\nUse command `. {args.output_folder}/RUN.ME`"
    )
