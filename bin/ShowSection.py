#!/usr/bin/env python3
import os
import argparse
import time

import matplotlib.pyplot as plt
import numpy as np

from parageom.common import print_parageom
from parageom.reader import From_geomTurbo
from parageom.rotor import Rotor

print_parageom()

# ARGUMENT DEFINITION

parser = argparse.ArgumentParser(
    description="Plot a specified section of one or more geomTurbo files"
)
parser.add_argument(
    "geomTurbo_files",
    help="geomTurbo files to plot.",
    type=str,
    nargs='+'
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
    action='count',
    default=0
)

def _le_section_getter(le_points, span_percentage):

    target = (le_points[-1]-le_points[0])*(span_percentage*0.01)+le_points[0]

    prev = np.linalg.norm(le_points[0]-target)

    i = 1
    while prev > np.linalg.norm(le_points[i]-target):
        prev = np.linalg.norm(le_points[i]-target)
        i+=1
        if i == le_points.shape[0]:
            break

    return i-1

args = parser.parse_args()

t = time.time()

ax = plt.axes(projection="3d")
colors = [
    'red',
    'blue',
    'yellow',
    'orange',
    'green',
    'lime',
    'pink',
    'purple'
]

for i, file in enumerate(args.geomTurbo_files):

    geomTurbo = From_geomTurbo(file, "sectioned")
    rotor = Rotor(geomTurbo)
    le_points = geomTurbo.rotor_points[0, :, 0]
    section = _le_section_getter(le_points, args.span_percentage)

    points = np.vstack(
        (rotor.suction_sections[section], np.flip(rotor.pressure_sections[section], axis = 0))
    )


    ax.plot3D(points.T[0], points.T[2], points.T[1], colors[i])
    print(f'\t\tplotted {file} in {colors[i]}')

    if i == 0:
        le = points[0]
        te = rotor.suction_sections[section, -1]

ax.set_xlim(le[0]-le[1]/2, te[0]+le[1]/2)
ax.set_zlim(le[1]-0.3, te[1]+0.3)
ax.set_ylim(le[2]-0.3, te[2]+0.3)
ax.set_box_aspect(
    [ub - lb for lb, ub in (getattr(ax, f"get_{a}lim")() for a in "xyz")]
)

print('This was generated in %(my_time).5f seconds\n' % {'my_time': time.time() - t})

plt.show()