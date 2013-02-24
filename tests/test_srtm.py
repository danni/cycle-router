import pytest
from matplotlib import pyplot as plt
from numpy.testing import assert_almost_equal

from srtm import SRTM

@pytest.fixture
def grid():
    return SRTM()

def test_load_srtm(grid):
    # assert grid makes sense shapewise
    assert grid.ndim == 2
    assert grid.lats.ndim == grid.lons.ndim == 1
    assert grid.shape == (grid.lats.shape[0], grid.lons.shape[0])

    # 3 arcsecond grid
    assert_almost_equal(grid.binsize, 3./3600)

    # origin is top-left
    assert grid.lats[0] > grid.lats[1]
    assert_almost_equal(grid.lats[0] - grid.lats[1], grid.binsize)

    assert grid.lons[0] < grid.lons[1]
    assert_almost_equal(grid.lons[1] - grid.lons[0], grid.binsize)

    # Check our grid contains places interesting to us:
    # Melbourne
    assert grid.lats[0] >= -37.81361 >= grid.lats[-1] and \
           grid.lons[0] <= 144.96306 <= grid.lons[-1]
    # Altona
    assert grid.lats[0] >= -37.868 >= grid.lats[-1] and \
           grid.lons[0] <= 144.83 <= grid.lons[-1]
    # Brunswick
    assert grid.lats[0] >= -37.767 >= grid.lats[-1] and \
           grid.lons[0] <= 144.960 <= grid.lons[-1]

def test_plot_srtm(grid):

    fig, (ax1, ax2) = plt.subplots(2, 1)

    ax1.set_title("Meridional Elevation (Lon = {})".format(grid.lons[0]))
    ax1.set_xlabel("Latitude")
    ax1.plot(grid.lats, grid[:, 0])

    ax2.set_title("Zonal Elevation (Lat = {})".format(grid.lats[0]))
    ax2.set_xlabel("Longitude")
    ax2.plot(grid.lons, grid[0, :])

    plt.show()
