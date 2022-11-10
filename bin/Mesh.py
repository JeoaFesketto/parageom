#!/usr/bin/env python3
import os
import argparse

from parageom.common import print_parageom
from parageom.functions import prepare_mesh_cfg


print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(description="Prepare files to be meshed and optionally mesh them in the process.")
parser.add_argument(
    "trb_file",
    help="Relative path to trb file to be used as a template to mesh the configuration file.",
    type=str,
)
parser.add_argument(
    "config_file",
    help="config file `.cfg` to mesh. Several can be inputted at once.",
    type=str,
    nargs="+",
)
parser.add_argument(
    "-o",
    "--output_folder",
    help="Output folder to which to write all the created files and the output mesh.",
    type=str,
    default="to_run",
)
parser.add_argument(
    "-m",
    "--mesh",
    help="use this flag to mesh the geometries straight away once the scripts are created.",
    action="count",
    default=0,
)


args = parser.parse_args()

prepare_mesh_cfg(args.trb_file, *args.config_file, output_folder=args.output_folder)

if args.mesh:
    os.system(f". {args.output_folder}/RUN.ME")
else:
    print(
        "\n\nPreparation of scripts done. Run `RUN.ME` from here when you are ready to mesh the geometries." 
        f"\nUse command `. {args.output_folder}/RUN.ME`"
    )
