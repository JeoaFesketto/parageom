from warnings import warn
import numpy as np
import parablade as pb
from geomdl import BSpline


class From_geomTurbo:
    def __init__(self, file, scale_factor=1, init="sectioned", xyz="xyz"):

        self.file_path = file
        self.filename = file.split("/")[-1][:-10]
        self.scale_factor = scale_factor
        self.xyz = xyz
        self.rotor_points = None
        self.parameters = None
        self.surfaces = None
        self.curves = None
        self.rotor_edges = None

        if init == "unsectioned":
            self.read_unsectioned_turbo(self.file_path)
        elif init == "sectioned":
            self.read_sectioned_turbo(self.file_path)
        else:
            raise NotImplementedError()

    def read_unsectioned_turbo(self, file_path=None):

        """
        This functions reads a sectioned geomTurbo file and returns a numpy array.

        self.surfaces is a list of 4 np.arrays corresponding to the pressure and suction
        sides of the rotor and the stator.
        For the np.arrays:  axis 0:     the various horizontal sections
                            axis 1:     the cloud of points of the section
                                        (only for one side)
                            axis 2:     each point coordinate

        """

        file = self.file_path if file_path == None else file_path

        with open(file, "r") as f:
            data = [
                " ".join(line.rstrip("\n").replace("\t", " ").split())
                for line in f.readlines()
            ]

        geom = [data[i].split(" ") for i in range(896)]
        igg = data[897:]

        self.rotor_edges = np.array([geom[99:280], geom[283:464]], dtype="float32")
        self.stator_edges = np.array([geom[535:704], geom[707:876]], dtype="float32")
        # TODO trouver un meilleur moyen de chopper les bons indexes

        surfaces_shapes = []
        for i, line in enumerate(igg):
            igg[i] = line.split(" ")
            if igg[i][0].startswith("SISLS"):
                surfaces_shapes.append(list(map(int, igg[i - 1][2:4])))

        curves, i, tmp_curve, adding = [], 0, [], False

        while i < len(igg):
            try:
                igg[i] = list(map(float, igg[i]))
                if len(igg[i]) == 3:
                    if not adding:
                        adding = True
                    tmp_curve.append(igg[i])
                else:
                    if adding:
                        curves.append(np.array(tmp_curve))
                        tmp_curve = []
                        adding = False
            except:
                pass
            i += 1

        curves = list(filter(lambda x: len(x) != 1, curves))
        surfaces, curves = curves[-4:], curves[:-4]

        for i, surface in enumerate(surfaces):
            surfaces[i] = np.array(np.vsplit(surface, surfaces_shapes[i][1]))
            surfaces[i] = surfaces[i].transpose((1, 0, 2))

        self.curves = curves
        self.surfaces = surfaces

        self.rotor_points = [surfaces[0], surfaces[1]]

    def read_sectioned_turbo(self, file_path=None):

        """

        This functions reads a sectioned geomTurbo file and returns a numpy array.

        The output self.rotor_points is structured as follows:

        axis 0:     pressure and suction sides
        axis 1:     the various horizontal sections
        axis 2:     the cloud of points of the section
        axis 3:     the coordinates of the points

        """
        # TODO make it auto to get the number of sections and the number of points
        file = self.file_path if file_path == None else file_path

        with open(file, "r") as f:
            raw_content = f.readlines()

        N_sections = int("".join(raw_content).split("\n")[7])
        N_points = int("".join(raw_content).split("\n")[10])

        content = "".join(raw_content).replace(
            f"pressure\nSECTIONAL\n{N_sections}\n", ""
        )

        content = content.split(f"suction\nSECTIONAL\n{N_sections}\n")[1]
        content = content.split(f"XYZ\n{N_points}\n")
        for i, contour in enumerate(content):
            content[i] = contour.split("\n")
        content = content[1:]

        for i in range(len(content)):
            if i != len(content) - 1:
                content[i] = content[i][:-2]
            else:
                content[i] = content[i][:-1]
            for j in range(len(content[i])):
                content[i][j] = content[i][j].split(" ")

        self.rotor_points = np.array(content, dtype="float").reshape(
            (2, N_sections, N_points, 3)
        )

        if self.xyz != "xyz":
            xyz = self.xyz.replace("x", "0").replace("y", "1").replace("z", "2")
            self.rotor_points = self.rotor_points[
                ..., [int(xyz[0]), int(xyz[1]), int(xyz[2])]
            ]


class From_param_2D:
    def __init__(self, file, no_points=100):

        """

        Creates a tmp rotor from blade parameters. The file path specified should be to
        a camber-thickness cfg file for parablade.

        Parameters
        ----------
        file :          path to the camber thickness .cfg file with the desired blade parameters
        no_points :     scalar of type int with the number of points wanted for each section
                        to later become the dimension N_points in the Rotor object

        """

        blade = pb.Blade2DCamberThickness(file)
        blade.get_section_coordinates(np.linspace(0.00, 1.00, no_points))

        self.rotor_points = [
            np.asarray(blade.pressure_coordinates, dtype="float32"),
            np.asarray(blade.suction_coordinates, dtype="float32"),
        ]

        z_coords = np.zeros((blade.section_coordinates.T.shape[0], 1))
        self.section_coordinates = np.array(
            [np.hstack((blade.section_coordinates.T, z_coords))]
        )

        self.rotor_edges = None


class From_param_3D:
    def __init__(self, file, N_sections=181, N_points=362, UV=None):

        """
        attributes:

            blade_coordinates: ndarray of shape (N_sections, N_points, N_dim)
            with on axis 0: all the sections
                    axis 1: all the points
                    axis 2: the coordinates

            split_coordinates: ndarray of shape(2, N_sections, N_points, N_dim)
            with the suction and pressure side respectively on axis 0.
        """

        blade = pb.Blade3D(file, UV=UV)
        blade.make_blade()

        u = np.linspace(0, 1, N_points)
        V = np.linspace(0, 1, N_sections)

        self.N_blades = blade.IN["N_BLADES"]

        self.N_sections = N_sections
        self.N_points = N_points
        self.blade_coordinates = np.array(
            list(map(lambda v: blade.get_section_coordinates(u, v).T, V))
        )
        # ^ this does this:
        # self.section_coordinates = []
        # for i in v:
        #     self.section_coordinates.append(blade.get_section_coordinates(u, i).T)
        # self.section_coordinates = np.array(self.section_coordinates)

        self.split_coordinates = None

    def output_geomTurbo(
        self, filename="output.geomTurbo", LE_fillet=False, TE_fillet=True
    ):
        """This function outputs a geomTurbo file of the blade ready to be read and used
        in autogrid.


        N_sections: scalar, number of sections.
        N_points: scalar, best if even, odd number of points not yet tested"""

        shape = self.blade_coordinates.shape
        if shape[1] % 2 == 0:
            tmp = self.blade_coordinates
            tmp = tmp.reshape((shape[0], 2, shape[1] // 2, 3))
            tmp[:, 0, -1] = tmp[:, 1, 0]  # matching the trailing edge
        else:
            warn(
                "Odd number of points not yet tested. If problems occur, it might be due to this."
            )
            middle = int(shape[1] / 2 - 0.5)
            tmp = np.insert(
                self.blade_coordinates,
                middle,
                self.blade_coordinates[:, middle, :],
                axis=1,
            )
            tmp = tmp.reshape((shape[0], 2, tmp.shape[1] // 2, 3))
        tmp[:, 1] = np.flip(tmp[:, 1], axis=1)
        tmp[..., [0, 1, 2]] = tmp[..., [1, 2, 0]]

        self.split_coordinates = tmp

        if LE_fillet:
            self.split_coordinates = self._LE_fillet(self.split_coordinates)
        if TE_fillet:
            self.split_coordinates = self._TE_fillet(self.split_coordinates)

        self.write_geomTurbo(filename)

    def _LE_fillet(self, point_cloud, N_le=80, min_width=0.8, min_angle=np.deg2rad(15)):
        """
        Sub-function that rounds the leading edge based on a couple parameters.
        The defaults seem to work quite well.

        N_le is the number of newly generated points at the leading edge.
        min_width is the width of the blade under which the blade will be cut.

        With p1 the point along the section surface at which the blade is to be cut, the angle alpha
        corresponds to the angle between the tangent to the surface at p1 and the line between
        p1 and the leading edge point.

        min_angle is the threshold before which the leading edge is moved in to shorten the blade
        and reduce the angle.
        min_angle should be input in radians.

        """
        # NOTE there is a slight problem with the number of points.
        # the array is expanded by N_le-1 points actually...

        tmp = point_cloud
        final_array = np.zeros((tmp.shape[0], 2, tmp.shape[2] + N_le - 1, 3))

        for k, section in enumerate(tmp):

            i = 1
            while _dist(*section[:, i]) < min_width:
                i += 1
                elem = section[:, i]

            suction_curve = BSpline.Curve()
            pressure_curve = BSpline.Curve()
            suction_curve.degree = 2
            pressure_curve.degree = 2

            le = section[0, 0]
            tangent_vectors = section[:, i] - section[:, i + 1]
            normal_vector = section[0, i] - section[1, i]
            ce = section[1, i] + 1 / 2 * normal_vector

            if np.min(_angle(tangent_vectors, le - section[:, i])) < min_angle:
                j = 1
                while (
                    np.min(
                        _angle(tangent_vectors, _centre(*section[:, j]) - section[:, i])
                    )
                    < min_angle
                ):
                    j += 1
                le = _centre(*section[:, j])

            suction_ctrl = _get_intersect(
                le, section[0, i], tangent_vectors[0], le - ce
            )
            pressure_ctrl = _get_intersect(
                le, section[1, i], tangent_vectors[1], le - ce
            )

            suction_curve.ctrlpts = [list(elem[0]), suction_ctrl, list(le)]
            pressure_curve.ctrlpts = [list(elem[1]), pressure_ctrl, list(le)]

            suction_curve.knotvector = [0, 0, 0, 2, 2, 2]
            pressure_curve.knotvector = [0, 0, 0, 2, 2, 2]

            suction_curve.delta = 1 / (N_le + i)
            pressure_curve.delta = 1 / (N_le + i)

            new_head = np.array(
                [
                    np.flip(suction_curve.evalpts, axis=0),
                    np.flip(pressure_curve.evalpts, axis=0),
                ]
            )

            final_array[k, :] = np.concatenate((new_head, tmp[k, :, i + 1 :]), axis=1)

        self.N_points += 2 * (N_le - 1)
        return final_array

    def _TE_fillet(self, point_cloud, N_te=80, min_width=0.5, min_angle=np.deg2rad(6)):
        """
        Sub-function that rounds the trailing edge based on a couple parameters.
        The defaults seem to work quite well.

        N_te is the number of newly generated points at the trailing edge.
        min_width is the width of the blade under which the blade will be cut.

        With p1 the point along the section surface at which the blade is to be cut, the angle alpha
        corresponds to the angle between the tangent to the surface at p1 and the line between
        p1 and the trailing edge point.

        min_angle is the threshold before which the trailing edge is moved in to shorten the blade
        and reduce the angle.
        min_angle should be input in radians.

        """

        tmp = point_cloud
        final_array = np.zeros((tmp.shape[0], 2, tmp.shape[2] + N_te, 3))

        for k, section in enumerate(tmp):

            i = 1
            while _dist(*section[:, -i]) < min_width:
                i += 1
                elem = section[:, -i]

            suction_curve = BSpline.Curve()
            pressure_curve = BSpline.Curve()
            suction_curve.degree = 2
            pressure_curve.degree = 2

            te = section[0, -1]
            tangent_vectors = section[:, -i] - section[:, -i - 1]
            normal_vector = section[0, -i] - section[1, -i]
            ce = section[1, -i] + 1 / 2 * normal_vector

            if np.min(_angle(tangent_vectors, te - section[:, -i])) < min_angle:
                j = 1
                while (
                    np.min(
                        _angle(
                            tangent_vectors, _centre(*section[:, -j]) - section[:, -i]
                        )
                    )
                    < min_angle
                ):
                    j += 1
                te = _centre(*section[:, -j])

            suction_ctrl = _get_intersect(
                te, section[0, -i], tangent_vectors[0], te - ce
            )
            pressure_ctrl = _get_intersect(
                te, section[1, -i], tangent_vectors[1], te - ce
            )

            suction_curve.ctrlpts = [list(elem[0]), suction_ctrl, list(te)]
            pressure_curve.ctrlpts = [list(elem[1]), pressure_ctrl, list(te)]

            suction_curve.knotvector = [0, 0, 0, 2, 2, 2]
            pressure_curve.knotvector = [0, 0, 0, 2, 2, 2]

            suction_curve.delta = 1 / (N_te + i)
            pressure_curve.delta = 1 / (N_te + i)

            new_tail = np.array([suction_curve.evalpts, pressure_curve.evalpts])

            final_array[k, :] = np.concatenate((tmp[k, :, :-i], new_tail), axis=1)

        self.N_points += 2 * N_te
        return final_array

    def write_geomTurbo(self, filename="output.geomTurbo"):
        lines = [
            "GEOMETRY TURBO VERSION 5",
            f"number_of_blades {int(self.N_blades[0])}",
            "blade_expansion_factor_hub  0.01",
            "blade_expansion_factor_shroud 0.01",
            "blade_tangential_definition	  0",
        ]

        for k, side in enumerate(["suction", "pressure"]):
            lines.append(side)
            lines.append("SECTIONAL")
            lines.append(str(self.split_coordinates.shape[0]))

            for i, section in enumerate(self.split_coordinates[:, k]):
                lines.append(f"# section {i+1}")
                lines.append("XYZ")
                lines.append(str(self.split_coordinates.shape[2]))

                for point in np.asarray(
                    np.asarray(section, dtype="float"), dtype="str"
                ):
                    lines.append(" ".join(point))

        with open(filename, "w") as f:
            f.write("\n".join(lines))
            f.write("\n")  # don't remove it


# Functions used in _LE_fillet and _TE_fillet.


def _dist(p1, p2):
    return np.linalg.norm(p2 - p1)


def _angle(v1, v2):
    """
    Gets the angle between vector elements of two similar sized arrays.
    Returns:
        numpy.ndarray of shape N_vectors
    """
    return np.arccos(
        np.diag(np.tensordot(v1, v2, axes=[1, 1]))
        / (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1))
    )


def _centre(p1, p2):
    return p1 + (p2 - p1) / 2


def _get_intersect(p1, p2, v1, n):
    n_hat = n / np.linalg.norm(n)
    k = np.matmul(p1.T, n_hat)
    t = (k - np.dot(p2, n_hat)) / np.dot(v1, n_hat)
    return list(p2 + t * v1)
