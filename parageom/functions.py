import os
import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import shutil as sh

import parablade.init_files.path as pb_path
from parablade.blade_match import BladeMatch
from parablade.common.config import (
    ReadUserInput,
    WriteBladeConfigFile,
    ConfigPasser,
    Scale,
    DeScale,
    Position,
    Angles,
    ConcatenateConfig,
)

from parageom.reader import Param_3D, GeomTurbo
from parageom.rotor import Rotor
import parageom.meshing as ms
from parageom.common import make_output_folder



# This file stores the functions used for the scripts available in bin/
def make_geomTurbo(
    config_file,
    output_folder="output_geometry/",
    N_sections=181,
    N_points=362,
    LE_fillet=False,
    TE_fillet=False,
):
    DIR = os.getcwd() + "/"

    t = time.time()

    make_output_folder(output_folder, warning=False)

    IN = ConfigPasser(DIR + config_file)
    DeScale(IN, in_place=True)

    blade = Param_3D(IN, N_sections=N_sections, N_points=N_points)
    blade.output_geomTurbo(
        f"{DIR}/{output_folder}/{config_file.split('/')[-1][:-3]}geomTurbo",
        LE_fillet,
        TE_fillet,
    )
    print(
        "This was generated in %(my_time).5f seconds\n" % {"my_time": time.time() - t}
    )


def show_section(*geomTurbo_files, span_percentage=0, _3Dimensional=False):

    # TODO implement 2D plotting
    t = time.time()

    ax = plt.axes(projection="3d")
    colors = ["red", "blue", "yellow", "orange", "green", "lime", "pink", "purple"]

    for i, file in enumerate(geomTurbo_files):
        geomTurbo = GeomTurbo(file, "sectioned")
        rotor = Rotor(geomTurbo)
        le_points = geomTurbo.rotor_points[0, :, 0]
        section = _le_section_getter(le_points, span_percentage)

        points = np.vstack(
            (
                rotor.suction_sections[section],
                np.flip(rotor.pressure_sections[section], axis=0),
            )
        )

        ax.plot3D(points.T[0], points.T[2], points.T[1], colors[i])
        print(f"\t\tplotted {file} in {colors[i]}")

        if i == 0:
            le = points[0]
            te = rotor.suction_sections[section, -1]

    ax.set_xlim(le[0] - le[1] / 2, te[0] + le[1] / 2)
    ax.set_zlim(le[1] - 0.3, te[1] + 0.3)
    ax.set_ylim(le[2] - 0.3, te[2] + 0.3)
    ax.set_box_aspect(
        [ub - lb for lb, ub in (getattr(ax, f"get_{a}lim")() for a in "xyz")]
    )

    print(
        "This was generated in %(my_time).5f seconds\n" % {"my_time": time.time() - t}
    )

    plt.show()


def _le_section_getter(le_points, span_percentage):
    target = (le_points[-1] - le_points[0]) * (span_percentage * 0.01) + le_points[0]
    prev = np.linalg.norm(le_points[0] - target)
    i = 1
    while prev > np.linalg.norm(le_points[i] - target):
        prev = np.linalg.norm(le_points[i] - target)
        i += 1
        if i == le_points.shape[0]:
            break
    return i - 1


def prepare_mesh_cfg(trb_file, *cfg, output_folder='to_run'):

    DIR = os.getcwd()

    if output_folder.endswith("/"):
        output_folder = output_folder[:-1]

    make_output_folder(output_folder)

    with open(f'{output_folder}/RUN.ME', 'w') as f: f.write('module load fine/17.1\n')

    for config_file in cfg:
        make_geomTurbo(config_file, output_folder=output_folder, N_sections=100, N_points=100)
        mesh_output_dir = f"{output_folder}/{config_file.split('/')[-1].split('.')[0]}"
        make_output_folder(mesh_output_dir)
        options = {
            '_CASE_NAME_': config_file.split('.')[0],
            '_TEMPLATE_': trb_file,
            '_GEOMTURBO_': f"{DIR}/{output_folder}/{config_file.split('/')[-1][:-3]}geomTurbo",
            '_OUTPUT_DIR_': f'{DIR}/{mesh_output_dir}/'
        }

        script_output_file = f"{output_folder}/ag_script_{config_file.split('.')[0]}.py"
        ms.make_ag_script(options, script_output_file=script_output_file)


        with open(f'{output_folder}/RUN.ME', 'a') as f: 
            f.write(f"igg -autogrid5 -realbatch -script {script_output_file}\n")


# DEPRECATED FUNCTIONS:


def full_match(geomTurbo_file, work_folder, N_sections):
    raise DeprecationWarning(
        "This is deprecated. Use available methods in `case.py` instead."
    )
    initialise_match(geomTurbo_file, work_folder, mode="manual")
    match_blade(
        geomTurbo_file,
        work_folder + "/init.cfg",
        output_folder=work_folder + "/blade_match_output/",
        N_sections=N_sections,
    )
    concatenate_to_blade("blade_match_output", work_folder=work_folder)


def concatenate_to_blade(folder, work_folder="."):
    try:
        os.rename(
            work_folder + "/" + folder + "/section_-01.cfg",
            work_folder + "/" + folder + "/section_-01.old_cfg",
        )
    except:
        print(
            "\nInit config file could not be found, it might have gotten concatenated accidentally.\nCheck number of parameters in concatenated file."
        )

    list_to_concat = [
        ReadUserInput(work_folder + "/" + folder + "/" + file)
        for file in os.listdir(folder)
        if file.endswith(".cfg")
    ]
    final_cfg = ConcatenateConfig(*list_to_concat)
    final_cfg["NDIM"] = 3
    WriteBladeConfigFile(open(work_folder + "/" + "final_output.cfg"), final_cfg)


def initialise_match(geomTurbo_file, work_folder="", mode="manual"):

    raise DeprecationWarning(
        "This is deprecated, use `Case.initialise_case()` " "instead."
    )
    # DIR = os.getcwd()
    path_to_init_files = os.path.dirname(pb_path.__file__)

    if not work_folder.endswith("/"):
        work_folder += "/"

    try:
        os.mkdir(os.getcwd() + "/" + work_folder)
    except:
        print("Writing to existing folder, files might have been overwriten.")

    if mode == "manual":

        init = input(
            "\nChoose blade type:\n\t0 for compressor\n\t1 for turbine\n\nSelected type:\t"
        )

        if int(init):
            sh.copy(path_to_init_files + "/turbine.cfg", work_folder + "init.cfg")
            IN = ConfigPasser(work_folder + "init.cfg")

        else:
            sh.copy(path_to_init_files + "/compressor.cfg", work_folder + "init.cfg")
            IN = ConfigPasser(work_folder + "init.cfg")

        geomTurbo = GeomTurbo(geomTurbo_file, "sectioned")
        le = geomTurbo.rotor_points[0, 0, 0]
        te = geomTurbo.rotor_points[0, 0, -1]
        Position(IN, le, te, in_place=True)
        Angles(IN, le, te, in_place=True)
        WriteBladeConfigFile(open(work_folder + "init.cfg", "w"), IN)

        match_section(
            geomTurbo_file, work_folder + "init.cfg", output_folder=work_folder
        )


def _le_lin_sampler(le_points, d_min):
    indeces = [0]
    last = le_points[0]
    limit = (d_min * 0.01) * np.sum(
        np.linalg.norm(le_points[1:] - le_points[:-1], axis=1)
    )
    for i in range(1, le_points.shape[0]):
        if np.linalg.norm(le_points[i] - last) > limit:
            last = le_points[i]
            indeces.append(i)
    indeces.append(le_points.shape[0] - 1)
    return np.array(indeces)


def match_blade(
    geomTurbo_file, init_config_file, output_folder="blade_match_output/", N_sections=30
):
    raise DeprecationWarning("This is deprecated, use `Case.match_blade` instead.")

    DIR = os.getcwd() + "/"

    if not output_folder.endswith("/"):
        output_folder += "/"

    try:
        os.mkdir(DIR + output_folder)
    except:
        print("Writing to existing folder, files might get overwriten")
        if input("\n\n\tProceed? y/n:\t\t") == "n":
            raise Exception("writing to existing folder")
        os.system(f"rm -rf {DIR+output_folder}output_matching/")

    geomTurbo = GeomTurbo(geomTurbo_file, "sectioned")
    le_points = geomTurbo.rotor_points[0, :, 0]

    # change this to be able to linearly space the sections geometrically.
    sections = _le_lin_sampler(le_points, 100 / (N_sections - 1))

    sh.copy(init_config_file, f"{DIR+output_folder}section_-01.cfg")

    for i, section_index in enumerate(sections):
        match_section(
            geomTurbo_file,
            f"{output_folder}section_{i-1:03d}.cfg",
            output_folder=output_folder,
            section_index=section_index,
        )
        sh.copy(
            f"{DIR+output_folder}output_matching/matched_parametrization.cfg",
            f"{DIR+output_folder}section_{i:03d}.cfg",
        )
        sh.copy(
            f"{DIR+output_folder}output_matching/optimization_progress.txt",
            f"{DIR+output_folder}section_{i:03d}_iterations.txt",
        )
        os.system(f"rm -rf {DIR+output_folder}output_matching/")


def match_section(
    geomTurbo_file, config_file, output_folder="section_match_output/", section_index=0
):
    raise DeprecationWarning("This is deprecated, use `Case.match_section` " "instead.")
    DIR = os.getcwd() + "/"

    if not output_folder.endswith("/"):
        output_folder += "/"

    try:
        os.mkdir(DIR + output_folder)
    except:
        if not sys._getframe().f_back.f_code.co_name == "initialise_match":
            print("Writing to existing folder, files might have been overwriten.")

    rotor = Rotor(GeomTurbo(geomTurbo_file, init="sectioned"))
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
    if "SCALE_FACTOR" in IN and IN["SCALE_FACTOR"] != rotor.scale_factor:
        IN = Scale(IN, scale=rotor.scale_factor, in_place=True)
    elif "SCALE_FACTOR" not in IN:
        IN = Scale(IN, scale=rotor.scale_factor, in_place=True)

    WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)

    if not sys._getframe().f_back.f_code.co_name == "match_blade":
        options = {
            "view_xy": "yes",  # 2D Recommended
            "view_xR": "yes",  # 3D Recommended
            "view_yz": "no",  # 3D Optional
            "view_3D": "yes",  # 3D Recommended
            "error_distribution": "yes",
        }
    else:
        options = {
            "view_xy": "no",  # 2D Recommended
            "view_xR": "no",  # 3D Recommended
            "view_yz": "no",  # 3D Optional
            "view_3D": "no",  # 3D Recommended
            "error_distribution": "no",
        }

    matched_blade_object = BladeMatch(
        IN, coarseness=1, plot_options=options, _output_path=DIR + output_folder[:-1]
    )

    if not sys._getframe().f_back.f_code.co_name == "match_blade":
        matched_blade_object.match_blade(matching_mode="manual")

    if not sys._getframe().f_back.f_code.co_name == "initialise_match":
        matched_blade_object.match_blade(matching_mode="DVs")
