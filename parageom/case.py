import errno
import os
from warnings import warn

import numpy as np
import shutil as sh

import parablade.init_files.path as pb_path
import parablade.common.config as cfg
from parablade.blade_match import BladeMatch

from parageom.reader import From_geomTurbo
from parageom.rotor import Rotor


class Case:

    DIR = os.getcwd()

    defaults = {
        "optimization_max_iter": 300, # max number of iterations for one section
        "convergence_max_dev_rel": 0.4, # values in % for the convergence criteria.
        "convergence_mean_dev_rel": 0.1,
        "scale_factor": 1e-3,  # optimization works best if dims are in meters.

        "interactive": True,
        "auto_concatenate": True,

        "on_hpc": False,
        "overwrite": True,  # allow overwrite
    }

    def __init__(self, work_dir, geomTurbo_file, **kwargs):

        self.work_dir = work_dir
        self.output_path = self.work_dir
        self.init_config_path = None

        for key, value in Case.defaults.items():
            if key in kwargs and type(value) == type(kwargs[key]):
                setattr(self, key, kwargs[key])
            else:
                setattr(self, key, value)
        
        if self.on_hpc:
            self.interactive = False
            self.overwrite = True

        for key in kwargs:
            if key not in Case.defaults:
                warn(f"`{key}` is not an option and will be ignored.")

        self.geomTurbo = From_geomTurbo(geomTurbo_file, self.scale_factor)

        try:
            os.mkdir(f'{Case.DIR}/{work_dir}')
        except:
            if self.overwrite:
                print("Writing to existing folder.")
            else:
                raise Exception(
                    "`overwrite` option is set to False and folder already exists."
                )
        

    def initialise_case(self, template=None):

        init_f_path = os.path.dirname(pb_path.__file__)

        if template is not None:
            pass
        elif self.interactive:
            template = input(
                "\nChoose blade type:\n\t0 for compressor\n\t1 for turbine\n\nSelected type:\t"
            )
        else:
            print("\nNo template chosen for initialisation, choosing compressor.cfg.\n")
            template = 0

        if str(template).endswith(".cfg"):
            pass
        elif template in ["compressor", "Compressor", 0, "0"]:
            template = init_f_path + "/compressor.cfg"
        elif template in ["turbine", "Turbine", 1, "1"]:
            template = init_f_path + "/turbine.cfg"

        try:
            sh.copy(template, f"{self.work_dir}/init.cfg")
        except sh.SameFileError:
            pass
        except:
            raise

        IN = cfg.ConfigPasser(f"{self.work_dir}/init.cfg")

        _initialise_cfg(IN, self.geomTurbo, self.work_dir, 0, True, True)
        cfg.WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)

        if self.interactive:
            plot_options = {
                "view_xy": "yes",  # 2D Recommended
                "view_xR": "yes",  # 3D Recommended
                "view_yz": "no",  # 3D Optional
                "view_3D": "yes",  # 3D Recommended
                "error_distribution": "yes",
            }
            optim_object = BladeMatch(
                IN,
                coarseness=1,
                plot_options=plot_options,
                _output_path=f"{Case.DIR}/{self.work_dir}",
                _no_subfolder=True,
            )
            optim_object.match_blade(matching_mode="manual")
        
        self.init_config_path = IN["Config_Path"]

    def match_section(
        self, config_file, section_idx, transfer_position=True, transfer_angles=False, _match_blade=False
    ):

        IN = cfg.ReadUserInput(config_file)
        _initialise_cfg(
            IN, self.geomTurbo, self.output_path, 
            section_idx, transfer_position, transfer_angles, name=config_file.split('/')[-1][:-4],
            scale_factor=self.scale_factor
        )

        if self.interactive:
            plot_options = {
                "view_xy": "yes",  # 2D Recommended
                "view_xR": "yes",  # 3D Recommended
                "view_yz": "no",  # 3D Optional
                "view_3D": "yes",  # 3D Recommended
                "error_distribution": "yes",
            }
        else:
            plot_options = {
                "view_xy": "no",
                "view_xR": "no",
                "view_yz": "no",
                "view_3D": "no",
                "error_distribution": "no",
            }

        optim_object = BladeMatch(
            IN,
            coarseness=1,
            plot_options=plot_options,
            _output_path=f"{Case.DIR}/{self.work_dir}",
            _optimization_max_iter=self.optimization_max_iter,
            _convergence_max_dev_rel=self.convergence_max_dev_rel,
            _convergence_mean_dev_rel=self.convergence_mean_dev_rel
        )

        if self.interactive and not _match_blade:
            cfg.WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)
            optim_object.match_blade(matching_mode="manual")

        optim_object.match_blade(matching_mode="DVs")

    def match_blade(self, init_config_file, N_sections):
        output_dir = "blade_match_output"
        output_path = f"{self.work_dir}/{output_dir}"
        self.output_path = output_path

        try:
            os.mkdir(f"{output_path}/")
        except OSError as exc:
            if exc.errno == errno.EEXIST and self.overwrite:
                warn(
                    "Writing results to existing directory but `overwrite` is True, code will proceed."
                )
                os.system(f"rm -rf {self.work_dir}/output_matching")
                os.system(f"rm -rf {self.work_dir}/{output_dir}")
                os.mkdir(f"{output_path}/")
            elif exc.errno == errno.EEXIST and not self.overwrite:
                raise Exception(
                    "`overwrite` is set to False and folder already exists."
                )
            else:
                raise

        le_points = self.geomTurbo.rotor_points[0, :, 0]

        sections = _le_lin_sampler(le_points, 100 / (N_sections - 1))

        sh.copy(init_config_file, f"{output_path}/section_{-1:03d}.cfg")

        for i, section_index in enumerate(sections):

            self.match_section(
                f"{output_path}/section_{i-1:03d}.cfg", section_index, _match_blade=True
            )

            sh.copy(
                f"{self.work_dir}/output_matching/matched_parametrization.cfg",
                f"{output_path}/section_{i:03d}.cfg",
            )
            sh.copy(
                f"{self.work_dir}/output_matching/optimization_progress.txt",
                f"{output_path}/section_{i:03d}_iterations.txt",
            )

            os.system(f"rm -rf {self.work_dir}/output_matching")
        
        try:
            os.remove(f'{output_path}/section_-01.cfg')
        except FileNotFoundError:
            warn(
                'Init config file not found anymore. ' 
                'If it is present under a different name, '
                'it might have gotten concatenated with the rest.'
            )
        except:
            raise
        try:
            os.remove(f'{output_path}/section_-01.txt')
        except FileNotFoundError:
            warn(
                'Init prescribed geometry file not found anymore.' 
            )
        except:
            raise
    
        list_to_concat = [
            cfg.ReadUserInput(f'{output_path}/{file}') for file
            in os.listdir(output_path) if file.endswith('.cfg')
        ]

        final_cfg = cfg.ConcatenateConfig(*list_to_concat)
        final_cfg['NDIM'] = 3

        cfg.WriteBladeConfigFile(
            open(f'{self.work_dir}/{self.geomTurbo.filename}_parametrized.cfg', 'w'),
            final_cfg
        )
            

    def full_match(self):
        raise NotImplementedError


def _initialise_cfg(IN, geomTurbo, output_path, section_idx, transfer_position=True, transfer_angles=False, name=None, scale_factor=1):

    if transfer_position or transfer_angles:
        le = geomTurbo.rotor_points[0, section_idx, 0]
        te = geomTurbo.rotor_points[0, section_idx, -1]
        if transfer_position:
            cfg.Position(IN, le, te, in_place=True)
        if transfer_angles:
            cfg.Angles(IN, le, te, in_place=True)

    name = 'init' if name is None else name

    rotor = Rotor(geomTurbo)
    rotor.parablade_section_export(
        section_idx,
        file=f'{output_path}/{name}.txt',
        dim="3D",
    )

    IN["NDIM"] = [2]
    IN["Config_Path"] = f"{Case.DIR}/{output_path}/{name}.cfg"
    IN["PRESCRIBED_BLADE_FILENAME"] = f"{Case.DIR}/{output_path}/{name}.txt"
    if "SCALE_FACTOR" in IN and IN["SCALE_FACTOR"] != geomTurbo.scale_factor:
        IN = cfg.Scale(IN, scale=geomTurbo.scale_factor, in_place=True)
    elif "SCALE_FACTOR" not in IN:
        IN = cfg.Scale(IN, scale=geomTurbo.scale_factor, in_place=True)


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
