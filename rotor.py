import numpy as np
import matplotlib.pyplot as plt

from reader import From_geomTurbo, From_param_2D, From_param_3D



class Rotor:
    """
    The Rotor class stores all the different point clouds and curves associated with the
    give rotor.
    """
    def __init__(self, Initializer_object):
        
        """ Takes in a rotor_points list (outputted by both read functions), as well
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

        self.no_sections = self.suction_sections.shape[0]

        try:
            self.section_coordinates = Initializer_object.section_coordinates
        except:
            # TODO find way to vectorize this...
            self.section_coordinates = np.array(
                [
                    np.vstack((
                        self.suction_sections[i],
                        self.pressure_sections[i]
                    )) for i in range(self.no_sections)
                    
                ]
            )

    def parablade_section_export(self, section_idx, file = './confidential/blade.txt'):

        """
        Writes the point cloud of a section to a txt file
        """

        section = np.vstack((
            self.suction_sections[section_idx],
            self.pressure_sections[section_idx]
        ))

        # WARNING normalization is in the wrong order here:
        # scaling is done after centering which might be problematic.
        k = 1/np.max(section)

        for i in range(3):
            section.T[i] = (section.T[i] - np.min(section.T[i]))*k

        with open(file, 'w') as f:
            f.writelines(
                [
                    f'{i}\t{section.T[2, i]}\t{section.T[0, i]}\n'
                    for i in range(len(section.T[0]))
                ]
            )

        print(f'Done exporting to {file}')
        

    def plot_section(self, section_idx):

        section = self.section_coordinates[section_idx]

        ax = plt.axes(projection="3d")
        ax.plot3D(section.T[0], section.T[2], section.T[1], "gray")

        ax.set_xlim(-100, 30)
        ax.set_zlim(0, 180)
        ax.set_ylim(-250, 200)
        ax.set_box_aspect(
            [ub - lb for lb, ub in (getattr(ax, f"get_{a}lim")() for a in "xyz")]
        )

        plt.show()


if __name__ == "__main__":
    o = Rotor(From_param_2D('/home/daep/j.fesquet/git_repos/parablade/my_tests/blade.cfg'))
    o.plot_section(0)