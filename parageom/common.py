import matplotlib.pyplot as plt
import numpy as np
import os
import errno
from warnings import warn




def make_output_folder(path, overwrite=True, warning=True):
    DIR = os.getcwd() + "/"

    if path.endswith("/"):
        path = path[:-1]

    try:
        os.mkdir(f"{path}/")
    except OSError as exc:
        if exc.errno == errno.EEXIST and overwrite:
            if warning:
                warn(
                    "Writing results to existing directory but `overwrite` is True, code will proceed."
                )
        elif exc.errno == errno.EEXIST and not overwrite:
            raise Exception(
                "`overwrite` is set to False and folder already exists."
            )
        else:
            raise


def _getlines(file, separator=" "):
    with open(file, "r") as f:
        data = [
            line.rstrip("\n").split(separator)
            if separator is not None
            else line.rstrip("\n")
            for line in f.readlines()
        ]
    for i in range(len(data)):
        data[i] = list(filter(None, data[i]))
    return data


def point_cloud_plot(points, centre=None, ax=None, c="grey"):
    """Plots a point cloud, the point list must be with shape (N_points, 3)
    for 3D plot"""

    auto_show = True if ax is None else False
    ax = plt.axes(projection="3d") if ax is None else ax
    ax.plot3D(points.T[0], points.T[2], points.T[1], c)

    centre = points[0] if centre is None else centre
    ax.set_xlim(centre[0] - 1, centre[0] + 1)
    ax.set_zlim(centre[1] - 1, centre[1] + 1)
    ax.set_ylim(centre[2] - 1, centre[2] + 1)
    ax.set_box_aspect(
        [ub - lb for lb, ub in (getattr(ax, f"get_{a}lim")() for a in "xyz")]
    )

    if auto_show:
        plt.show()


def plot_vector(origin, vector, plot_object=None, c=None):
    """Plots a vector from a point given."""
    to_plot = np.vstack((origin, origin + vector))
    if c is None:
        c = ["red", "orange"]
    if plot_object is not None:
        plot_object.scatter(*origin[[0, 2, 1]], c=c[0])
        plot_object.plot3D(*to_plot.T[[0, 2, 1]], c[1])
    else:
        raise NotImplementedError("Not implemented")


def make_plot_matplotlib_2D(x, y):

    """Create 2D Matplotlib line plot"""

    # Get blade coordinates

    # Plot the prescribed and the fitted blades
    fig_2D = plt.figure(figsize=(8, 6))
    ax_2D = fig_2D.add_subplot(111)
    ax_2D.set_xlabel("$x$ axis", fontsize=12, color="k", labelpad=12)
    ax_2D.set_ylabel("$y$ axis", fontsize=12, color="k", labelpad=12)
    # ax_2D.xaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    # ax_2D.yaxis.set_major_formatter(mpl.ticker.FormatStrFormatter('%.2f'))
    for t in ax_2D.xaxis.get_major_ticks():
        t.label.set_fontsize(12)
    for t in ax_2D.yaxis.get_major_ticks():
        t.label.set_fontsize(12)

    # Plot prescribed coordinates
    (points_2D,) = ax_2D.plot(x, y)
    points_2D.set_marker(" ")
    points_2D.set_markersize(3.5)
    points_2D.set_markeredgewidth(0.5)
    points_2D.set_markeredgecolor("k")
    points_2D.set_markerfacecolor("w")
    points_2D.set_linestyle("-")
    points_2D.set_color("k")
    points_2D.set_linewidth(1.50)

    # Set the aspect ratio of the data
    ax_2D.set_aspect(1.0)

    # Set axes aspect ratio
    x_min, x_max = ax_2D.get_xlim()
    y_min, y_max = ax_2D.get_ylim()
    x_mid = (x_min + x_max) / 2
    y_mid = (y_min + y_max) / 2
    L = np.max((x_max - x_min, y_max - y_min)) / 2
    ax_2D.set_xlim([x_mid - 1.25 * L, x_mid + 1.25 * L])
    ax_2D.set_ylim([y_mid - 1.25 * L, y_mid + 1.25 * L])

    # Adjust pad
    plt.tight_layout(pad=5.0, w_pad=None, h_pad=None)


def print_parageom():
    print("\n\n\n")
    print("    PARAGEOM    ")
    print("    PARABLADE    ")
    print("\n\n\n")
