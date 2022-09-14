import numpy as np
import parablade as pb


class From_geomTurbo:
    def __init__(self, file, init="unsectioned"):

        self.file_path = file
        self.rotor_points = None
        self.parameters = None
        self.surfaces = None
        self.curves = None

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

        file = self.file_path if file_path == None else file_path

        with open(file, "r") as f:
            content = "".join(f.readlines()).replace("pressure\nSECTIONAL\n181\n", "")

        content = content.split("suction\nSECTIONAL\n181\n")[1]
        content = content.split("XYZ\n181\n")
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

        self.rotor_points = np.array(content, dtype="float").reshape((2, 181, 181, 3))


class From_param_2D:
    def __init__(self, file, no_points=100):

        """
        Creates a new rotor from blade parameters. The file path specified should be to
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
        self.section_coordinates = np.array([
            np.hstack((blade.section_coordinates.T, z_coords))
        ])

        self.rotor_edges = None
    
class From_param_3D:
    def __init__(self, file, UV = None):
        blade = pb.Blade3D(file)
        blade.make_blade()
        plot = pb.BladePlot(blade)
        plot.make_plots()


if __name__ == "__main__":
    o = From_param_3D('./example_files/moded_aachen.cfg')
