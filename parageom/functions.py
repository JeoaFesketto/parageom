import os
import sys
import time

import matplotlib.pyplot as plt
import numpy as np

from parablade.blade_match import BladeMatch
from parablade.common.config import ReadUserInput, WriteBladeConfigFile

from parageom.reader import From_param_3D, From_geomTurbo
from parageom.rotor import Rotor
import shutil as sh

# This file has a functional version of all the scripts available in bin/

def match_blade(
    geomTurbo_file, init_config_file, output_folder="blade_match_output/", N_sections=30
):

    DIR = os.getcwd() + "/"

    if not output_folder.endswith("/"):
        output_folder += "/"

    try:
        os.mkdir(DIR + output_folder)
    except:
        print("Writing to existing folder, files might get overwriten")
        if input('\n\n\tProceed? y/n:\t\t') == 'n':
            raise Exception('writing to existing folder')
        os.system(f"rm -rf {DIR+output_folder}output_matching/")

    N_sections_geomTurbo = From_geomTurbo(geomTurbo_file, 'sectioned').rotor_points.shape[1]

    # change this to be able to linearly space the sections geometrically.
    sections = np.array(np.linspace(0, N_sections_geomTurbo-1, N_sections), dtype=int)
    
    sh.copy(
        init_config_file,
        f'{DIR+output_folder}section_-1.cfg'
    )

    for i, section_index in enumerate(sections):
        match_section(
            geomTurbo_file,
            f'{output_folder}section_{i-1}.cfg',
            output_folder=output_folder,
            section_index=section_index
        )
        sh.copy(
            f'{DIR+output_folder}output_matching/matched_parametrization.cfg',
            f'{DIR+output_folder}section_{i}.cfg'
        )
        sh.copy(
            f'{DIR+output_folder}output_matching/optimization_progress.txt',
            f'{DIR+output_folder}section_{i}_iterations.txt'
        )
        os.system(f"rm -rf {DIR+output_folder}output_matching/")




def match_section(
    geomTurbo_file, config_file, output_folder="section_match_output/", section_index=0
):
    DIR = os.getcwd() + "/"

    if not output_folder.endswith("/"):
        output_folder += "/"

    try:
        os.mkdir(DIR + output_folder)
    except:
        print("Writing to existing folder, files might have been overwriten.")

    rotor = Rotor(From_geomTurbo(geomTurbo_file, init="sectioned"))
    rotor.parablade_section_export(
        section_index,
        file=DIR + output_folder + f'{config_file.split("/")[-1][:-3]}txt',
        scale_factor=1e-3,
        dim="3D",
    )

    IN = ReadUserInput(DIR + config_file)
    IN["NDIM"] = [2]
    IN["Config_Path"] = DIR + output_folder + config_file.split("/")[-1]
    IN["PRESCRIBED_BLADE_FILENAME"] = (
        DIR + output_folder + f'{config_file.split("/")[-1][:-3]}txt'
    )
    IN["SCALE_FACTOR"] = rotor.scale_factor

    WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)

    options = {
        "view_xy": "yes",  # 2D Recommended
        "view_xR": "yes",  # 3D Recommended
        "view_yz": "no",  # 3D Optional
        "view_3D": "yes",  # 3D Recommended
        "error_distribution": "yes",
    }

    matched_blade_object = BladeMatch(
        IN, coarseness=1, plot_options=options, _output_path=DIR + output_folder[:-1]
    )

    if not sys._getframe().f_back.f_code.co_name == 'match_blade':
        matched_blade_object.match_blade(matching_mode="manual")

    matched_blade_object.match_blade(matching_mode="DVs")


def make_geomTurbo(
    config_file, output_folder="output_geometry/", LE_fillet=False, TE_fillet=False
):
    DIR = os.getcwd() + "/"

    if not output_folder.endswith("/"):
        output_folder += "/"

    try:
        os.mkdir(DIR + output_folder)
    except:
        print("Writing to existing folder, files might have been overwriten.")

    blade = From_param_3D(DIR + config_file)
    blade.output_geomTurbo(
        DIR + output_folder + config_file.split("/")[-1][:-3] + "geomTurbo",
        LE_fillet,
        TE_fillet,
    )


def show_section(*geomTurbo_files, section = 0, _3Dimensional = False):

    #TODO implement 2D plotting

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

    for i, file in enumerate(geomTurbo_files):
        rotor = Rotor(From_geomTurbo(file, 'sectioned'))

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