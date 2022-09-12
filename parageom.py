import numpy as np
import matplotlib.pyplot as plt
# from common import _getlines


class RotorGeom:
    def __init__(self, file, init="unsectioned"):

        self.file_path = file
        self.data = None
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

        """This functions reads a sectioned geomTurbo file and returns a numpy array."""

        file = self.file_path if file_path == None else file_path

        with open(file, "r") as f:
            data = [
                " ".join(line.rstrip("\n").replace("\t", " ").split())
                for line in f.readlines()
            ]

        geom = [data[i].split(' ') for i in range(896)]
        igg = data[897:]

        self.rotor_edges = np.array([geom[99:280], geom[283:464]], dtype='float32')
        self.stator_edges = np.array([geom[535:704], geom[707:876]], dtype='float32')
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
        print(np.array(surfaces).shape)

    def read_sectioned_turbo(self, file_path=None):

        """
        
        This functions reads a sectioned geomTurbo file and returns a numpy array.
        
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

        self.data = np.array(content, dtype="float")

        return self.data

    def parablade_2D_export(self, file):
        """Writes the pre-generated data to a txt file that can be read by parablade
        for parameterization."""
        # TODO exporter une des sections
        if self.data == None:
            if self.file_path == None:
                print(
                    "Please first specify a filepath for the points cloud to be imported."
                )
            else:
                self.read_turbo()

        points = self.data.reshape((2, 181, 181, 3))
        points = points.transpose((1, 0, 2, 3))
        points = points.reshape(181, 362, 3)[0]
        for i in range(3):
            points.T[i] = (points.T[i] - np.min(points.T[i])) * 0.002
        with open(file, "w") as f:
            f.writelines(
                [
                    f"{i}\t{points.T[2, i]}\t{points.T[0, i]}\n"
                    for i in range(len(points.T[0]))
                ]
            )
        print(f"Done exporting to {file}")

    def plot_3D(self):

        ax = plt.axes(projection="3d")
        ax.plot3D(self.data.T[0], self.data.T[2], self.data.T[1], "gray")

        ax.set_xlim(-100, 30)
        ax.set_zlim(0, 180)
        ax.set_ylim(-250, 200)
        ax.set_box_aspect(
            [ub - lb for lb, ub in (getattr(ax, f"get_{a}lim")() for a in "xyz")]
        )
        plt.show()


if __name__ == "__main__":
    o = RotorGeom('igg.geomTurbo')
    print(o.rotor_edges)