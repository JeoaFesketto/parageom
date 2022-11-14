import errno
import os
from warnings import warn

import numpy as np
import shutil as sh
import json

import parablade.init_files.path as pb_path
import parablade.common.config as cfg
from parablade.blade_match import BladeMatch

from parageom.reader import GeomTurbo
from parageom.rotor import Rotor


class Case:

    """
    `Case` object for matching blade geometries with various parameters.

    Parameters
    ----------
    work_dir : string
        Relative path of the directory from wich to take inputs or, alternatively to be created.
        If the directory already exists and an init.cfg file is inside it, it will be used as the init
        file where required. 
        If the directory does not exist, it will be created and the required files will be written inside.
    geomTurbo_file : string
        Path to the .geomTurbo file that contains the geometry from which to make the parablade setions.
        The .geomTurbo must be a sectioned one ie. created in Autogrid directly by outputting the geometry of the 
        rotor.

    Returns
    -------
    out : Case
        `Case` object from which a geometry can be matched.

    Other Parameters
    ----------------
    **kwargs : dict , optional
        Advanced options for blade matching methods.
        interactive :       require, or not, the user to take actions during code execution (including closing plots).
                            Therefore, if this is off, no graphs will be outputted. This option is forced off when
                            `on_hpc` is on. Default: True
        overwrite :         allow overwriting of files when writing results. If this is off, and oerwriting is required,
                            the code will raise an error. Default: True
        auto_concatenate :  automatically concatenate the resulting cfg files of each section. Default: True
        on_hpc :            for running the code on an hpc, will silence the `interactive` option and force `overwrite`
                            off. Default: False
        scale_factor :      set the scale factor to that of the .geomTurbo file. eg: 1e-3 for mm. 
                            Default: 1e-3
        xyz :               coordinates reordering for the optimization process if necessary. eg: 'zyx', 'xzy', etc...
                            Default: 'xyz'
        optim_max_iter :    max number of iterations during optimization. Number will be increased if retries are
                            necessary. Default: 300
        optim_convergence_max_dev_rel :
                            threshold for the maximum relative deviation between the prescribed and the matched point
                            clouds before optimization is stopped. Default: 0.4
        optim_convergence_mean_dev_rel :
                            threshold for the mean relative deviation between the prescribed and the matched point
                            clouds before optimization is stopped. Default: 0.1
        optim_uv_method :   method to be used for uv optimization. Check `scipy.optimize.minimize` documentation.
                            Default: 'L-BFGS-B'
        optim_dv_method :   method to be used for design variables optimization. Check `scipy.optimize.minimize` 
                            documentation. Default: 'SLSQP'
        optim_max_retries_slsqp:
                            number of times the optimization is allowed to retry after exiting due to code 4: 
                            incompatible inequality constraints, when running slsqp. Default: 1
        transfer_position : automatically set the position of the leading and trailing edges of in the cfg file based
                            on the coordinates from the .geomTurbo file. This will also adapt the stagger angle to
                            match the trailing edge y coordinate. Default: True
        fatten :            fatten the blade profile in the cfg file when initialising for a section. Turn this on in
                            case the optimization yields bad results. Default: False
    
    """

    DIR = os.getcwd()

    defaults = {
        # case parameters
        "interactive": True,
        "overwrite": True,  # allow overwrite
        "auto_concatenate": True,
        "on_hpc": False,  # will force interactive off and overwrite on
        # geomTurbo parameters
        "scale_factor": 1e-3,  # optimization works best if dims are in meters.
        "xyz": "xyz",  # order of the coordinates in the geomTurbo file: chord, thickness, span
        # optimization parameters
        "optim_max_iter": 300,  # max number of iterations for one section
        "optim_convergence_max_dev_rel": 0.4,  # values in % for the convergence criteria.
        "optim_convergence_mean_dev_rel": 0.1,
        # advanced optim parameters.
        "optim_uv_method": "L-BFGS-B",  # check scipy doc for optimization methods.
        "optim_dv_method": "SLSQP",
        "optim_max_retries_slsqp": 1,
        "transfer_position": True,
        "fatten": False,
    }

    def __init__(self, work_dir, geomTurbo_file, **kwargs):

        self.work_dir = work_dir
        self.output_path = f"{self.work_dir}/blade_match_output"
        self.init_config_file = None
        self.residuals = None

        for key, value in Case.defaults.items():
            if key in kwargs:
                if type(value) == type(kwargs[key]):
                    setattr(self, key, kwargs[key])
                else:
                    warn(
                        f"value for `{key}` was set to `{kwargs[key]}`, "
                        f"of type {type(kwargs[key])} "
                        f"but should be of type {type(value)}. "
                        "Value was still set but this might cause errors."
                    )
                    setattr(self, key, kwargs[key])
            elif key not in kwargs:
                setattr(self, key, value)

        if self.on_hpc:
            self.interactive = False
            self.overwrite = True

        for key in kwargs:
            if key not in Case.defaults:
                warn(f"`{key}` is not an option and will be ignored.")

        self.geomTurbo = GeomTurbo(geomTurbo_file, self.scale_factor, xyz=self.xyz)

        try:
            os.mkdir(f"{Case.DIR}/{work_dir}")
        except:
            if self.overwrite:
                print("Will be writing to existing folder.")
            else:
                raise Exception(
                    "`overwrite` option is set to False and folder already exists."
                )

        output_dir = "blade_match_output"
        output_path = f"{self.work_dir}/{output_dir}"
        self.output_path = output_path

        try:
            os.mkdir(f"{output_path}/")
            os.mkdir(f"{output_path}/residuals/")
        except OSError as exc:
            if exc.errno == errno.EEXIST and self.overwrite:
                warn(
                    "Writing results to existing directory but `overwrite` is True, code will proceed."
                )
                os.system(f"rm -rf {self.work_dir}/output_matching")
                # os.system(f"rm -rf {output_path}")
                # os.mkdir(f"{output_path}/")
                # os.mkdir(f"{output_path}/residuals/")
            elif exc.errno == errno.EEXIST and not self.overwrite:
                raise Exception(
                    "`overwrite` is set to False and folder already exists."
                )
            else:
                raise

    def initialise_case(self, template=None):
        """
        Method to initialise a `Case` ie. create the init .cfg file to be used for the optimization process.
        If `Case.interactive` is True, the user will be prompted for manual blade matching.
        It writes a .cfg file to the `Case.work_dir` directory from which to start the matching process.

        Parameters
        ----------
        template : None, int or string
            Template on which to base the initialization .cfg file. This can be the path to a .cfg file as a string, a
            string, an int to specify one of the presets or None. If `template` is None, the method will look for a
            file specificaly named `init.cfg` in the working directory specified when initialising the case object with
            `work_dir`. Else and if `Case.interactive` is True, the user will be prompted to select one of the possible
            presets available in the parablade.init_files directory.
        """

        init_f_path = os.path.dirname(pb_path.__file__)

        if template is not None:
            pass
        elif "init.cfg" in os.listdir(self.work_dir):
            template = f"{self.work_dir}/init.cfg"
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

        _initialise_cfg(IN, self.geomTurbo, self.work_dir, 0, True)
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
            optim_object.match_blade(matching_mode="manual_sliders")

        IN = cfg.ReadUserInput(IN["Config_Path"])
        cfg.DeScale(IN, True)
        cfg.WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)

        self.init_config_file = IN["Config_Path"]

    def match_section(self, config_file, section_idx, _match_blade=False):

        """
        Outputs a config file that corresponds to a specified section of the `Case.geomTurbo_file` geometry file from a
        initial config file `config_file`.

        Parameters
        ----------
        config_file : string
            Relative path to a config file to be used to initialise the optimization process.
        section_idx : int
            Index corresponding to that inside the geomTurbo file to be matched.

        Returns
        -------
        None

        Other Parameters
        ----------------
        _match_blade : bool, optional
            Not for user. Set to True if called inside `Case.match_blade`.
        """

        IN = cfg.ReadUserInput(config_file)
        name = config_file.split("/")[-1][:-4]

        if name == "section_-01" or not _match_blade:
            _initialise_cfg(
                IN,
                self.geomTurbo,
                self.output_path,
                section_idx,
                self.transfer_position,
                name,
            )
        else:
            _initialise_cfg(
                IN,
                self.geomTurbo,
                self.output_path,
                section_idx,
                self.transfer_position,
                self.fatten,
                name,
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
            **{
                f"_{key}": getattr(self, key)
                for key in Case.defaults
                if key.startswith("optim")
            },
        )

        if self.interactive and not _match_blade:
            cfg.WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)
            optim_object.match_blade(matching_mode="manual")
            optim_object.match_blade(matching_mode="manual_sliders")

        optim_object.match_blade(matching_mode="DVs")

    def match_blade(self, init_config_file=None, N_sections=5):

        """
         
        """

        if init_config_file is None:
            if self.init_config_file is not None:
                init_config_file = self.init_config_file
            elif "init.cfg" in os.listdir(self.work_dir):
                init_config_file = f"{self.work_dir}/init.cfg"
                self.init_config_file = init_config_file
            else:
                raise ValueError(
                    "Init config file not specified and not " "found in object."
                )

        # TODO change this try, it's unacceptable
        try:
            os.system(f"rm -rf {self.output_path}")
            os.mkdir(f"{self.output_path}/")
            os.mkdir(f"{self.output_path}/residuals/")
        except:
            pass

        le_points = self.geomTurbo.rotor_points[0, :, 0]

        sections = _le_lin_sampler(le_points, 100 / (N_sections - 1))
        json.dump(
            {"geomTurbo_section_indeces": list(np.asarray(sections, dtype=float))},
            open(f"{self.work_dir}/sections.json", "w"),
        )

        sh.copy(init_config_file, f"{self.output_path}/section_{-1:03d}.cfg")

        for i, section_index in enumerate(sections):

            self.match_section(
                f"{self.output_path}/section_{i-1:03d}.cfg",
                section_index,
                _match_blade=True,
            )

            sh.copy(
                f"{self.work_dir}/output_matching/matched_parametrization.cfg",
                f"{self.output_path}/section_{i:03d}.cfg",
            )
            sh.copy(
                f"{self.work_dir}/output_matching/optimization_progress.txt",
                f"{self.output_path}/residuals/section_{i:03d}_iterations.txt",
            )

            os.system(f"rm -rf {self.work_dir}/output_matching")

        try:
            os.remove(f"{self.output_path}/section_-01.cfg")
        except FileNotFoundError:
            warn(
                "Init config file not found anymore. "
                "If it is present under a different name, "
                "it might have gotten concatenated with the rest."
            )
        except:
            raise
        try:
            os.remove(f"{self.output_path}/section_-01.txt")
        except FileNotFoundError:
            warn("Init prescribed geometry file not found anymore.")
        except:
            raise

        self.residuals = self.get_residuals()

        if self.auto_concatenate:

            list_to_concat = [
                cfg.ReadUserInput(f"{self.output_path}/{file}")
                for file in sorted(os.listdir(self.output_path))
                if file.endswith(".cfg")
            ]

            final_cfg = cfg.ConcatenateConfig(*list_to_concat)
            final_cfg["NDIM"] = 3
            final_cfg["N_SECTIONS"] = sections.shape[0]

            cfg.WriteBladeConfigFile(
                open(
                    f"{self.work_dir}/{self.geomTurbo.filename}_parametrized.cfg", "w"
                ),
                final_cfg,
            )

    def refine(self, mean_deviation_threshold, max_deviation_threshold):
        """This method allows the user to refine the sections that are not well converged enough."""

        if not self.interactive:
            raise NotImplementedError()

        if self.residuals is None:
            self.residuals = self.get_residuals(False)

        geomTurbo_sections = json.load(open(f"{self.work_dir}/sections.json", "r"))[
            "geomTurbo_section_indeces"
        ]
        geomTurbo_sections = list(map(int, geomTurbo_sections))

        self.convergence_max_dev_rel = max_deviation_threshold
        self.convergence_mean_dev_rel = mean_deviation_threshold

        modded = []
        for i, section in enumerate(self.residuals):
            if (section[-1][-2] > mean_deviation_threshold) or (
                section[-1][-1] > max_deviation_threshold
            ):
                print(f"Section {i} needs refining")
                sh.copy(
                    f"{self.output_path}/section_{i:03d}.cfg",
                    f"{self.output_path}/new_section_{i:03d}.cfg",
                )

                IN = cfg.ReadUserInput(f"{self.output_path}/new_section_{i:03d}.cfg")

                _initialise_cfg(
                    IN,
                    self.geomTurbo,
                    self.output_path,
                    geomTurbo_sections[i],
                    self.transfer_position,
                    self.fatten,
                    name=f"new_section_{i:03d}",
                )

                plot_options = {
                    "view_xy": "yes",  # 2D Recommended
                    "view_xR": "yes",  # 3D Recommended
                    "view_yz": "no",  # 3D Optional
                    "view_3D": "yes",  # 3D Recommended
                    "error_distribution": "yes",
                }
                os.system(f"rm -rf {self.work_dir}/output_matching")
                optim_object = BladeMatch(
                    IN,
                    coarseness=1,
                    plot_options=plot_options,
                    _output_path=f"{Case.DIR}/{self.work_dir}",
                    **{
                        f"_{key}": getattr(self, key)
                        for key in Case.defaults
                        if key.startswith("optim")
                    },
                )

                cfg.WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)
                # optim_object.match_blade(matching_mode="manual")
                optim_object.match_blade(matching_mode="manual_sliders")

                optim_object.match_blade(matching_mode="DVs")
                modded.append(i)

                sh.copy(
                    f"{self.work_dir}/output_matching/matched_parametrization.cfg",
                    f"{self.output_path}/new_section_{i:03d}.cfg",
                )
                try:
                    os.remove(
                        f"{self.output_path}/residuals/section_{i:03d}_iterations.txt"
                    )
                except:
                    pass

                sh.copy(
                    f"{self.work_dir}/output_matching/optimization_progress.txt",
                    f"{self.output_path}/residuals/section_{i:03d}_iterations.txt",
                )
                os.system(f"rm -rf {self.work_dir}/output_matching")

        answer = ""
        while answer not in ["y", "n", "yes", "no"]:
            answer = input("\n\n\tOverwrite with new cfg files? \ny/n:\t\t")

        if answer in ["y", "yes"]:
            for i in modded:
                os.remove(f"{self.output_path}/section_{i:03d}.cfg")
                sh.copy(
                    f"{self.output_path}/new_section_{i:03d}.cfg",
                    f"{self.output_path}/section_{i:03d}.cfg",
                )
                os.remove(f"{self.output_path}/new_section_{i:03d}.cfg")

        self.get_residuals()

    def refine_3D(self):

        points = []

        for file in os.listdir(self.output_path):
            if file.endswith(".txt"):
                points.append(np.loadtxt(f"{self.output_path}/{file}"))

        final = np.stack(tuple(points), axis=0)
        final = final.reshape((-1, 4))
        final = final[:, [0, 3, 2, 1]]
        np.savetxt(f"{self.work_dir}/3D_points.txt", final, delimiter="\t")

        file = [
            file
            for file in os.listdir(self.work_dir)
            if file.endswith("parametrized.cfg")
        ][0]

        IN = cfg.ReadUserInput(f"{self.work_dir}/{file}")
        cfg.Scale(IN, scale=self.scale_factor, in_place=True)
        IN["N_SECTIONS"] = [len(points)]
        IN["PRESCRIBED_BLADE_FILENAME"] = f"{self.work_dir}/3D_points.txt"
        IN["Config_Path"] = f"{self.work_dir}/3D_parametrized.cfg"
        cfg.WriteBladeConfigFile(open(IN["Config_Path"], "w"), IN)

        if self.interactive:
            plot_options = {
                "view_xy": "yes",
                "view_xR": "no",
                "view_yz": "no",
                "view_3D": "no",
                "error_distribution": "no",
            }
        else:
            plot_options = {
                "view_xy": "no",
                "view_xR": "no",
                "view_yz": "no",
                "view_3D": "no",
                "error_distribution": "no",
            }

        o = BladeMatch(
            IN,
            coarseness=1,
            plot_options=plot_options,
            _output_path=f"{Case.DIR}/{self.work_dir}",
            **{
                f"_{key}": getattr(self, key)
                for key in Case.defaults
                if key.startswith("optim")
            },
        )
        o.match_blade("DVs")
        # TODO finish copying the file back to where it needs to be
        # sh.copy(f'{self.work_dir}/output_matching/')

    def get_residuals(self, print_residuals=True):
        residuals = []
        for file in sorted(os.listdir(f"{self.output_path}/residuals")):
            if file.endswith("s.txt"):
                with open(f"{self.output_path}/residuals/{file}", "r") as f:
                    data = list(
                        map(lambda x: x.rstrip("\n").split(" \t "), f.readlines()[1:])
                    )
                    data = list(map(lambda x: list(map(lambda y: float(y), x)), data))
                residuals.append(data)

        if print_residuals:
            print(
                "\n Iteration \t Mean deviation (m) \t Maximum deviation (m) \t Mean deviation (%) \t Maximum deviation (%)"
            )
            for i, residual in enumerate(residuals):
                print(f"\nSection {i}:")
                for iteration in residual[-1:]:
                    for element in iteration:
                        print(element, end=" \t ")
                    print()

        return residuals


def _initialise_cfg(
    IN,
    geomTurbo,
    output_path,
    section_idx,
    transfer_position=True,
    fatten=False,
    name=None,
):

    if transfer_position:
        le = geomTurbo.rotor_points[0, section_idx, 0]
        te = geomTurbo.rotor_points[0, section_idx, -1]
        cfg.Position(IN, le, te, in_place=True)
    if fatten:
        cfg.Fatten(IN, in_place=True)

    name = "init" if name is None else name

    rotor = Rotor(geomTurbo)
    rotor.parablade_section_export(
        section_idx,
        file=f"{output_path}/{name}.txt",
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
