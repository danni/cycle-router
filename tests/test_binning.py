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

    fig, (ax1, ax2) = plt.subplots(1, 2)

    ax1.set_title("Speed Anomaly (No Directional Binning)")
    ax2.set_title("n datapoints")

    cs = ax1.pcolor(grid.x, grid.y, grid, cmap=plt.get_cmap('RdBu_r'))
    cs.set_clim(-1, 1)
    # fig.colorbar(cs)

    cs = ax2.pcolor(grid.x, grid.y, grid._nelems, cmap=plt.get_cmap('binary'))

    for ax in [ax1, ax2]:
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_aspect('equal')

        ax.annotate("Docklands", (144.948, -37.815))
        ax.annotate("Brunswick", (144.960, -37.767))
        ax.annotate("Richmond", (144.999, -37.819))
        ax.annotate("Fitzroy", (144.978, -37.800))
        ax.annotate("Moonee Ponds", (144.92, -37.765))
        # ax.annotate("Melbourne", (144.96306, -37.81361))
        ax.annotate("Altona", (144.83, -37.868))

    plt.show()
