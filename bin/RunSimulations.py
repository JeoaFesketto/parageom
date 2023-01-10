#!/usr/bin/env python3
import os
import errno

import argparse
import json
import shutil as sh

from parageom.common import print_parageom
from parageom.case import Case

import parablade.init_files.path as pb_path

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

for folder in args.folders:
    if os.path.isdir(folder):
        print(folder)