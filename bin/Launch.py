#!/usr/bin/env python3
import os
import errno

import argparse
import json
import shutil as sh

from parageom.common import print_parageom
from parageom.case import Case

import parablade.init_files.path as pb_path

init_f_path = os.path.dirname(pb_path.__file__)

print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(description="Prepare a case for pando.")
parser.add_argument(
    "work_dir",
    help="Relative path to work directory.",
    default="CASE",
    type=str,
)
parser.add_argument(
    "geomTurbo_file",
    help="Source .geomTurbo file to be matched.",
    type=str,
)
parser.add_argument(
    "-n",
    "--Nsections",
    help="Number of sections in output cfg file.",
    default=10,
    type=int,
)
parser.add_argument(
    "-s",
    "--scale_factor",
    help="scale_factor of the .geomTurbo file",
    default=1e-3,
    type=float,
)
parser.add_argument(
    "-x",
    "--coordinates_order",
    help="Order in which the coordinates are set in the geomTurbo file. 'xyz' is default.",
    default="xyz",
    type=str,
)
parser.add_argument(
    "-r",
    "--refine3D",
    help="Flag to run 3D matching afterwards. It might yield better results.",
    action="count",
    default=0,
)

args = parser.parse_args()

try:
    os.mkdir(f"container_{args.work_dir}")
except OSError as exc:
    if exc.errno == errno.EEXIST:
        print("Writing to existing directory")
try:
    with open(f"{args.work_dir}/options.json", "r") as f:
        options = json.load(f)
except:
    options = Case.defaults

options["scale_factor"] = args.scale_factor
options["xyz"] = args.coordinates_order

# initialise everything.

o = Case(args.work_dir, args.geomTurbo_file, **options)
o.initialise_case()

sh.copy(
    args.geomTurbo_file,
    f"container_{args.work_dir}/{args.geomTurbo_file.split('/')[-1]}",
)

# write file to be run on hpc.

options["on_hpc"] = True

with open(f"container_{args.work_dir}/options.json", "w") as f:
    json.dump(options, f, indent=4, separators=(", ", ": "))


lines = []
lines.append("import json")
lines.append("from parageom.case import Case\n\n")
lines.append(f"with open(f'options.json', 'r') as f:")
lines.append(f"\toptions = json.load(f)\n\n")
lines.append(
    f"o = Case('{args.work_dir}', '{args.geomTurbo_file.split('/')[-1]}', **options)"
)
lines.append(f"o.match_blade(N_sections={args.Nsections})")

if bool(args.refine3D):
    lines.append(f"o.refine_3D()")

to_file = "\n".join(lines)

with open(f"container_{args.work_dir}/launch.py", "w") as f:
    f.write(to_file)

sh.copy(f"{init_f_path}/job_PGEOM", f"container_{args.work_dir}/job_PGEOM")

with open(f"container_{args.work_dir}/job_PGEOM", "r") as f:
    data = f.readlines()
data = "".join(data)
data = data.replace("REPLACETHIS", args.work_dir)
with open(f"container_{args.work_dir}/job_PGEOM", "w") as f:
    f.write(data)

os.system(f"rm -rf container_{args.work_dir}/{args.work_dir}")
sh.move(args.work_dir, f"container_{args.work_dir}/{args.work_dir}")
