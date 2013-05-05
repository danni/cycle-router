import os
from glob import glob

import pytest

import numpy as np
import scipy as sp
import scipy.stats
from matplotlib import pyplot as plt

from cyclerouter.processing.track import RKJSON, BadInputException
from cyclerouter.processing.binning import Grid, MELBOURNE, Direction


NO_PLOTS = not (os.environ.get('PLOTS', 'no') == 'yes')


@pytest.mark.skipif('NO_PLOTS')
def test_bin_direction():
    filename = glob('json/*.json')[4]

    with open(filename) as f:
        track = RKJSON(f)
        vels = track.calculate_vels()
        grid = Grid([track])

        fig, ax = plt.subplots(1)
        ax.set_title("Direction Sorting (red inbound, blue outbound)")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect('equal')
        ax.annotate("Brunswick", (144.960, -37.767))
        ax.annotate("MELBOURNE", (MELBOURNE.lon, MELBOURNE.lat))
        ax.scatter(MELBOURNE.lon, MELBOURNE.lat)

        for v in vels:
            d = grid.bin_direction(v)
            if d == Direction.INBOUND:
                color='r'
            else:
                color='b'

            ax.barbs(v.lon, v.lat, v.u, v.v, color=color)


        plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_binning_one():
    filename = glob('tracks/*.json')[0]

    with open(filename) as f:
        track = RKJSON(f)
        grid = Grid([track])

        assert grid.x.shape == (100,)
        assert grid.y.shape == (100,)
        assert grid.shape == (100, 100)

        fig, ax = plt.subplots(1)

        cs = ax.pcolor(grid.x, grid.y, grid,
                       cmap=plt.get_cmap('RdBu_r'))
        cs.set_clim(-1, 1)

        fig.colorbar(cs)

        plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_binning_all():

    def generate_tracks():
        for fn in glob('tracks/*.json'):
            with open(fn) as f:
                try:
                    yield RKJSON(f)
                except BadInputException:
                    pass

    grid = Grid(list(generate_tracks()))

    assert grid.x.shape == (100,)
    assert grid.y.shape == (100,)
    assert grid.shape == (2, 100, 100)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)

    ax1.set_title("Speed Anomaly (In)")
    ax2.set_title("n datapoints (In)")
    ax3.set_title("Speed Anomaly (Out)")
    ax4.set_title("n datapoints (Out)")

    cs = ax1.pcolor(grid.x, grid.y, grid[Direction.INBOUND],
                    cmap=plt.get_cmap('RdBu_r'))
    cs.set_clim(-1, 1)
    cs = ax3.pcolor(grid.x, grid.y, grid[Direction.OUTBOUND],
                    cmap=plt.get_cmap('RdBu_r'))
    cs.set_clim(-1, 1)

    cs = ax2.pcolor(grid.x, grid.y, grid._nelems[Direction.INBOUND],
                    cmap=plt.get_cmap('binary'))
    cs = ax4.pcolor(grid.x, grid.y, grid._nelems[Direction.OUTBOUND],
                    cmap=plt.get_cmap('binary'))

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect('equal')

        ax.annotate("Docklands", (144.948, -37.815))
        ax.annotate("Brunswick", (144.960, -37.767))
        ax.annotate("Richmond", (144.999, -37.819))
        ax.annotate("Fitzroy", (144.978, -37.800))
        ax.annotate("Moonee Ponds", (144.92, -37.765))
        ax.annotate("Altona", (144.83, -37.868))

    plt.show()


@pytest.mark.skipif('NO_PLOTS')
def test_binning_inverted_relationship():

    def generate_tracks():
        for fn in glob('tracks/*.json'):
            with open(fn) as f:
                try:
                    yield RKJSON(f)
                except BadInputException:
                    pass

    grid = Grid(list(generate_tracks()))

    assert grid.x.shape == (100,)
    assert grid.y.shape == (100,)
    assert grid.shape == (2, 100, 100)

    fig, ax = plt.subplots(1, 1)

    ax.set_title("Speed Anomalies")
    ax.set_xlabel("Inbound")
    ax.set_ylabel("Outbound")
    ax.set_aspect('equal')

    x = grid[Direction.INBOUND].flatten()
    y = grid[Direction.OUTBOUND].flatten()

    # filter out values close to zero
    i = np.abs(x) > 0.01
    x = x[i]; y = y[i]
    i = np.abs(y) > 0.01
    x = x[i]; y = y[i]

    print x.shape
    print y.shape
    assert x.shape[0] == y.shape[0]

    m, c, r, p, se = sp.stats.linregress(x, y)

    ax.scatter(x, y)

    x1 = np.array([-1, 1])
    ax.plot(x1, m * x1 + c, 'r')
    ax.text(1.4, 0.9, """m = {}
c = {}
r = {}
r^2 = {}
p = {}
se = {}""".format(m, c, r, r**2, p, se),
        horizontalalignment='right',
        verticalalignment='top')

    plt.show()
