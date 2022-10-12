from parageom.rotor import Rotor
from parageom.reader import From_geomTurbo


def make_section(INFile, OUTFile = './tmp.txt', section = 0):
    
    """
    Write a parablade point cloud file to `OUTFile` from the blade section `section` of a sectioned .geomTurbo file.

    Parameters
    ----------
    INFile : string
        Path to the .geomTurbo file that contains the geometry from which to make the parablade sections.
        The .geomTurbo must be a sectioned one ie. created in Autogrid directly by outputting the geometry of the rotor.

    OUTFile : string, optional
        Path to the file to be outputted. Parablade reads .txt files
        Default: './tmp.txt'
    section : int, optional
        The index of the section to be outputted to parablade format. The section indeces are directly defined in the
        .geomTurbo file. Refer to that to know which section you want to output.
        Default: 0

    Returns
    -------
    None
    """

    rotor = Rotor(From_geomTurbo(INFile, init="sectioned"))
    rotor.parablade_section_export(section, file = OUTFile, normalize = True, dim='3D')
