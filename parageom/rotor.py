import numpy as np
import matplotlib.pyplot as plt

from parageom.reader import From_geomTurbo, From_param_2D, From_param_3D


class Rotor:
    """
    The Rotor class stores all the different point clouds and curves associated with the
    give rotor.
    """

    def __init__(self, Initializer_object):

        """Takes in a rotor_points list (outputted by both read functions), as well
        as the rotor_edges list (outputted by the unsectioned read function)

        The attributes have the following shapes:

            - self.sections_coordinates:
                of shape (N_sections, N_points, N_dim)

            - self.pressure_sections: of shape (N_sections, N_points_pressure, N_dim)

                with N_points the number of points per section and N_dim = 3
                N_points may be different on the pressure and suction sides if
                the geometry is read from an .geomTurbo file.


            # TODO check that it corresponds in fact to the number of sections

            - self.leading_edge: of shape (N_sections, N_dim)

            - self.no_sections: scalar

        """

        self.pressure_sections = Initializer_object.rotor_points[0]
        self.suction_sections = Initializer_object.rotor_points[1]

        # TODO read the LE and TE from the point coordinates
        if Initializer_object.rotor_edges is not None:
            self.leading_edge = Initializer_object.rotor_edges[0]
            self.trailing_edge = Initializer_object.rotor_edges[1]
        else:
            self.leading_edge = None
            self.trailing_edge = None

        self.N_sections = self.suction_sections.shape[0]

        try:
            self.section_coordinates = Initializer_object.section_coordinates
        except:
            # TODO find way to vectorize this...
            self.section_coordinates = np.array(
                [
                    np.vstack((self.suction_sections[i], self.pressure_sections[i]))
                    for i in range(self.N_sections)
                ]
            )
        
        self.scale_factor = Initializer_object.scale_factor

    def parablade_section_export(
        self, section_idx, file=None, dim="2D", is_new=True
    ):

        """
        Writes the point cloud of a section to a txt file
        """

        section = self.section_coordinates[section_idx]*self.scale_factor

        if file is None:
            file = "./confidential/blade.txt" if dim == "2D" else "./confidential/3Dblade.txt"

        mode = "w" if is_new else "a"
        with open(file, mode) as f:
            if dim == "2D":
                f.writelines(
                    [
                        f"{i}\t{section.T[2, i]}\t{section.T[0, i]}\n"
                        for i in range(len(section.T[0]))
                    ]
                )
            elif dim == "3D":
                f.writelines(
                    [
                        f"{i}\t{section.T[2, i]}\t{section.T[0, i]}\t{section.T[1, i]}\n"
                        for i in range(len(section.T[0]))
                    ]
                )

        print(f"Done exporting to {file}")
    
    def parablade_blade_export(
        self, file = None, iterator = None
    ):

        """
        Writes the point cloud of the 3D blade to a txt file
        """

        iterator = np.array(np.linspace(0, 180, 10), dtype = 'int') if iterator is None else iterator
        
        self.parablade_section_export(iterator[0], file = file, dim = "3D")

        for i in iterator[1:]:
            self.parablade_section_export(i, file = file, dim = "3D", is_new=False)



    def plot_section(self, section_idx):

        section = self.section_coordinates[section_idx]

        ax = plt.axes(projection="3d")
        ax.plot3D(section.T[2], section.T[1], section.T[0], "gray")

        ax.set_xlim(-100, 30)
        ax.set_zlim(0, 180)
        ax.set_ylim(-250, 200)
        ax.set_box_aspect(
            [ub - lb for lb, ub in (getattr(ax, f"get_{a}lim")() for a in "xyz")]
        )

        plt.show()


if __name__ == "__main__":
    o = Rotor(From_geomTurbo("./confidential/DGEN_geom/rotor_sections.geomTurbo", init="sectioned"))
    o.parablade_blade_export(
        file = '/home/daep/j.fesquet/git_repos/parablade/testing/for_pando/dual_section.txt',
        iterator=[0, -1]
    )
    # for i in np.array(np.linspace(0, 180, 10), dtype = 'int'):
        # o.parablade_section_export(i, dim = "3D", normalize=False)
    # o.parablade_section_export(0, file = 'dgen_base.txt', dim = '2D', normalize=False)
