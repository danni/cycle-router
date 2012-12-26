from glob import glob

from matplotlib import pyplot as plt

from track import RKJSON, BadInputException
from binning import Grid

def test_binning_one():
    filename = glob('tracks/*.json')[0]

    with open(filename) as f:
        track = RKJSON(f)
        grid = Grid([track])

        assert grid.x.shape == (50,)
        assert grid.y.shape == (50,)
        assert grid.shape == (50, 50)

        fig, ax = plt.subplots(1)

        cs = ax.pcolor(grid.x, grid.y, grid,
                       cmap=plt.get_cmap('RdBu_r'))
        cs.set_clim(-1, 1)

        fig.colorbar(cs)

        plt.show()

def test_binning_all():

    def generate_tracks():
        for fn in glob('tracks/*.json'):
            with open(fn) as f:
                try:
                    yield RKJSON(f)
                except BadInputException:
                    pass

    grid = Grid(list(generate_tracks()))

    assert grid.x.shape == (50,)
    assert grid.y.shape == (50,)
    assert grid.shape == (50, 50)

    fig, ax = plt.subplots(1)
    ax.set_title("Speed Anomaly (No Directional Binning)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    cs = ax.contourf(grid.x, grid.y, grid, cmap=plt.get_cmap('RdBu_r'))
    cs.set_clim(-1, 1)
    ax.contour(grid.x, grid.y, grid)
    fig.colorbar(cs)

    # x,y coordinates are lon,lat
    plt.annotate("Docklands", (144.948, -37.815))
    plt.annotate("Brunswick", (144.960, -37.767))
    plt.annotate("Brunswick East", (144.979, -37.769))
    plt.annotate("Richmond", (144.999, -37.819))
    plt.annotate("Fitzroy", (144.978, -37.800))

    plt.show()
