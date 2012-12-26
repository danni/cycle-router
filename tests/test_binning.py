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
    ax.set_title("Speed Anomaly")
    cs = ax.contourf(grid.x, grid.y, grid, cmap=plt.get_cmap('RdBu_r'))
    cs.set_clim(-1, 1)
    ax.contour(grid.x, grid.y, grid)
    fig.colorbar(cs)

    plt.show()
